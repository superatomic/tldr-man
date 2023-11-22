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
or visit the project repository at https://github.com/superatomic/tldr-man.
"""

__author__ = "Olivia Kinnear <contact@superatomic.dev>"

from pathlib import Path
from os import getenv
from functools import wraps
from typing import Any, ParamSpec, TypeVar, Concatenate
from collections.abc import Callable

import click
from click import Parameter, Context, command, argument, option, version_option, help_option, get_current_context, echo
from click.decorators import FC
from click_help_colors import HelpColorsCommand

from tldr_man import pages
from tldr_man.color import HELP_COLORS
from tldr_man.pages import cache_dir_lock
from tldr_man.shell_completion import page_shell_complete, language_shell_complete
from tldr_man.languages import get_locales
from tldr_man.platforms import get_page_sections, TLDR_PLATFORMS
from tldr_man.temp_path import temp_file


def subcommand(*param_decls: str, **attrs: Any) -> Callable[[Callable[..., None]], Callable[[FC], FC]]:
    """Transform a function into a `click.option()` decorator with a callback to the function."""
    def decorator(func: Callable[..., None]) -> Callable[[FC], FC]:
        @wraps(func)
        def wrapper(ctx: Context, _param: Parameter, value: Any) -> None:
            if not value or ctx.resilient_parsing:
                return

            try:
                func(value) if value is not True else func()
            except KeyboardInterrupt:
                ctx.exit(130)
            else:
                ctx.exit()

        return option(
            *param_decls,
            callback=wrapper,
            expose_value=False,
            is_flag=True if attrs.get('type') is None else attrs.get('is_flag'),
            help=func.__doc__,
            **attrs,
        )

    return decorator


P = ParamSpec('P')
T = TypeVar('T')

def require_tldr_cache(func: Callable[Concatenate[list[str], list[str], P], T]) -> Callable[P, T]:
    """
    Function decorator to mark that a subcommand requires the tldr-page cache to exist.
    Additionally, maps `ctx` into the valid locales and platforms.

    func(locales, platforms, ...) --> func(...)
    """
    @wraps(func)
    @cache_dir_lock
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        pages.verify_tldr_cache_exists()

        ctx = get_current_context()
        locales = get_locales(ctx)
        page_sections = get_page_sections(ctx)

        return func(locales, page_sections, *args, **kwargs)

    return wrapper


@subcommand('-u', '--update')
def subcommand_update() -> None:
    """Update the tldr-pages cache"""
    pages.update_cache()


@subcommand('-r', '--render', type=click.Path(exists=True, dir_okay=False, path_type=Path))
def subcommand_render(value: Path) -> None:
    """Render a page locally"""
    page_to_render = value.read_text()
    rendered_page = pages.render_manpage(page_to_render)

    with temp_file('.1', text=True) as page_path:
        page_path.write_text(rendered_page)
        pages.display_page(page_path)


@subcommand('-l', '--list')
@require_tldr_cache
def subcommand_list(locales: list[str], page_sections: list[str]) -> None:
    """List all the pages for the current platform"""
    echo('\n'.join(
        page.stem
        for section in pages.get_dir_search_order(locales, page_sections)
        for page in section.iterdir()
        if page.is_file()
    ))


@subcommand('-M', '--manpath')
@require_tldr_cache
def subcommand_manpath(locales: list[str], page_sections: list[str]) -> None:
    """Print the paths to the tldr manpages"""
    echo(':'.join(str(man_dir.parent) for man_dir in pages.get_dir_search_order(locales, page_sections)))


@command(cls=HelpColorsCommand,
         **HELP_COLORS,
         context_settings={
             'color': False if getenv('TERM') == 'dumb' or getenv('TLDR_MAN_NO_COLOR') or getenv('NO_COLOR') else None,
         },
         no_args_is_help=True)
@argument('page', nargs=-1, required=True, shell_complete=page_shell_complete)
@option('-p', '--platform',
        metavar='PLATFORM',
        type=click.Choice(TLDR_PLATFORMS),
        is_eager=True,
        help='Override the preferred platform')
@option('-L', '--language',
        metavar='LANGUAGE',
        type=str,
        is_eager=True,
        shell_complete=language_shell_complete,
        help='Specify a preferred language')
@subcommand_update
@subcommand_render
@subcommand_list
@subcommand_manpath
@version_option(None, '-v', '-V', '--version',
                message="%(prog)s %(version)s",
                help='Display the version and exit')
@help_option('-h', '--help',
             help='Show this message and exit')
@require_tldr_cache
def cli(locales: list[str], page_sections: list[str], /, page: list[str], **_: Any) -> None:
    """TLDR client that displays tldr-pages as manpages"""
    page_name = '-'.join(page).strip().lower()
    page_file = pages.find_page(page_name, locales, page_sections)
    with temp_file(page_file.name) as temp_page_file:
        temp_page_file.write_bytes(page_file.read_bytes())
        cache_dir_lock.release(force=True)
        pages.display_page(temp_page_file)


if __name__ == '__main__':
    cli()
