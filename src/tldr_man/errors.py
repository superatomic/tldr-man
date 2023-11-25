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

"""Exceptions raised by the client."""

from urllib.parse import quote as url_escape
from typing import Optional, IO, Any

from click import echo, get_current_context
from click.exceptions import ClickException

from tldr_man.color import style_command, style_error, style_input, style_url


class ColoredClickException(ClickException):
    def __init__(self, message: str):
        super().__init__(message)
        self.ctx = get_current_context(silent=True)

    def show(self, file: Optional[IO[Any]] = None) -> None:
        if file is None:
            # noinspection PyProtectedMember
            from click._compat import get_text_stderr
            file = get_text_stderr()

        color = False if self.ctx is None else self.ctx.color
        echo(style_error("Error: ") + self.format_message(), file=file, color=color)


class Fail(ColoredClickException):
    """Represents a generic failure."""


class PageNotFound(ColoredClickException):
    _URL_BASE = "https://github.com/tldr-pages/tldr/issues/new?title=page%20request:%20"

    def format_message(self) -> str:
        return '\n'.join([
            f"Page {style_input(self.message)} is not found.",
            f"  Try running {style_command('tldr --update')} to update the tldr-pages cache.",
            "",
            "Request this page here:",
            f"  {style_url(self._URL_BASE + url_escape(self.message))}",
        ])


class NoPageCache(ColoredClickException):
    exit_code = 3


class ExternalCommandNotFound(ColoredClickException):
    exit_code = 127

    def __init__(self, command_name: str, message: str):
        super().__init__(message)
        self.command_name = command_name

    def format_message(self) -> str:
        return f"Couldn't find the {style_command(self.command_name)} command.\n" + self.message
