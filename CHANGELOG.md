# Changelog

## 0.3.8

- Kept NVMe temperature entities available when SMART health is unavailable but the agent still supplies a live hwmon temperature.
- Removed Home Assistant reserved `unknown` and `unavailable` states from core enum options.
- Mapped unsupported, unknown, and unavailable core enum readings to entity unavailability.
- Added regression coverage for the SMART hwmon fallback and reserved enum-state handling.

## 0.3.7

- Completed the Agent 2.8.3 sensor audit.
- Updated stale repository tests for the current integration version and network link-speed sensor.
- Added the selected network interface as the single explanatory attribute on network status.
- Updated the README sensor inventory.

## 0.3.6

- Added cooling-state, network-status, and network-link-speed sensors for Monitor Suite Agent 2.8.3.
- Added dynamic RAID status, SMART status, SMART temperature, and NVMe remaining-life regression coverage using the verified 2.8.3 response shape.

## 0.3.5

- Preserved the config-flow schema serialization fix from 0.3.4.
- Renamed the internal-rail power estimate to `Estimated power`.
- Set its suggested display precision to two decimal places.
- Removed the ambiguous aggregated `smart_status` attribute from RAID status sensors; per-device SMART sensors remain authoritative.
- Added regression checks for frontend schema serialization, sensor precision, power naming, and RAID attributes.

## 0.3.4

- Fixed the config flow HTTP 500 caused by the non-serializable `str.strip` validator in the host schema.
- Added a regression test that serializes the config flow schema through Home Assistant's serializer.

## 0.3.2

- Fixed config flow and options flow loading on Home Assistant 2025.12 by replacing the removed `FlowResult` import with `ConfigFlowResult`.

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
