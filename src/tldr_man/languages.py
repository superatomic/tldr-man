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

"""Handle tldr-page languages."""

from os import getenv
from collections.abc import Iterator

from tldr_man.pages import TLDR_CACHE_HOME, language_directory_to_code


def all_languages() -> Iterator[str]:
    return map(get_language_directory, all_language_codes())


def all_language_codes() -> Iterator[str]:
    return (
        language_directory_to_code(pages_dir)
        for pages_dir in TLDR_CACHE_HOME.iterdir()
        if pages_dir.is_dir()
    )


def get_environment_languages() -> Iterator[str]:
    """
    Returns a list of the user's preferred languages, inferred by the environment variables LANG and LANGUAGE.

    See https://github.com/tldr-pages/tldr/blob/main/CLIENT-SPECIFICATION.md#language for details.
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
        if (TLDR_CACHE_HOME / full_locale).is_dir():
            return full_locale
        else:
            return f'pages.{language}'
