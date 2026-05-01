# Nedap AEOS Inventory — Home Assistant integration

A Home Assistant custom integration that pulls Nedap AEOS / AEpu controller
inventory from the [InventoryAPI](https://github.com/forgottenruntime/InventoryAPI)
service and exposes each controller as a device with sensors and binary
sensors inside Home Assistant.

> **Companion repo.** The REST endpoint this integration consumes is provided
> by the InventoryAPI Python service. Deploy that on your AEOS server first
> (it ships a wizard-driven Windows installer), then point this integration
> at it.

## Features

- **One device per AEpu controller** — discovered automatically from the
  `/aeosws/inventory` payload, identified by `serial_number`.
- **Sensors:** IP, MAC, AEOS version, firmware name/version/date, boot
  firmware, controller board (`cb_type`), model, NTP server, AEserver host,
  memory free / total, disk free, uptime (duration), last reboot (timestamp).
- **Binary sensors:** online (connectivity), DHCP, SNMP agent, secure mode
  (lock), 802.1X.
- Configurable polling interval (default 5 minutes, min 30 s).
- Native config flow (no YAML required) with API-key validation on submit.
- Survives the API being temporarily down — entities go *unavailable*
  rather than disappearing.

## Requirements

- Home Assistant **2024.6** or newer.
- An InventoryAPI service reachable from Home Assistant on the LAN.
- The API key configured in InventoryAPI's `.env` (`INVENTORY_API_KEY`).

## Installation

### Via HACS (recommended)

1. In HACS → Integrations → ⋯ → *Custom repositories*, add this repo URL
   and select category **Integration**.
2. Search for "Nedap AEOS Inventory", install it, and restart Home Assistant.
3. *Settings → Devices & Services → + Add Integration → Nedap AEOS Inventory*.

### Manual

1. Copy the [`custom_components/aeos_inventory/`](custom_components/aeos_inventory/)
   folder into your Home Assistant `config/custom_components/` directory.
2. Restart Home Assistant.
3. *Settings → Devices & Services → + Add Integration → Nedap AEOS Inventory*.

## Configuration

The config flow asks for:

| Field | Default | Notes |
|---|---|---|
| Host or IP | — | Hostname/IP of the InventoryAPI service |
| Port | `8088` | The port chosen during InventoryAPI install |
| API key | — | Value of `INVENTORY_API_KEY` in InventoryAPI's `.env` |
| Use HTTPS | off | Enable if you've put a TLS reverse proxy in front |
| Verify TLS certificate | on | Disable for self-signed dev certs |

Polling interval is exposed under the integration's *Configure* button (30 s
to 24 h).

## Mapping (InventoryAPI → Home Assistant)

Each device is registered with:

- `identifiers`: `(aeos_inventory, <serial_number>)`
- `name`: `host_name`
- `manufacturer`: `Nedap N.V.`
- `model`: `model` (AEbridge) or `cb_type` (controller board)
- `sw_version`: `aeos_version`
- `hw_version`: `production_date`
- `serial_number`: `serial_number`
- `configuration_url`: `http://<ip_address>` when present

## Development

```bash
git clone https://github.com/forgottenruntime/ha-aeos-inventory.git
# Symlink into your dev HA config
ln -s "$PWD/ha-aeos-inventory/custom_components/aeos_inventory" \
      ~/.homeassistant/custom_components/aeos_inventory
```

## License

MIT — see [LICENSE](LICENSE).
