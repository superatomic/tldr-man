#!/usr/bin/env python3

# Copyright 2022 Ethan Kinnear
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

"""
tldr-man-client: Command-line TLDR client that displays tldr-pages as manpages.

Depends on pandoc (and man!). Install `pandoc` from https://pandoc.org/installing.html.

Run `tldr --help` for more information,
or visit the project repository at https://github.com/superatomic/tldr-man-client.
"""

from importlib import metadata
__version__ = metadata.version('tldr-man')
__author__ = "Ethan Kinnear <contact@superatomic.dev>"

import sys
from pathlib import Path
from contextlib import suppress
from os import remove
from functools import wraps
from typing import Optional

import click
from click import secho
from click_help_colors import HelpColorsCommand

from tldr_man import languages, pages
from tldr_man.util import unique, mkstemp_path, esecho


TLDR_COMMAND_NAME = 'tldr'

TLDR_PLATFORMS = 'android linux macos osx sunos windows'.split()


def click_standalone_subcommand(func):
    """Function decorator to reduce boilerplate code at the start and end of all subcommand callback functions."""
    @wraps(func)
    def wrapper(ctx, param, value):
        if not value or ctx.resilient_parsing:
            return

        exited_with_error = False
        # noinspection PyBroadException
        try:
            func(ctx, param, value)
        except Exception:
            from traceback import format_exc
            from sys import stderr

            print(format_exc(), file=stderr)
            exited_with_error = True  # Don't call the `ctx.exit()` in the `finally` block
            ctx.exit(1)
        except SystemExit as err:
            # If `sys.exit()` was called, exit that context with the given status code.
            exited_with_error = True  # Don't call the `ctx.exit()` in the `finally` block
            ctx.exit(err.code)
        finally:
            if not exited_with_error:
                ctx.exit()

    return wrapper


@click_standalone_subcommand
def subcommand_update(_ctx, _param, _value):
    pages.update_cache()


@click_standalone_subcommand
def subcommand_render(_ctx, _param, value: str):
    page_to_render = Path(value).read_text()
    rendered_page = pages.render_manpage(page_to_render)

    try:
        path = mkstemp_path('tldr-man', text=True)
        path.write_text(rendered_page)
        pages.display_page(path)
    finally:
        with suppress(NameError, FileNotFoundError):
            # noinspection PyUnboundLocalVariable
            remove(path)


@click_standalone_subcommand
def subcommand_list(ctx, _param, _value: None):
    pages.verify_tldr_cache_exists()

    locales = get_locales(ctx)
    page_sections = get_page_sections(ctx)

    print('\n'.join(unique(
        page.stem
        for section in pages.get_dir_search_order(locales, page_sections)
        for page in section.iterdir()
        if page.is_file()
    )))


@click_standalone_subcommand
def subcommand_manpath(ctx, _param, _value: None):
    pages.verify_tldr_cache_exists()

    locales = get_locales(ctx)
    page_sections = get_page_sections(ctx)

    print(':'.join(unique(str(x.parent) for x in pages.get_dir_search_order(locales, page_sections))))


@click_standalone_subcommand
def subcommand_version(_ctx, _param, _value: str):
    secho(f'{TLDR_COMMAND_NAME} {__version__}')


@click.command(cls=HelpColorsCommand, help_headers_color='yellow', help_options_color='green')
@click.argument('page', nargs=-1, required=True)
@click.option('-p', '--platform', type=click.Choice(TLDR_PLATFORMS), is_eager=True,
              help='Override the preferred platform')
@click.option('-L', '--language', is_eager=True,
              help='Specify a preferred language')
@click.option('-u', '--update', is_flag=True, callback=subcommand_update, expose_value=False, is_eager=True,
              help='Update the tldr-pages cache')
@click.option('-r', '--render', nargs=1, callback=subcommand_render, expose_value=False, is_eager=True,
              help='Render a page locally')
@click.option('-l', '--list', is_flag=True, callback=subcommand_list, expose_value=False,
              help='List all the pages for the current platform')
@click.option('--manpath', is_flag=True, callback=subcommand_manpath, expose_value=False,
              help='Print the paths to the tldr manpages')
@click.option('-v', '-V', '--version', is_flag=True, callback=subcommand_version, expose_value=False, is_eager=True,
              help='Display the version of the client')
@click.help_option('-h', '--help')
@click.pass_context
def cli(ctx, page: list[str], **_):
    """TLDR client that displays tldr-pages as manpages"""

    pages.verify_tldr_cache_exists()

    locales = get_locales(ctx)
    page_sections = get_page_sections(ctx)

    page_name = '-'.join(page).strip().lower()

    page = pages.find_page(page_name, locales, page_sections)

    if page is not None:
        pages.display_page(page)


def get_locales(ctx) -> list[str]:
    language = ctx.params.get('language')
    if language is not None:
        page_locale = languages.get_language_directory(language)
        if page_locale not in languages.all_languages():
            esecho(f"Unrecognized locale: {language}", exitcode=1)
        else:
            return [page_locale]
    else:
        return list(languages.get_languages())


def get_page_sections(ctx) -> list[str]:
    page_sections = ['common']

    current_platform = get_current_platform()
    custom_platform = ctx.params.get('platform')

    if current_platform:
        page_sections.insert(0, current_platform)

    if custom_platform:
        page_sections.insert(0, custom_platform.replace('macos', 'osx'))

    return page_sections


def get_current_platform() -> Optional[str]:
    """Get the correct tldr platform directory name from `sys.platform`."""
    match sys.platform:
        case 'darwin':
            return 'osx'
        case 'linux':
            return 'linux'
        case 'win32' | 'cygwin' | 'msys':
            return 'windows'
        case 'sunos5':
            return 'sunos'
        case _:
            return None


if __name__ == '__main__':
    cli()
