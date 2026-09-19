# Changelog

## 0.3.1

- Reworked the README around a concise project overview and clear highlights.
- Added a visual explanation of the agent-to-Home Assistant data flow.
- Separated installation, setup, everyday usage, options, privacy, and troubleshooting guidance.
- Added direct support, development, author, release history, and license links.
- Clarified which entities are created and why some raw agent values are intentionally not exposed.

## 0.3.0

- Separated mutable endpoint identity from stable device and entity identity.
- Added config-entry migration for existing version 1 entries.
- Updated reconfiguration to change the endpoint unique ID without replacing entities.
- Removed host names and storage device paths from diagnostics.
- Replaced diagnostic path lists with capability counts.
- Added defensive polling-interval validation for stored options.
- Added the repository code owner and HACS brand icon.
- Added HACS, Hassfest, Ruff, formatting, and pytest validation workflows.
- Added Home Assistant behavior tests for setup, reconfiguration, options, migration, and diagnostics.
- Removed the incorrect Toast hardware manufacturer value and made device names distinct per entry.

## 0.2.0

- Added a dedicated `options.py` flow for a 5 to 300 second update interval.
- Added automatic integration reload after option changes.
- Refactored initial setup, reauthentication, and reconfiguration into explicit flows with shared connection validation.
- Prevented the existing API token from being displayed during reconfiguration.
- Added normalized endpoint identities and duplicate-endpoint protection.
- Removed the redundant health request during normal integration startup.
- Polished sensor value validation, timestamp handling, approved attributes, and dynamic RAID and SMART discovery.
- Added privacy-conscious Home Assistant diagnostics without host or token disclosure.
- Expanded repository regression checks for options, diagnostics, HACS metadata, translations, focused entities, and packaging.

## 0.1.1

- Added explicit request timeouts and controlled handling for redirects, malformed JSON, authentication failures, unavailable samples, and invalid API structures.
- Added reauthentication and reconfiguration flows.
- Changed device and entity identities to use the stable config-entry unique ID.
- Added enum sensor metadata and translated states for overall, RAID, and SMART status sensors.
- Moved state-based and numeric-range icon behavior into `icons.json`.
- Corrected unavailable handling for RAID and SMART entities.
- Added HACS repository metadata and an MIT license.

## 0.1.0

- Added the first Monitor Suite Home Assistant custom integration.
- Added UI setup, shared polling, core sensors, RAID sensors, and SMART sensors.
