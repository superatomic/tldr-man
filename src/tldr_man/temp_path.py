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

"""Context manager wrappers around `mkstemp` and `mkdtemp` which yield `pathlib.Path` objects."""

from collections.abc import Iterator
from contextlib import contextmanager, suppress
from os import remove
from pathlib import Path
from shutil import rmtree
from tempfile import mkstemp, mkdtemp
from typing import Any


@contextmanager
def temp_file(*args: Any, **kwargs: Any) -> Iterator[Path]:
    try:
        yield Path(file := mkstemp(*args, **kwargs)[1])
    finally:
        with suppress(NameError, FileNotFoundError):
            # noinspection PyUnboundLocalVariable
            remove(file)


@contextmanager
def temp_dir(*args: Any, **kwargs: Any) -> Iterator[Path]:
    try:
        yield Path(directory := mkdtemp(*args, **kwargs))
    finally:
        with suppress(NameError, FileNotFoundError):
            # noinspection PyUnboundLocalVariable
            rmtree(directory)
