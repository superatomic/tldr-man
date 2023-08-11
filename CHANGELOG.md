# Changelog

## [1.3.1] - 2023-08-07

### Changed

- Change GitHub links from `tldr-man-client` to `tldr-man` ([`f389033`](https://github.com/superatomic/tldr-man/commit/f3890338e21c24a05be4eab7f566d1658b8e7fde))

### Fixed

- Patch click Bash completion generation ([#10](https://github.com/superatomic/tldr-man/issues/10), [#11](https://github.com/superatomic/tldr-man/pull/11), [pallets/click#2574](https://github.com/pallets/click/issues/2574))

## [1.3.0] - 2023-07-26

### Changed

- Exit with a non-zero exit code when a page does not exist ([`5c839f4`](https://github.com/superatomic/tldr-man/commit/5c839f4a8c0435a89c5517660912ac7d34a51698))
- Exit with exit code 3 when the cache directory does not exit ([`5c839f4`](https://github.com/superatomic/tldr-man/commit/5c839f4a8c0435a89c5517660912ac7d34a51698))
- Exit with exit code 130 on a Keyboard Interrupt ([`5c839f4`](https://github.com/superatomic/tldr-man/commit/5c839f4a8c0435a89c5517660912ac7d34a51698))
- Update PyPI trove classifiers ([`280ab5b`](https://github.com/superatomic/tldr-man/commit/280ab5b0d231185396aaa428dd0c335038be0c1c))

### Added

- Add manpage ([`f494fe7`](https://github.com/superatomic/tldr-man/commit/f494fe73afbdad708e37b0e269a315be98d0e1f2))

### Removed

- Drop dependency on `xdg` package ([`012fac9`](https://github.com/superatomic/tldr-man/commit/012fac9d882f4c57b07b015c5d9040ba60f4dca9))

## [1.2.0] - 2023-06-16

### Changed

- Display help page when no arguments or options are specified ([#7](https://github.com/superatomic/tldr-man/pull/7))
- Shorten label for cache update progress bar ([#9](https://github.com/superatomic/tldr-man/pull/9))
- Update metavar names for `--platform` and `--language` to be more descriptive ([#7](https://github.com/superatomic/tldr-man/pull/7))
- Change project name to `tldr-man` from `tldr-man-client` ([`7661e81`](https://github.com/superatomic/tldr-man/commit/7661e8162a68160c732d2b704e911be512b4704c))

### Added

- Add shell completion for page names and the `--language` option ([#8](https://github.com/superatomic/tldr-man/pull/8))
- Display the number of added, updated, and unchanged pages after updating the cache ([#9](https://github.com/superatomic/tldr-man/pull/9))
- Add `-M` option as an alias for the `--manpath` option ([#7](https://github.com/superatomic/tldr-man/pull/7))

### Fixed

- Remove trailing period from the end of the help and version descriptions ([#7](https://github.com/superatomic/tldr-man/pull/7))

## [1.1.1] - 2023-03-20

### Fixed

- Bump minimum `python` from 3.10.0 to 3.10.4 to fix race condition in `zipfile` ([#3](https://github.com/superatomic/tldr-man/issues/3), [#4](https://github.com/superatomic/tldr-man/pull/4))

## [1.1.0] - 2023-03-13

### Changed

- Improve cache update speed ([#2](https://github.com/superatomic/tldr-man/issues/2))
- Improve error message for the `--render` option when a directory or nonexistant file is provided ([`04bd41a`](https://github.com/superatomic/tldr-man/commit/04bd41aa17b05fbe516f0919c08819458d066f3a))

## [1.0.3] - 2022-08-06

### Fixed

- Fix incorrect styling for pages which contain asterisk characters ([`c9a440b`](https://github.com/superatomic/tldr-man/commit/c9a440b56585911095824c1775f8830af8552452))

## [1.0.2] - 2022-07-29

### Added

- Document Homebrew installation option ([`d0b9959`](https://github.com/superatomic/tldr-man/commit/d0b9959211e247b9fe41f1b64a0c4022fbacd1ae))

## [1.0.1] - 2022-07-28

### Fixed

- Fix package name ([`b9271a2`](https://github.com/superatomic/tldr-man/commit/b9271a20339ef38402ae490670a9d0f0983d7d3e))

## [1.0.0] - 2022-07-28

_First release._

[1.3.1]: https://github.com/superatomic/tldr-man/compare/v1.3.0...v1.3.1
[1.3.0]: https://github.com/superatomic/tldr-man/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/superatomic/tldr-man/compare/v1.1.1...v1.2.0
[1.1.1]: https://github.com/superatomic/tldr-man/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/superatomic/tldr-man/compare/v1.0.3...v1.1.0
[1.0.3]: https://github.com/superatomic/tldr-man/compare/v1.0.2...v1.0.3
[1.0.2]: https://github.com/superatomic/tldr-man/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/superatomic/tldr-man/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/superatomic/tldr-man/commits/v1.0.0
