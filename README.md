# Member Audit Secure Groups Integration for Alliance Auth<a name="member-audit-secure-groups-integration-for-alliance-auth"></a>

This is an integration between [Member Audit](https://gitlab.com/ErikKalkoken/aa-memberaudit) and [Secure Groups](https://github.com/pvyParts/allianceauth-secure-groups) for [Alliance Auth](https://gitlab.com/allianceauth/allianceauth) (AA).

![release](https://img.shields.io/pypi/v/aa-memberaudit-securegroups?label=release)
![License](https://img.shields.io/badge/license-GPL-green)
![python](https://img.shields.io/pypi/pyversions/aa-memberaudit-securegroups)
![django](https://img.shields.io/pypi/djversions/aa-memberaudit-securegroups?label=django)
![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)
![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)

______________________________________________________________________

<!-- mdformat-toc start --slug=gitlab --maxlevel=6 --minlevel=1 -->

- [Member Audit Secure Groups Integration for Alliance Auth](#member-audit-secure-groups-integration-for-alliance-auth)
  - [Features](#features)
  - [Installation](#installation)
    - [Requirements](#requirements)
    - [Step 1: Install the Package](#step-1-install-the-package)
    - [Step 2: Config](#step-2-config)
    - [Step 3: Finalize App Installation](#step-3-finalize-app-installation)
  - [Filters](#filters)
  - [Changelog](#changelog)

<!-- mdformat-toc end -->

______________________________________________________________________

## Features<a name="features"></a>

- Activity Filter
- Asset Filter
- Character Age Filter
- Compliance Filter
- Corporation Role Filter
- Corporation Title Filter
- Skill Set Filter
- Skill Point Filter
- Time in Corporation Filter

## Installation<a name="installation"></a>

### Requirements<a name="requirements"></a>

This integration needs [Member Audit](https://gitlab.com/ErikKalkoken/aa-memberaudit) and [Secure Groups](https://github.com/pvyParts/allianceauth-secure-groups) to function. Please make sure they are installed before continuing.

### Step 1: Install the Package<a name="step-1-install-the-package"></a>

Make sure you are in the virtual environment (venv) of your Alliance Auth installation. Then install the newest release from PyPI:

`pip install aa-memberaudit-securegroups`

### Step 2: Config<a name="step-2-config"></a>

Add `memberaudit_securegroups` to your `INSTALLED_APPS`.

### Step 3: Finalize App Installation<a name="step-3-finalize-app-installation"></a>

Run migrations:

```bash
python manage.py migrate
```

Restart your supervisor services for Auth

## Filters<a name="filters"></a>

| Filter Name        | Matches if...                                                           |
|--------------------|-------------------------------------------------------------------------|
| Activity Filter    | User has *at least one* character active within the last X days         |
| Age Filter         | User has *at least one* character over X days old                       |
| Asset Filter       | User has *at least one* character with *any of* the assets defined      |
| Compliance Filter  | User has *all* characters registered on Member Audit                    |
| Skill Point Filter | User has *at least one* character with at least X skill points          |
| Skill Set Filter   | User has *at least one* character with *any of* the selected skill sets |

## Changelog<a name="changelog"></a>

See [CHANGELOG.md](https://gitlab.com/eclipse-expeditions/aa-memberaudit-securegroups/-/blob/master/CHANGELOG.md)
