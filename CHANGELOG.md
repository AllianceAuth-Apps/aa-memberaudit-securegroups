# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [In Development]

## [2.0.0] - TBD

This release adds support for Alliance Auth V5 and contains breaking changes and fixes.

### Update notes

If you are updating from an existing [aa-ma-securegroups](https://github.com/ppfeufer/aa-ma-securegroups) installation, please follow the update instructions in the README: **Updating from aa-ma-securegroups**

### Changed

- BREAKING CHANGE: Removed support for Python 3.8
- BREAKING CHANGE: Removed support for Python 3.9
- BREAKING CHANGE: Now requires Member Audit 5+
- BREAKING CHANGE: Now requires Secure Groups 0.10.1+
- Added support for AA 5
- Removed unused module `memberaudit.py`
- Refactoring
- Modernized and extended tests
- Updated documentation

### Fixed

- HomeStationFilter not working correctly
- AltFilter not returning audit data for non-matching users
- ActivityFilter not returning audit data for non-matching users

## [1.6.1] - 2025-11-04

### Fixed

- Django `makemessages` seems to be ignoring f-strings now

### Changed

- Translations updated

## [1.6.0] - 2025-08-05

### Added

- Home Station (Death Clone) smart filter

### Changed

- Translations updated

## [1.5.2] - 2025-06-03

### Changed

- Translations updated

## [1.5.1] - 2025-05-05

### Changed

- Translations updated

## [1.5.0] - 2025-01-06

### Added

- End date to the `TimeInCorporationFilter` for reverse logic

### Changed

- Filter messages made translatable

## [1.4.0] - 2024-12-31

### Added

- Checkbox to reverse logic for `TimeInCorporationFilter`, which comes in handy
  when you want to put characters that are not in the corporation for a
  certain amount of time in a group, like for a probation period.

## [1.3.1] - 2024-12-14

### Added

- Python 3.13 to the test matrix

### Changed

- Simplify code for `ComplianceFilter.audit_filter` logic
- Translations updated

## [1.3.0] - 2024-12-06

### Added

- Proper filter names
- Reversed logic to compliance filter (optional)
- Testing for Python 3.13

### Changed

- Several code improvements

## [1.2.0] - 2024-10-10

### Changed

- Dependencies updated
  - `allianceauth`>=4.3.1
  - `aa-memberaudit`>=3.10.0
- Japanese translation improved
- Lingua codes updated to match Alliance Auth v4.3.1

## [1.1.0] - 2024-07-27

### Added

- Prepared Czech translation for when Alliance Auth supports it

### Changed

- French translation improved
- Russian translation improved

### Removed

- Support for Python 3.8 and Python 3.9

## [1.0.1] - 2024-05-16

### Changed

- Translations updated

## [1.0.0] - 2024-03-16

### Added

- Corp title filter (Thanks to @ErikKalkoken)
- Time in corp filter (Thanks to @ErikKalkoken)

## [0.6.1] - 2023-10-22

### Fixed

- Smart Group failed to process when filter requirements are not met

## [0.6.0] - 2023-10-19

### Added

- Support for corporation role filter (Thanks to @ErikKalkoken)
- Character type selector to skill set filter (This allows creating auto groups for
  something like fax alts) (Thanks to @ErikKalkoken)

### Fixed

- Capitalization for translatable strings

### Changed

- Page load of asset filter form improved (Thanks to @ErikKalkoken)
- Performance of asset and compliance filters improved (Thanks to @ErikKalkoken)
- App renamed, so it is sorted next to "Secure Groups" on the admin page (since those
  two are used together) (Thanks to @ErikKalkoken)
- Dependency to Member Audit
  - aa-memberaudit>=3.3.1
- Translations updated

## [0.5.0] - 2023-09-02

### Added

- Korean translation

## [0.4.0] - 2023-08-15

### Added

- Names of missing characters when the compliance filter fails
- Spanish translation

### Changed

- Moved the build process to PEP 621 / pyproject.toml
- Character names sorted alphabetically in all filters

## [0.3.0] - 2023-05-31

### Fixed

- Migration dependency for Member Audit >= 2.0.0

### Changed

- Dependencies:
  - `aa-memberaudit>=2.0.0`
  - `allianceauth>=3.0.0`
  - `allianceauth-securegroups>=0.5.1`

## [0.2.0] - 2023-02-27

### Added

- Secure Group's audit filter to the filters for better visual feedback

## [0.1.0] - 2022-08-06

### Fixed

- Compatibility to the Member Audit >=1.15.1 and its changes to the `Character` model

### Added

- Makefile
- Editorconfig

### Changed

- Several configs updated
- Requirements
  - `allianceauth>=2.15.1`
  - `aa-memberaudit>=1.15.1`
  - `allianceauth-securegroups>=0.2.1`
  - `python>=3.8`

### Removed

- Unused files

## [0.1.0a3] - 2021-01-16

### Fixed

- Bug involving skillpoint filter

## [0.1.0a2] - 2021-01-05

### Added

- Activity Filter
- Age Filter
- Skill Point Filter

### Changed

- Improved Admin Panel

## [0.1.0a1] - 2021-01-05

### Added

- Initial Release
