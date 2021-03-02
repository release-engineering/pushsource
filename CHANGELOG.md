# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.5.0] - 2021-03-02

### Added

- Added optional field `billing_codes` to the AMI staged push item schema and model.

## [2.4.0] - 2020-12-11

### Fixed

- Fix missing `reboot_suggested` field in erratum pkglist schema and model.
  The field was formerly permitted in the top-level erratum schema only, which was
  incorrect.

## [2.3.0] - 2020-11-23

### Fixed

- Fix too strict schema on staging metadata for FILES: "description" field is permitted
  to be an empty string.

## [2.2.0] - 2020-11-19

### Changed
- On `ErratumPushItem`, the `from_` attribute is now available under the preferred
  name of `from`. Since this clashes with the python keyword of the same name, the
  `from_` name will remain available indefinitely.

## [2.1.0] - 2020-11-12

### Changed

- References to unsupported `DOCKER`, `CHANNEL_DUMPS` content types in staging
  metadata files will no longer cause a validation error.
- The `id` field within erratum reference objects may now be provided as an integer
  (it will be converted to a string).
- The `name` field within erratum pkglist objects is now optional, defaulting to
  a blank string.

## [2.0.0] - 2020-11-04

### Added

- Added some user-friendly logs when advisory or staged metadata fails validation.

### Removed

- Removed support for obsolete "channel dump" push items:
   - `ChannelDumpPushItem` class was removed (backwards-incompatible API change)
   - `CHANNEL_DUMPS` directory in staging areas should no longer be used
     (will generate a warning)

## [1.2.0] - 2020-07-06

### Added

- Introduced `PushItem.with_checksums` method for calculating checksums.

## [1.1.0] - 2020-06-23

### Fixed
- Fix too strict schema on erratum references; id and title are allowed to be null.
- Fix crash on Python 2 if using `get_partial` and `register_backend` together

### Changed
- Improved log message details in some cases of error

## 1.0.0 - 2020-06-16

- Initial stable release of project

[Unreleased]: https://github.com/release-engineering/pushsource/compare/v2.5.0...HEAD
[2.5.0]: https://github.com/release-engineering/pushsource/compare/v2.4.0...v2.5.0
[2.4.0]: https://github.com/release-engineering/pushsource/compare/v2.3.0...v2.4.0
[2.3.0]: https://github.com/release-engineering/pushsource/compare/v2.2.0...v2.3.0
[2.2.0]: https://github.com/release-engineering/pushsource/compare/v2.1.0...v2.2.0
[2.1.0]: https://github.com/release-engineering/pushsource/compare/v2.0.0...v2.1.0
[2.0.0]: https://github.com/release-engineering/pushsource/compare/v1.2.0...v2.0.0
[1.2.0]: https://github.com/release-engineering/pushsource/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/release-engineering/pushsource/compare/v1.0.0...v1.1.0
