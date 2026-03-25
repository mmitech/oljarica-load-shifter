# Oljarica Load Shifter

A Python-based power load shifting system that dynamically manages Bitcoin ASIC miners based on real-time power output from a small hydroelectric plant. The system monitors power generation via MQTT and automatically starts or stops miners to match available capacity, maximizing energy utilization without exceeding grid limits.

## How It Works

The system connects to power monitoring equipment at the hydro plant via MQTT, reads real-time generation data, and calculates how many ASIC miners can run within the available power envelope. When generation increases, miners are brought online. When it drops, miners are gracefully shut down — all automatically.

```
Hydro Plant → MQTT Broker → Load Shifter → Miner Fleet (via pyasic)
```

The load shifting loop runs on a configurable interval (default: 60 seconds), continuously adjusting the active miner count to track power output. A configurable buffer prevents rapid start/stop cycling caused by natural fluctuations in hydro generation.

## Features

- **Real-time load matching** — dynamically adjusts the number of active miners based on live power generation data received over MQTT
- **MQTT-based architecture** — built-in MQTT broker and client for communication with power monitoring hardware (controllers/sensors)
- **Fleet management** — manages up to 50+ ASIC miners simultaneously using [pyasic](https://github.com/UpstreamData/pyasic) for hardware-agnostic miner control
- **Temperature-aware operation** — optionally halts mining when ambient temperature exceeds a threshold, useful for air-cooled setups where noise from fans at high temperatures may be a concern
- **Time-based scheduling** — optional start/stop hours for mining (e.g., mine only during off-peak hours), can be overridden to run continuously
- **Configurable power buffer** — a tunable buffer (in kW) absorbs short-term power fluctuations without triggering unnecessary miner state changes
- **Auto-recovery** — automatically reconnects and resumes operation after errors, network interruptions, or miner communication failures
- **SSL/TLS support** — MQTTS with self-signed or CA-signed certificates for secure communication
- **Miner reboot support** — optional reboot instead of pause for pools that drop idle sessions (DDoS protection workaround)

## Requirements

- Python 3.8+
- MQTT-capable power monitoring hardware at the generation site
- Network access to ASIC miners (tested with Antminer S19 series)

## Installation

```bash
git clone https://github.com/mmitech/oljarica-load-shifter.git
cd oljarica-load-shifter
pip install -r requirements.txt
```

## Configuration

Copy the example config and edit it to match your setup:

```bash
cp config-example.py config.py
```

Key configuration options:

| Parameter | Description | Default |
|---|---|---|
| `run_non_stop` | Ignore time schedule, mine whenever power is available | `True` |
| `start_hour` / `stop_hour` | Mining window (used when `run_non_stop` is `False`) | 19:00–08:00 |
| `buffer` | Power buffer in kW to absorb generation fluctuations | `10` |
| `sleep_duration` | Seconds between load adjustment cycles | `60` |
| `miner_avg_kw` | Average power draw per miner (kW), used for capacity calculation | `2.6` |
| `temp_halt` | Enable temperature-based mining halt | `True` |
| `temp_halt_ambient` | Ambient temperature threshold (°C) to pause mining | `20` |
| `reboot` | Reboot miners instead of pausing (for pool compatibility) | `False` |
| `miners_ips` | Dictionary mapping miner hostnames to IP addresses | — |
| `power_topic` | MQTT topic for power generation readouts | — |
| `credentials` | MQTT broker username/password | — |
| `ssl` | Paths to SSL key and certificate for MQTTS | — |

### MQTT Authentication

Generate a password hash for the MQTT broker:

```bash
python passhash.py
```

Update `auth.conf` with the generated credentials.

## Usage

```bash
python main.py
```

The system will:

1. Start the built-in MQTT broker
2. Connect to the power monitoring topic and begin receiving generation data
3. Initialize connections to all configured miners via pyasic
4. Enter the load shifting loop — adjusting active miners every `sleep_duration` seconds
5. Log all decisions and state changes

Press `Ctrl+C` to stop gracefully.

## Architecture

```
┌──────────────────┐     MQTT      ┌──────────────────┐
│  Hydro Plant     │──────────────▶│  MQTT Broker     │
│  Power Monitor   │   (readouts)  │  (built-in)      │
└──────────────────┘               └────────┬─────────┘
                                            │
                                   ┌────────▼─────────┐
                                   │  Load Shifter    │
                                   │  (manager.py)    │
                                   └────────┬─────────┘
                                            │
                              ┌─────────────┼─────────────┐
                              │             │             │
                        ┌─────▼───┐   ┌─────▼───┐   ┌─────▼───┐
                        │ Miner 1 │   │ Miner 2 │   │ Miner N │
                        │ (pyasic)│   │ (pyasic)│   │ (pyasic)│
                        └─────────┘   └─────────┘   └─────────┘
```

## Project Structure

```
oljarica-load-shifter/
├── main.py              # Entry point — starts broker, client, and load shifting loop
├── config-example.py    # Example configuration with all available options
├── auth.conf            # MQTT broker authentication configuration
├── passhash.py          # Utility to generate MQTT password hashes
├── requirements.txt     # Python dependencies
├── src/
│   ├── broker.py        # Built-in MQTT broker (asyncio)
│   ├── client.py        # MQTT client — subscribes to power readout topics
│   ├── manager.py       # Core logic — miner data collection and load shifting decisions
│   └── logger.py        # Logging configuration
└── LICENSE              # MIT License
```

## Background

This project was built to solve a real problem: efficiently utilizing variable power output from a small hydroelectric plant for Bitcoin mining. Hydro generation fluctuates with water flow, and running miners at full capacity during low-output periods would either pull from the grid or trip breakers. Manual management of dozens of miners is impractical, so this system automates the process entirely.

The "Oljarica" name refers to the hydroelectric site where this system was originally deployed.

## Author

Built by [Mourad Ilyes Mlik](https://github.com/mmitech) at [MMITech](https://mmitech.si), a hosting and infrastructure provider based in Kranj, Slovenia.

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.