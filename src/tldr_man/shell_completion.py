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

"""Rich shell completions for the client."""

from click import Context, Parameter
from click.shell_completion import CompletionItem

from tldr_man.pages import CACHE_DIR, get_dir_search_order
from tldr_man.languages import get_locales, all_language_codes
from tldr_man.platforms import get_page_sections


def page_shell_complete(ctx: Context, param: Parameter, incomplete: str) -> list[CompletionItem]:
    if not CACHE_DIR.exists() or param.name is None: # the `param.name is None` check makes the type checker happy
        return []

    locales: list[str] = get_locales(ctx)
    page_sections: list[str] = get_page_sections(ctx)

    completed_part = ''.join(part + '-' for part in ctx.params[param.name] or [])

    return [
        CompletionItem(page.stem.removeprefix(completed_part))
        for section in get_dir_search_order(locales, page_sections)
        for page in section.iterdir()
        if page.is_file()
        if page.stem.startswith(completed_part + incomplete)
    ]


def language_shell_complete(_ctx: Context, _param: Parameter, _incomplete: str) -> list[CompletionItem]:
    if not CACHE_DIR.exists():
        return []
    return [CompletionItem(code) for code in all_language_codes()]
