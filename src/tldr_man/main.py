#!/usr/bin/env python3

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

"""
tldr-man: Command-line TLDR client that displays tldr-pages as manpages.

Depends on pandoc (and man!). Install `pandoc` from https://pandoc.org/installing.html.

Run `tldr --help` for more information,
or visit the project repository at https://github.com/superatomic/tldr-man-client.
"""

__author__ = "Olivia Kinnear <contact@superatomic.dev>"

from pathlib import Path
from contextlib import suppress
from os import remove
from functools import wraps

import click
from click import Context, command, argument, option, version_option, help_option, pass_context
from click_help_colors import HelpColorsCommand

from tldr_man import pages
from tldr_man.shell_completion import page_shell_complete, language_shell_complete
from tldr_man.languages import get_locales
from tldr_man.platforms import get_page_sections, TLDR_PLATFORMS
from tldr_man.util import unique, mkstemp_path


def standalone_subcommand(func):
    """Function decorator to reduce boilerplate code at the start and end of all subcommand callback functions."""
    @wraps(func)
    def wrapper(ctx: Context, _param, value):
        if not value or ctx.resilient_parsing:
            return

        exited_with_error = False
        # noinspection PyBroadException
        try:
            return func(ctx, value) if value is not True else func(ctx)
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
        except KeyboardInterrupt:
            exited_with_error = True
            ctx.exit(130)
        finally:
            if not exited_with_error:
                ctx.exit()

    return wrapper

def require_tldr_cache(func):
    """
    Function decorator to mark that a subcommand requires the tldr-page cache to exist.
    Additionally, maps `ctx` into the valid locales and platforms.

    func(locales, platforms, ...) --> func(ctx, ...)
    """
    @wraps(func)
    def wrapper(ctx: Context, *args, **kwargs):
        pages.verify_tldr_cache_exists()

        locales: list[str] = get_locales(ctx)
        page_sections: list[str] = get_page_sections(ctx)

        return func(locales, page_sections, *args, **kwargs)

    return wrapper


@standalone_subcommand
def subcommand_update(_ctx):
    pages.update_cache()


@standalone_subcommand
def subcommand_render(_ctx, value: Path):
    page_to_render = value.read_text()
    rendered_page = pages.render_manpage(page_to_render)

    try:
        path = mkstemp_path('tldr-man', text=True)
        path.write_text(rendered_page)
        pages.display_page(path)
    finally:
        with suppress(NameError, FileNotFoundError):
            # noinspection PyUnboundLocalVariable
            remove(path)


@standalone_subcommand
@require_tldr_cache
def subcommand_list(locales, page_sections):
    print('\n'.join(unique(
        page.stem
        for section in pages.get_dir_search_order(locales, page_sections)
        for page in section.iterdir()
        if page.is_file()
    )))


@standalone_subcommand
@require_tldr_cache
def subcommand_manpath(locales, page_sections):
    print(':'.join(unique(str(man_dir.parent) for man_dir in pages.get_dir_search_order(locales, page_sections))))


@command(cls=HelpColorsCommand, help_headers_color='yellow', help_options_color='green', no_args_is_help=True)
@argument('page', nargs=-1, required=True, shell_complete=page_shell_complete)
@option('-p', '--platform',
        metavar='PLATFORM',
        type=click.Choice(TLDR_PLATFORMS),
        is_eager=True,
        help='Override the preferred platform')
@option('-L', '--language',
        metavar='LANGUAGE',
        is_eager=True,
        shell_complete=language_shell_complete,
        help='Specify a preferred language')
@option('-u', '--update',
        callback=subcommand_update, expose_value=False,
        is_flag=True,
        is_eager=True,
        help='Update the tldr-pages cache')
@option('-r', '--render',
        callback=subcommand_render, expose_value=False,
        type=click.Path(exists=True, dir_okay=False, path_type=Path), nargs=1,
        is_eager=True,
        help='Render a page locally')
@option('-l', '--list',
        callback=subcommand_list, expose_value=False,
        is_flag=True,
        help='List all the pages for the current platform')
@option('-M', '--manpath',
        callback=subcommand_manpath, expose_value=False,
        is_flag=True,
        help='Print the paths to the tldr manpages')
@version_option(None, '-v', '-V', '--version',
                message="%(prog)s %(version)s",
                help='Display the version and exit')
@help_option('-h', '--help',
             help='Show this message and exit')
@pass_context
@require_tldr_cache
def cli(locales, page_sections, page: list[str], **_):
    """TLDR client that displays tldr-pages as manpages"""
    page_name = '-'.join(page).strip().lower()

    page_path = pages.find_page(page_name, locales, page_sections)

    if page_path is not None:
        pages.display_page(page_path)


if __name__ == '__main__':
    cli()
