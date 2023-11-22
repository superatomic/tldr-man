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

"""Color and styling utilities for output."""

from functools import partial

from click import style


HELP_COLORS = dict(help_headers_color='yellow', help_options_color='green')


_style: partial[partial[str]] = partial(partial, style)

style_command = _style(fg='cyan', bold=True)
style_error = _style(fg='red', bold=True)
style_input = _style(fg='yellow')
style_path = _style(fg='blue')
style_task = _style(fg='cyan')
style_url = _style(underline=True)

style_create = _style(fg='green', bold=True)
style_update = _style(fg='blue', bold=True)
style_no_change = _style(bold=True)
