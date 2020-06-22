# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

- n/a

## [1.1.0] - 2020-06-23

### Fixed
- Fix too strict schema on erratum references; id and title are allowed to be null.
- Fix crash on Python 2 if using `get_partial` and `register_backend` together

### Changed
- Improved log message details in some cases of error

## 1.0.0 - 2020-06-16

- Initial stable release of project

[Unreleased]: https://github.com/release-engineering/pushsource/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/release-engineering/pushsource/compare/v1.0.0...v1.1.0
