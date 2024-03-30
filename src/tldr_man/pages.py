# Copyright 2023 Olivia Kinnear
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Interact with tldr-pages and the tldr-pages manpage cache."""

import re
import shlex
import zipfile
from concurrent.futures import ThreadPoolExecutor
from contextlib import suppress, contextmanager
from math import ceil
from pathlib import Path
from os import makedirs, getenv
from shutil import rmtree, move, which
from subprocess import run, PIPE, DEVNULL
from typing import Optional, TypeVar, overload
from collections.abc import Iterable, Iterator, Hashable

import requests
from click import echo, progressbar, format_filename
from filelock import FileLock
from requests.exceptions import ConnectionError, HTTPError, InvalidSchema, InvalidURL, MissingSchema, Timeout

from tldr_man.color import style_command, style_path, style_task, style_url, style_create, style_update, style_no_change
from tldr_man.errors import Fail, NoPageCache, ExternalCommandNotFound, PageNotFound
from tldr_man.temp_path import temp_file, temp_dir

CACHE_DIR_NAME = 'tldr-man'

ZIP_ARCHIVE_URL = getenv('TLDR_MAN_ARCHIVE_URL', "https://github.com/tldr-pages/tldr/releases/latest/download/tldr.zip")
ZIP_ARCHIVE_CHUNK_SIZE = 8192

MANPAGE_SECTION = '1'

MANPAGE_HEADER = f"""
% {{name}}({MANPAGE_SECTION}) {{name}}
%
% tldr-man

# NAME
{{name}} - {{desc}}

# DESCRIPTION
{{info}}

# EXAMPLES
{{examples}}

"""[1:-1]

PANDOC_MISSING_MESSAGE = f"""
Make sure that pandoc is installed and on your PATH.
  Installation instructions: {style_url('https://pandoc.org/installing.html')}
"""[1:-1]

CACHE_DOES_NOT_EXIST_MESSAGE = f"""
The tldr-pages cache needs to be generated before {style_command('tldr')} can be used.
  Run {style_command('tldr --update')} to generate the cache.
"""[1:-1]


@overload
def getenv_dir(key: str, default: None = None) -> Optional[Path]: ...

@overload
def getenv_dir(key: str, default: Path) -> Path: ...

def getenv_dir(key: str, default: Optional[Path] = None) -> Optional[Path]:
    if value := getenv(key):
        path = Path(value)
        if path.is_absolute():
            return path.resolve()
    return default


def get_cache_dir() -> Path:
    return getenv_dir('TLDR_MAN_CACHE_DIR') or getenv_dir('XDG_CACHE_HOME', Path.home() / '.cache') / CACHE_DIR_NAME


CACHE_DIR: Path = get_cache_dir()
cache_dir_lock = FileLock(CACHE_DIR.parent / f'.{CACHE_DIR.name}.lock', timeout=2)


@contextmanager
def pages_archive(url: str = ZIP_ARCHIVE_URL) -> Iterator[zipfile.Path]:
    """Downloads the current tldr-pages zip archive and yields it."""
    with temp_file('tldr.zip') as zip_file:
        try:
            with requests.get(url, stream=True, timeout=10) as r:
                r.raise_for_status()
                try:
                    length = ceil(int(r.headers['Content-Length']) / ZIP_ARCHIVE_CHUNK_SIZE)
                except (KeyError, ValueError):  # KeyError if lookup failed and ValueError if `int()` failed.
                    length = None
                with (open(zip_file, 'wb') as file,
                      progressbar(
                          r.iter_content(chunk_size=ZIP_ARCHIVE_CHUNK_SIZE),
                          label=style_task("Downloading ZIP"),
                          length=length,
                      ) as chunks):
                    for chunk in chunks:
                        file.write(chunk)
            yield zipfile.Path(zip_file)
        except (InvalidURL, InvalidSchema):
            raise Fail(f"Invalid URL '{style_url(url)}'")
        except MissingSchema:
            raise Fail(f"Invalid URL '{style_url(url)}'. Perhaps you meant {style_url('https://' + url)}?")
        except ConnectionError:
            raise Fail(f"Could not connect to {style_url(url)}")
        except Timeout:
            raise Fail(f"Request to {style_url(url)} timed out")
        except HTTPError:
            raise Fail(f"Request to {style_url(url)}: {r.status_code} {r.reason}")
        except zipfile.BadZipFile:
            raise Fail(f"Got a bad ZIP file from {style_url(ZIP_ARCHIVE_URL)}")


AnyPath = TypeVar('AnyPath', Path, zipfile.Path)


def iter_dirs(path: AnyPath) -> Iterator[AnyPath]:
    return filter(lambda p: p.is_dir(), path.iterdir())


def update_cache() -> None:
    """Updates the tldr-pages manpage cache."""

    if not pandoc_exists():
        raise ExternalCommandNotFound('pandoc', PANDOC_MISSING_MESSAGE)

    ensure_cache_dir_update_safety()

    echo('Updating tldr-pages cache...')

    created, updated, unchanged = 0, 0, 0

    with pages_archive() as zip_path, temp_dir('tldr-man') as temp_cache_dir:
        # Iterate through each language and section in the zip file.
        for language_dir in iter_dirs(zip_path):
            if language_dir.name == 'pages' and (zip_path / 'pages.en').is_dir():
                continue  # Skip the duplicate legacy English directory.
            for sections_dir in iter_dirs(language_dir):
                # Get the full path to the directory where all manpages for this language and section will be extracted.
                res_dir = temp_cache_dir / language_dir.name / sections_dir.name / ('man' + MANPAGE_SECTION)
                res_dir.mkdir(parents=True, exist_ok=True)  # Create the directories if they don't exist.

                # Get the directory where the old versions of the manpages are located,
                # to compare it with the new versions that are generated:
                original_dir = (
                    CACHE_DIR / language_dir.name / sections_dir.name / ('man' + MANPAGE_SECTION)
                    if CACHE_DIR.exists() else None
                )

                # Create the label for the progress bars that are shown.
                progressbar_label = (style_path(f"{language_directory_to_code(language_dir):5s}")
                                     + ' / '
                                     + style_path(f'{sections_dir.name:7s}'))

                # `render_manpage()` takes a significant amount of time to run.
                # Due to the number of pages that need to be rendered,
                # this function is invoked simultaneously using threads.
                def to_manpage(tldr_page: zipfile.Path) -> tuple[str, str]:
                    """Convert a tldr-page into a manpage"""
                    rendered_manpage = render_manpage(tldr_page.read_text())
                    manpage_filename = tldr_page.name.removesuffix('.md') + '.' + MANPAGE_SECTION
                    # Return the filename to save the manpage to along with the rendered manpage itself.
                    return manpage_filename, rendered_manpage

                # Get a list of all tldr-pages in the current language and section.
                # The generator needs to be collected into a list to give the progressbar a length.
                pages = list(filter(lambda p: p.is_file(), sections_dir.iterdir()))

                # Create a thread pool to render multiple manpages in parallel, and display progress with a progressbar.
                # The default number of workers is used ((os.cpu_count() or 1) + 4).
                with (ThreadPoolExecutor(thread_name_prefix='render_manpage') as pool,
                      progressbar(pool.map(to_manpage, pages), label=progressbar_label, length=len(pages)) as fut):
                    try:
                        # As each manpage finishes rendering, save their contents to the destination file.
                        # Note: This operation must be done here and not within a thread! `Path.write_text` and
                        #       `shutil.rmtree` (called as part of cleanup) are not thread-safe if they happen at the
                        #       same time. (This would occur during a keyboard interrupt)
                        for filename, manpage in fut:
                            res_file = res_dir / filename
                            res_file.write_text(manpage)

                            # Log whether the file was created, updated, or unchanged:
                            with cache_dir_lock:
                                if original_dir is None or not (original_file := original_dir / filename).exists():
                                    created += 1
                                elif original_file.read_text() != manpage:
                                    updated += 1
                                else:
                                    unchanged += 1
                    except:
                        # If an exception occurs, such as a KeyboardInterrupt or an actual Exception,
                        # shutdown the pool *without* waiting for any remaining futures to finish. This will prevent the
                        # program from having a significant delay when it exits prematurely.
                        # This is not a `finally` clause because the normal `pool.shutdown` behavior implemented by
                        # `Executor.__exit__` is correct when no error occurs.
                        pool.shutdown(wait=False, cancel_futures=True)
                        raise

        # Now that the updated cache has been generated, remove the old cache, make sure the parent directory exists,
        # and move the new cache into the correct directory from the temporary directory.

        with cache_dir_lock:
            ensure_cache_dir_update_safety()
            with suppress(FileNotFoundError):
                rmtree(CACHE_DIR)

            makedirs(CACHE_DIR.parent, exist_ok=True)
            move(temp_cache_dir, CACHE_DIR)

    # Display the details for the cache update:
    echo(', '.join([
        style_create(f'{created} Added'),
        style_update(f'{updated} Updated'),
        style_no_change(f'{unchanged} Unchanged'),
    ]))


# Matches names in the formats of `pages`, `pages.xx`, and `pages.xx_YY`:
EXPECTED_CACHE_CONTENT_PATTERN = re.compile(r'^pages(?:\.\w{2}(?:_\w{2})?)?$')


@cache_dir_lock
def ensure_cache_dir_update_safety() -> None:
    """Make sure not to overwrite directories with user data in them."""

    if not CACHE_DIR.exists():
        return

    problematic_files = ['  ' + format_filename(path) + ('/' if path.is_dir() else '')
                         for path in sorted(CACHE_DIR.iterdir(), key=lambda path: (path.is_file(), path.name))
                         if not (path.is_dir() and EXPECTED_CACHE_CONTENT_PATTERN.match(path.name))]

    if problematic_files:
        raise Fail('\n'.join([
            f"Cache directory at {style_path(format_filename(CACHE_DIR))} contains non-cache files.",
            "Updating could cause data loss and is a potentially destructive action.",
            "",
            "The following files would be removed:",
            *problematic_files,
            "",
            "To force an update, run the following command to delete the cache:",
            style_command(f"  rm -r {shlex.quote(str(CACHE_DIR))}"),
        ]))


PANDOC_LOCATION: Optional[str] = which('pandoc')


def render_manpage(tldr_page: str) -> str:
    """
    Render a manpage from a markdown formatted tldr-page.

    Exits with an error message if `pandoc` is not installed.
    """

    lines = tldr_page.splitlines()

    name = lines.pop(0).lstrip('# ')  # Get the name of the command.

    # Get the information of the command.
    info: list[str] = []
    while lines and ((valid_line := (line := lines.pop(0)).startswith('> ')) or not info):
        if not valid_line:
            continue
        info.append(line.removeprefix('> '))

    examples_list = []
    for line in lines:
        if not line:
            continue

        indicator, contents = line[0], line[1:].strip().replace(r'\\', r'\e').replace('*', r'\*')
        match indicator:
            case '-':
                examples_list.append(f'\n**{contents}**\n')
            case '`':
                examples_list.append(f': {contents[:-1]}\n')
    examples = re.sub(r'\{\{(.*?)}}', r'*\1*', ''.join(examples_list))

    res = MANPAGE_HEADER.format(name=name, desc=info[0], info='\n'.join(info[1:]), examples=examples)

    try:
        if PANDOC_LOCATION is None:
            raise FileNotFoundError
        pandoc = run([PANDOC_LOCATION, '-', '-s', '-t', 'man', '-f', 'markdown-tex_math_dollars-smart'],
                     input=res, stdout=PIPE, encoding="utf-8")
        if pandoc.returncode:
            raise Fail(f"Command 'pandoc' returned non-zero exit status {pandoc.returncode}")
        return pandoc.stdout
    except FileNotFoundError:
        raise ExternalCommandNotFound('pandoc', PANDOC_MISSING_MESSAGE)


def pandoc_exists() -> bool:
    """Check whether pandoc exists."""
    if PANDOC_LOCATION is None:
        return False
    try:
        return run([PANDOC_LOCATION, '--version'], stdout=DEVNULL).returncode == 0
    except FileNotFoundError:
        return False


@cache_dir_lock
def verify_tldr_cache_exists() -> None:
    """Display a specific message if the tldr manpage cache doesn't exist yet, and then exit."""
    if not CACHE_DIR.exists():
        raise NoPageCache(CACHE_DOES_NOT_EXIST_MESSAGE)


def display_page(page: Path) -> None:
    try:
        run(['man', page])
    except FileNotFoundError as err:
        if err.filename == 'man':
            raise ExternalCommandNotFound('man', 'Make sure that man is on your PATH.')
        else:
            raise


@cache_dir_lock
def find_page(page_name: str, /, locales: Iterable[str], page_sections: Iterable[str]) -> Path:
    for search_dir in get_dir_search_order(locales, page_sections):
        page = search_dir / (page_name + '.' + MANPAGE_SECTION)

        if page.exists():
            return page
    else:
        raise PageNotFound(page_name)


T = TypeVar('T', bound=Hashable)

def unique(items: Iterable[T]) -> Iterator[T]:
    seen = set()
    for item in items:
        if item not in seen:
            seen.add(item)
            yield item


@cache_dir_lock
def get_dir_search_order(locales: Iterable[str], page_sections: Iterable[str]) -> Iterator[Path]:
    return unique(
        CACHE_DIR / locale / section / ('man' + MANPAGE_SECTION)
        for locale in locales
        for section in page_sections
    )


def language_directory_to_code(language_dir: AnyPath) -> str:
    return language_dir.name.removeprefix('pages').lstrip('.') or 'en'
