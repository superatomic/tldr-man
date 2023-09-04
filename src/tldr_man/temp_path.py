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

"""Wrappers around `mkstemp` and `mkdtemp` which return `pathlib.Path` objects."""

from pathlib import Path
from tempfile import mkstemp, mkdtemp


def make_temp_file(*args, **kwargs) -> Path:
    return Path(mkstemp(*args, **kwargs)[1])


def make_temp_dir(*args, **kwargs) -> Path:
    return Path(mkdtemp(*args, **kwargs))
