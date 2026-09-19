# Monitor Suite for Home Assistant

[![Validate](https://github.com/swetoast/ha-monitor-suite/actions/workflows/validate.yml/badge.svg)](https://github.com/swetoast/ha-monitor-suite/actions/workflows/validate.yml)
[![HACS](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Monitor Suite brings useful Raspberry Pi health and performance data into Home Assistant. It connects directly to a Monitor Suite Agent on the local network and creates a focused set of clear entities instead of exposing every raw API value.

## Highlights

- Monitors CPU, memory, storage, network, power, cooling, RAID, and SMART health.
- Uses one shared local status request for all entities.
- Creates focused sensors with Home Assistant device classes, units, state classes, and dynamic icons.
- Discovers Linux MD arrays and supported SMART measurements automatically.
- Supports setup, reauthentication, reconfiguration, and configurable polling from the Home Assistant UI.
- Keeps API tokens, host names, RAID names, and SMART device paths out of diagnostics.
- Preserves entity and device identities when the agent address changes.
- Requires no cloud service.

## How it works

```text
Raspberry Pi                  Home Assistant
+-------------------+         +---------------------------+
| Monitor Suite     |  HTTP   | Monitor Suite integration |
| Agent             | ------> | Sensors and device data   |
| /health /status   |  LAN    | Diagnostics and options   |
+-------------------+         +---------------------------+
```

The integration polls the agent's `/status` endpoint and shares each response across all entities. The `/health` endpoint is used while validating a new or changed connection.

## Requirements

- Home Assistant 2025.12.2 or newer
- A reachable Monitor Suite Agent
- The agent host, port, and API token
- HACS 2.0.0 or newer when installing through HACS

The agent must be reachable directly from Home Assistant over the trusted local network.

## Installation

### HACS

1. Open HACS in Home Assistant.
2. Open the menu and choose **Custom repositories**.
3. Add `https://github.com/swetoast/ha-monitor-suite` as an **Integration** repository.
4. Search for **Monitor Suite** and install it.
5. Restart Home Assistant.

### Manual installation

1. Copy `custom_components/monitor_suite` from this repository into the Home Assistant configuration directory.
2. Confirm that the final path is:

   ```text
   /config/custom_components/monitor_suite
   ```

3. Restart Home Assistant.

## Setup

1. Open **Settings > Devices & services**.
2. Select **Add integration**.
3. Search for **Monitor Suite**.
4. Enter the agent host, port, and API token.

The integration verifies authentication and validates complete health and status responses before creating the entry.

## Usage

After setup, Home Assistant creates a Monitor Suite device containing the available entities. Use those entities in dashboards, automations, history, and alerts like any other Home Assistant sensor.

The integration creates these core sensors when their values are available:

- Overall status
- CPU usage with temperature and frequency attributes
- Memory usage
- Root filesystem usage
- Power and input voltage
- Fan speed with cooling-state attribute
- Network status with interface, link speed, download, and upload attributes
- Disk read and write rates
- Last boot

The compound CPU sensor uses this structure:

```yaml
sensor.hyperion_cpu_usage:
  state: 14.8
  attributes:
    temperature: 35.3
    frequency: 1500
```

The compound fan sensor uses this structure:

```yaml
sensor.hyperion_fan_speed:
  state: 0
  attributes:
    cooling_state: idle
```

The compound network sensor uses this structure:

```yaml
sensor.hyperion_network_status:
  state: up
  attributes:
    interface: eth0
    link_speed: 1000
    download: 5531
    upload: 8072
```

For each detected Linux MD array, the integration creates one RAID status sensor.

For each detected SMART device, the integration creates one SMART status sensor. Temperature and remaining life are included as attributes when supplied by the agent:

```yaml
sensor.hyperion_nvme0n1_smart_status:
  state: healthy
  attributes:
    temperature: 19.85
    remaining_life: 98
```

Entities are added only when the agent reports the corresponding capability. Raw duplicates, internal counters, serial numbers, power-on hours, total byte counts, and similar low-value fields are intentionally not exposed.

## Attribute units

Attribute names describe the measurement without embedding the unit in the name.

- `temperature`: degrees Celsius
- `frequency`: megahertz
- `remaining_life`: percent
- `link_speed`: megabits per second
- `download`: bytes per second
- `upload`: bytes per second

## Options

Open the integration and select **Configure** to change the polling interval.

- Default: 10 seconds
- Minimum: 5 seconds
- Maximum: 300 seconds

Changing the interval reloads the integration automatically. Individual entities can be enabled or disabled through Home Assistant's entity registry.

## Reconfiguration and authentication

Use **Reconfigure** from the integration page to change the agent host, port, or API token. Leaving the token field empty keeps the existing token.

If the agent rejects the stored token, Home Assistant starts a reauthentication flow. Updating the agent address does not replace existing entities or devices.

## Availability and error handling

Entities become unavailable when the shared coordinator cannot obtain a valid status response. The integration handles authentication failures, connection errors, request timeouts, unexpected redirects, malformed JSON, incomplete payloads, and agents that are not ready to provide a status sample.

A successful later poll restores entity availability automatically.

## Diagnostics and privacy

Home Assistant diagnostics include:

- Whether connection fields are configured
- The validated polling interval
- Coordinator status
- Non-sensitive platform information
- RAID and SMART capability counts
- The compact agent health block

Diagnostics do not include host names, API tokens, RAID names, SMART device paths, serial numbers, or other raw storage identifiers.

## Troubleshooting

### The integration cannot connect

- Confirm that Home Assistant can reach the agent host and port over the local network.
- Confirm that the Monitor Suite Agent service is running.
- Check that the configured API token matches the agent token.
- Confirm that no firewall rule blocks Home Assistant from reaching the agent.

### Entities are unavailable

- Open the integration entry and check whether it reports a setup or authentication error.
- Verify that the agent returns a complete `/status` response.
- Allow the agent time to collect its first sample after startup.

### A RAID or SMART entity is missing

Dynamic entities are created only when the agent reports a supported array or storage device. Confirm that the agent can read the relevant RAID or SMART data on the monitored system.

### The validation badge does not appear

Confirm that the workflow exists at this exact path:

```text
.github/workflows/validate.yml
```

The filename must match the path used by the validation badge.

## Support and feedback

Use the repository's [issue tracker](https://github.com/swetoast/ha-monitor-suite/issues) to report bugs or request improvements.

Include the following information when reporting a problem:

- Home Assistant version
- Monitor Suite integration version
- Monitor Suite Agent version
- Relevant logs

Remove private network details and API tokens before posting.

## Development

The repository includes automated checks for Python syntax, formatting, linting, config-entry flows, migration behavior, diagnostics privacy, attribute naming, HACS metadata, and Home Assistant integration structure.

Run the local repository checks with:

```bash
python -m pytest -q
python -m ruff check custom_components tests
python -m ruff format --check custom_components tests
```

See [CHANGELOG.md](CHANGELOG.md) for release history.

## Author

Monitor Suite is maintained by [@swetoast](https://github.com/swetoast).

## License

Monitor Suite is released under the [MIT License](LICENSE).
