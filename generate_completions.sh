#!/usr/bin/env bash

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

# Generates very basic shell completions for `tldr` and saves them in the `completions/` directory.

mkdir -p completions/

generate_completion() {
  _TLDR_MAN_COMPLETE=${1}_source tldr-man > completions/tldr-man."${1}"
  _TLDR_COMPLETE=${1}_source tldr > completions/tldr."${1}"
}

generate_completion bash
generate_completion zsh
generate_completion fish
