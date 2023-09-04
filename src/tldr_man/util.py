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

"""Various utility functions."""

from pathlib import Path
from tempfile import mkstemp, mkdtemp
from typing import TypeVar
from collections.abc import Iterable, Iterator, Hashable


T = TypeVar('T', bound=Hashable)

def unique(items: Iterable[T]) -> Iterator[T]:
    seen = set()
    for item in items:
        if item not in seen:
            seen.add(item)
            yield item


def mkstemp_path(*args, **kwargs) -> Path:
    return Path(mkstemp(*args, **kwargs)[1])


def mkdtemp_path(*args, **kwargs) -> Path:
    return Path(mkdtemp(*args, **kwargs))
