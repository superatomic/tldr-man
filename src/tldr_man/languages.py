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

"""Handle languages for the client."""

from os import getenv
from collections.abc import Iterator

from click import Context

from tldr_man.pages import CACHE_DIR, language_directory_to_code
from tldr_man.util import exit_with


def all_languages() -> Iterator[str]:
    """Returns an iterator of all languages directory names."""
    return map(get_language_directory, all_language_codes())


def all_language_codes() -> Iterator[str]:
    """Returns an iterator of all language codes, based on all language directories."""
    return (
        language_directory_to_code(pages_dir)
        for pages_dir in CACHE_DIR.iterdir()
        if pages_dir.is_dir()
    )


def get_environment_languages() -> Iterator[str]:
    """
    Returns an iterator of the user's preferred languages,
    inferred from the environment variables `LANG`, `LANGUAGE`, and `TLDR_LANGUAGE`.

    See https://github.com/tldr-pages/tldr/blob/main/CLIENT-SPECIFICATION.md#language for more details.
    """

    languages: list[str] = []

    env_lang = getenv('LANG')
    env_language = getenv('LANGUAGE')
    env_tldr_language = getenv('TLDR_LANGUAGE')

    if env_language:
        languages += env_language.split(':')

    if env_tldr_language:
        languages += env_tldr_language.split(':')

    if env_lang and env_lang.upper() not in ['C', 'POSIX']:
        languages.insert(0, env_lang)

    languages.append('en')

    # Remove country code from the language codes
    return map(get_language_directory, languages)


def _language_code_as_parts(language_code: str) -> tuple[str, str]:
    """Removes country codes from language codes and preforms data normalization."""
    language, is_region, region = language_code.split('.')[0].partition('_')

    language = language.strip().lower()
    region = region.strip().upper() if is_region else language.upper()

    return language, region


def get_language_directory(language_code: str) -> str:
    """Get the name of the directory for a language code."""
    language, region = _language_code_as_parts(language_code)
    if language == 'en':
        return 'pages'
    else:
        full_locale = f'pages.{language}_{region}'
        if (CACHE_DIR / full_locale).is_dir():
            return full_locale
        else:
            return f'pages.{language}'


def get_locales(ctx: Context) -> list[str]:
    """Return an ordered list of the languages that the user specifies."""
    language = ctx.params.get('language')
    if language is not None:
        page_locale = get_language_directory(language)
        if page_locale not in all_languages():
            exit_with(f"Unrecognized locale: {language}")
        else:
            return [page_locale]
    else:
        return list(get_environment_languages())
