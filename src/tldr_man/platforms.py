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

"""Handle platforms for the client."""

from sys import platform
from typing import Optional

from click import Context


TLDR_PLATFORMS = 'android freebsd linux macos netbsd openbsd osx sunos windows'.split()


def get_page_sections(ctx: Context) -> list[str]:
    """Return an ordered list of the platform sections that the user specifies."""
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
    for platform_prefix in ['freebsd', 'linux', 'netbsd', 'openbsd', 'sunos']:
        if platform.startswith(platform_prefix):
            return platform_prefix
    if platform == 'darwin':
        return 'osx'
    if platform in ['win32', 'cygwin', 'msys']:
        return 'windows'
    return None
