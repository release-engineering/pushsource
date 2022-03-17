# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

- n/a

## [2.18.0] - 2022-03-18

### Added

- Introduced new backends to load a single file: "file", "rpm" and others.
- Introduced `pushsource-ls` command.

## [2.17.0] - 2022-03-16

### Added

- Introduced entry points mechanism to assist with registration of custom backends.

## [2.16.0] - 2022-03-10

### Fixed

- Added a workaround for a python2 strptime thread-safety bug.

### Added

- Introduced `DirectoryPushItem` class for `RAW` content.

## [2.15.0] - 2022-03-08

### Changed

- All `PushItem` classes are now slotted, for reduced memory usage.

## [2.14.0] - 2022-02-01

### Added

- Introduced `FilePushItem.display_order` attribute.

## [2.13.4] - 2022-01-20

### Fixed

- `registry`: fixed usage with source images and schema1-only images.
- `errata`: improved logging in one modulemd error case.

## [2.13.3] - 2021-12-06

### Fixed

- Fixed a crash when mixing `get_partial` with backends accepting a `url` (e.g. staged).

## [2.13.2] - 2021-12-03

### Fixed

- Ensure that `registry` source produces manifest pull specs for all manifest types

## [2.13.1] - 2021-11-24

### Fixed

- Fixed a crash in `registry` source when authentication is used

## [2.13.0] - 2021-11-08

### Added

- Introduced `registry` source for accessing images from a container image registry.

## [2.12.0] - 2021-10-18

### Changed

- Mitigate spurious timeout error by using `as_completed_with_timeout_reset`

## [2.11.0] - 2021-09-15

- `ErrataSource` now uses HTTPS when performing XML-RPC calls to Errata Tool.
  Previously, HTTP was used.

## [2.10.3] - 2021-08-27

### Fixed

- Fixed `KojiSource` crash bug introduced in 2.10.2.

## [2.10.2] - 2021-08-26

### Fixed

- Added a workaround for a thread-safety issue in pyasn1 in some legacy environments.

## [2.10.1] - 2021-08-11

### Fixed

- Added a missing dependency declaration on `scandir` for Python versions older than 3.5.

## [2.10.0] - 2021-08-10

### Changed

- Internally created executors are now named for improved metrics and debuggability.
- Library no longer has a hard dependency on Python bindings to `rpm`, if RPM-related
  functionality is not used.

## [2.9.0] - 2021-07-05

### Changed

- `Source` instances now support `with` statements to ensure that resources are freed
  when no longer required.

## [2.8.0] - 2021-06-25

### Added

- Added `build_info` attribute to push items.
- Added `module_build` attribute to RPM push items.
- Added `rpm_filter_arch` parameter to errata source, to select a subset of RPMs
  by architecture.
- Added `ModuleMdSourcePushItem` class. Source modulemd documents are now represented
  by this class rather than `ModuleMdPushItem`.
- Added many classes for container-related content, supported by `koji` and `errata`
  sources.

### Changed

- `errata` source now produces `ModuleMdSourcePushItem` where applicable, and respects
  FTP paths from Errata Tool for these items.
- `errata` source is now available for general use and is no longer marked as
  a technical preview.

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

[Unreleased]: https://github.com/release-engineering/pushsource/compare/v2.18.0...HEAD
[2.18.0]: https://github.com/release-engineering/pushsource/compare/v2.17.0...v2.18.0
[2.17.0]: https://github.com/release-engineering/pushsource/compare/v2.16.0...v2.17.0
[2.16.0]: https://github.com/release-engineering/pushsource/compare/v2.15.0...v2.16.0
[2.15.0]: https://github.com/release-engineering/pushsource/compare/v2.14.0...v2.15.0
[2.14.0]: https://github.com/release-engineering/pushsource/compare/v2.13.4...v2.14.0
[2.13.4]: https://github.com/release-engineering/pushsource/compare/v2.13.3...v2.13.4
[2.13.3]: https://github.com/release-engineering/pushsource/compare/v2.13.2...v2.13.3
[2.13.2]: https://github.com/release-engineering/pushsource/compare/v2.13.1...v2.13.2
[2.13.1]: https://github.com/release-engineering/pushsource/compare/v2.13.0...v2.13.1
[2.13.0]: https://github.com/release-engineering/pushsource/compare/v2.12.0...v2.13.0
[2.12.0]: https://github.com/release-engineering/pushsource/compare/v2.11.0...v2.12.0
[2.11.0]: https://github.com/release-engineering/pushsource/compare/v2.10.3...v2.11.0
[2.10.3]: https://github.com/release-engineering/pushsource/compare/v2.10.2...v2.10.3
[2.10.2]: https://github.com/release-engineering/pushsource/compare/v2.10.1...v2.10.2
[2.10.1]: https://github.com/release-engineering/pushsource/compare/v2.10.0...v2.10.1
[2.10.0]: https://github.com/release-engineering/pushsource/compare/v2.9.0...v2.10.0
[2.9.0]: https://github.com/release-engineering/pushsource/compare/v2.8.0...v2.9.0
[2.8.0]: https://github.com/release-engineering/pushsource/compare/v2.7.0...v2.8.0
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
