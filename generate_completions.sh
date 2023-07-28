#!/usr/bin/env sh

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

# Generates bash, zsh, and fish shell completions for `tldr`.
#
# IMPORTANT: `tldr` and `tldr-man` must both be present on $PATH for this script to work.
#
# Usage:
#   ./generate_completions.sh [OUTPUT_DIR]
#
# If OUTPUT_DIR is specified, files are generated in the directory OUTPUT_DIR.
# Otherwise, `$(dirname -- "$0")/completions` is used.

set -e

# Verify that the commands `tldr` and `tldr-man` exist:
for command_name in tldr tldr-man; do
  if ! command -v $command_name > /dev/null; then
    echo "error: command '$command_name' not found" > /dev/stderr
    exit 1
  fi
done

# Determine the output directory, and create it if it doesn't exist:
out="${1:-$(dirname -- "$0")/completions}"
mkdir -p "$out"

# Generate shell completion files:
for shell in bash zsh fish; do
  _TLDR_COMPLETE=${shell}_source tldr > "$out/tldr.${shell}"
  _TLDR_MAN_COMPLETE=${shell}_source tldr-man > "$out/tldr-man.${shell}"
done
