# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Added `build_info` attribute to push items.
- Added `module_build` attribute to RPM push items.
- Added `rpm_filter_arch` parameter to errata source, to select a subset of RPMs
  by architecture.
- Added `ModuleMdSourcePushItem` class. Source modulemd documents are now represented
  by this class rather than `ModuleMdPushItem`.
- Added minimal `ContainerImagePushItem` and `OperatorManifestPushItem` classes for
  container images. These classes currently are of limited use as they do not yet
  carry relevant metadata.

### Changed

- `errata` source now produces `ModuleMdSourcePushItem` where applicable, and respects
  FTP paths from Errata Tool for these items.

## [2.7.0] - 2021-06-10

### Fixed

- Fix usage of `errata` source when the an Errata Tool URL includes a path
  component.
- When Errata Tool requests push of a module which cannot be found in koji, this
  is now raised as an error rather than ignored.

### Added

- Added `module_filter_filename` parameter to koji source, to select only a subset
  of modulemd files from a build (e.g. limit to certain arches).

### Changed

- On `ErratumPushItem`, the `type` attribute will now be automatically converted
  from legacy values found in the wild such as "RHBA", "RHSA". Values are
  now also validated.
- `ModuleMdPushItem.name` now uses the NSVCA of a module rather than the filename of
  a loaded modulemd file, when this metadata is available.
- `errata` source now includes FTP paths in the `dest` field of generated push items,
  where applicable.

## [2.6.0] - 2021-05-27

### Added

- Added `Source.reset` to restore default state of library, intended
  for testing.

### Fixed

- Fix keyword arguments leaking between subsequent calls to a source prepared using
  `Source.get_partial`.

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

[Unreleased]: https://github.com/release-engineering/pushsource/compare/v2.7.0...HEAD
[2.7.0]: https://github.com/release-engineering/pushsource/compare/v2.6.0...v2.7.0
[2.6.0]: https://github.com/release-engineering/pushsource/compare/v2.5.0...v2.6.0
[2.5.0]: https://github.com/release-engineering/pushsource/compare/v2.4.0...v2.5.0
[2.4.0]: https://github.com/release-engineering/pushsource/compare/v2.3.0...v2.4.0
[2.3.0]: https://github.com/release-engineering/pushsource/compare/v2.2.0...v2.3.0
[2.2.0]: https://github.com/release-engineering/pushsource/compare/v2.1.0...v2.2.0
[2.1.0]: https://github.com/release-engineering/pushsource/compare/v2.0.0...v2.1.0
[2.0.0]: https://github.com/release-engineering/pushsource/compare/v1.2.0...v2.0.0
[1.2.0]: https://github.com/release-engineering/pushsource/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/release-engineering/pushsource/compare/v1.0.0...v1.1.0
