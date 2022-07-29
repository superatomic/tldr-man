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

"""Handle tldr-page languages."""

from os import getenv
from typing import Iterable

from tldr_man.pages import TLDR_CACHE_HOME


def all_languages():
    return (
        get_language_directory(pages_dir.name.removeprefix('pages').lstrip('.') or 'en')
        for pages_dir in TLDR_CACHE_HOME.iterdir()
        if pages_dir.is_dir()
    )


def get_languages() -> Iterable[str]:
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


def _language_code_as_parts(language_code: str) -> (str, str):
    """Removes country codes from language codes and preforms data normalization."""
    code = language_code.split('.')[0].split('_', 1)

    language = code[0].strip().lower()
    region = code[1].strip().upper() if len(code) >= 2 else language.upper()

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
