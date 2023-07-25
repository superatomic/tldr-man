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
import zipfile
from concurrent.futures import ThreadPoolExecutor
from contextlib import suppress
from pathlib import Path
from os import remove, makedirs, getenv
from shutil import rmtree, move
from subprocess import run, PIPE, DEVNULL
from typing import Optional
from collections.abc import Iterable

import requests
from click import secho, progressbar, style, echo

from tldr_man.util import mkstemp_path, mkdtemp_path, eprint, exit_with

CACHE_DIR_NAME = 'tldr-man'

ZIP_ARCHIVE_URL = "https://tldr.sh/assets/tldr.zip"

MANPAGE_SECTION = '1'

MANPAGE_HEADER = f"""
% {{name}}({MANPAGE_SECTION}) {{name}}
%
% tldr-man-client

# NAME
{{name}} - {{desc}}

# DESCRIPTION
{{info}}

# EXAMPLES
{{examples}}

"""[1:-1]

PANDOC_MISSING_MESSAGE = """
Error: Couldn't find the `pandoc` command.
Make sure that pandoc is installed and on your PATH.
    Installation instructions: https://pandoc.org/installing.html
"""[1:-1]

MANPAGE_MISSING_MESSAGE = """
Error: Couldn't find the `man` command.
Make sure that `man` is on your PATH.
"""[1:-1]

PAGE_NOT_FOUND_MESSAGE = """
Error: Page `{page_name}` is not found.
    Try running `tldr --update` to update the tldr-pages cache.

Request this page here:
    https://github.com/tldr-pages/tldr/issues/new?title=page%20request:%20{page_name}
"""[1:-1]

CACHE_DOES_NOT_EXIST_MESSAGE = """
The tldr-pages cache needs to be generated before `tldr` can be used.
    Run `tldr --update` to generate the cache.
"""[1:-1]


def getenv_dir(key: str, default: Optional[Path] = None) -> Optional[Path]:
    if value := getenv(key):
        path = Path(value)
        if path.is_absolute():
            return path.resolve()
    return default


def get_cache_dir() -> Path:
    return getenv_dir('XDG_CACHE_HOME', Path.home() / '.cache') / CACHE_DIR_NAME


CACHE_DIR: Path = get_cache_dir()


def download_archive(location: Path, url: str = ZIP_ARCHIVE_URL) -> None:
    """Downloads the current tldr-pages zip archive into a specific location."""

    try:
        r = requests.get(url, timeout=10)
    except requests.ConnectionError:
        exit_with(f"Error: Could not make connection to {url}")
    except requests.Timeout:
        exit_with(f"Error: Request to {url} timed out")
    except requests.RequestException:
        eprint(f"The following error occurred when trying to access {url}:")
        raise
    else:
        location.write_bytes(r.content)


def update_cache() -> None:
    """Updates the tldr-pages manpage cache."""

    if not pandoc_exists():
        exit_with(PANDOC_MISSING_MESSAGE, exitcode=127)

    secho('Updating tldr-pages cache...', fg='cyan')

    created, updated, unchanged = 0, 0, 0

    try:
        # Create a temporary file for the tldr-pages zip archive to generate manpages from.
        zip_archive_location = mkstemp_path('tldr.zip')
        download_archive(zip_archive_location)

        # Create the cache directory that will be copied to `~/.cache/tldr-man`.
        temp_cache_dir = mkdtemp_path('tldr-man')

        # Get the zip file
        try:
            zip_path = zipfile.Path(zip_archive_location)
        except zipfile.BadZipFile:
            eprint(f"Error: Got a bad zipfile from {ZIP_ARCHIVE_URL}")
            raise

        # Iterate through each language and section in the zip file.
        for language_dir in zip_path.iterdir():
            if not language_dir.is_dir():
                continue
            for sections_dir in language_dir.iterdir():
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
                progressbar_label = (style(f"{language_directory_to_code(language_dir):5s}", fg='blue')
                                     + ' / '
                                     + style(f'{sections_dir.name:7s}', fg='blue'))

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

        with suppress(FileNotFoundError):
            rmtree(CACHE_DIR)

        makedirs(CACHE_DIR.parent, exist_ok=True)
        move(temp_cache_dir, CACHE_DIR)

    finally:
        # Clean up any temporary files that aren't gone.
        with suppress(NameError, FileNotFoundError):
            # noinspection PyUnboundLocalVariable
            remove(zip_archive_location)
        with suppress(NameError, FileNotFoundError):
            # noinspection PyUnboundLocalVariable
            rmtree(temp_cache_dir)

    # Display the details for the cache update:
    echo(', '.join([
        style(f'{created} Added', fg='green', bold=True),
        style(f'{updated} Updated', fg='blue', bold=True),
        style(f'{unchanged} Unchanged', bold=True),
    ]))


def render_manpage(tldr_page: str) -> str:
    """
    Render a manpage from a markdown formatted tldr-page.

    Exits with an error message if `pandoc` is not installed.
    """

    lines = tldr_page.splitlines()

    name = lines.pop(0).lstrip('# ')  # Get the name of the command.

    # Get the information of the command.
    info = []
    while lines and ((valid_line := (line := lines.pop(0)).startswith('> ')) or not info):
        if not valid_line:
            continue
        info.append(line.removeprefix('> '))

    examples = []
    for line in lines:
        if not line:
            continue

        indicator, contents = line[0], line[1:].strip().replace(r'\\', r'\e').replace('*', r'\*')
        match indicator:
            case '-':
                examples.append(f'\n**{contents}**\n')
            case '`':
                examples.append(f': {contents[:-1]}\n')
    examples = re.sub(r'\{\{(.*?)}}', r'*\1*', ''.join(examples))

    res = MANPAGE_HEADER.format(name=name, desc=info[0], info='\n'.join(info[1:]), examples=examples)

    try:
        return run(['pandoc', '-', '-s', '-t', 'man', '-f', 'markdown-tex_math_dollars-smart'],
                   input=res, stdout=PIPE, encoding="utf-8").stdout
    except FileNotFoundError:
        exit_with(PANDOC_MISSING_MESSAGE, exitcode=127)


def pandoc_exists() -> bool:
    """Check whether pandoc exists."""
    try:
        return run(['pandoc', '--version'], stdout=DEVNULL).returncode == 0
    except FileNotFoundError:
        return False


def verify_tldr_cache_exists():
    """Display a specific message if the tldr manpage cache doesn't exist yet, and then exit."""
    if not CACHE_DIR.exists():
        exit_with(CACHE_DOES_NOT_EXIST_MESSAGE, exitcode=3)


def display_page(page: Path) -> None:
    try:
        run(['man', page])
    except FileNotFoundError as err:
        if err.filename == 'man':
            exit_with(MANPAGE_MISSING_MESSAGE, exitcode=127)
        else:
            raise


def find_page(page_name: str, /, locales: Iterable[str], page_sections: Iterable[str]) -> Optional[Path]:
    for search_dir in get_dir_search_order(locales, page_sections):
        page = search_dir / (page_name + '.' + MANPAGE_SECTION)

        if page.exists():
            return page
    else:
        exit_with(PAGE_NOT_FOUND_MESSAGE.format(page_name=page_name))


def get_dir_search_order(locales: Iterable[str], page_sections: Iterable[str]) -> Iterable[Path]:
    return (
        CACHE_DIR / locale / section / ('man' + MANPAGE_SECTION)
        for locale in locales
        for section in page_sections
    )


def language_directory_to_code(language_dir: Path):
    return language_dir.name.removeprefix('pages').lstrip('.') or 'en'
