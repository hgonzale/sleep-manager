# homebridge-sleep-manager

Custom Homebridge plugin for sleep-manager. Requires Homebridge ≥ 2.0.

## Features

- **On/Off switch**: turns sleeper on (Wake-on-LAN) or off (suspend)
- **StatusFault**: shows a warning icon in Apple Home when a wake attempt fails (state = `FAILED`)
- **Polling**: calls `GET /waker/status` every 30s (configurable); no live probe to sleeper

## State → HomeKit mapping

| State machine state | Switch.On | StatusFault    |
|---------------------|-----------|----------------|
| `ON`                | true      | NO_FAULT       |
| `OFF`               | false     | NO_FAULT       |
| `WAKING`            | false     | NO_FAULT       |
| `FAILED`            | false     | GENERAL_FAULT  |

## Installation

Copy this directory into your Homebridge plugin path, or install locally:

```bash
npm install -g /path/to/homebridge-sleep-manager
```

## Homebridge config.json

Add to the `accessories` array:

```json
{
  "accessory": "SleepManagerSwitch",
  "name": "My PC",
  "waker_url": "http://waker_url:51339",
  "api_key": "your-secure-api-key-here",
  "poll_interval": 30
}
```

## API Endpoints Used

- **Wake**: `GET /waker/wake`
- **Suspend**: `GET /waker/suspend`
- **Status**: `GET /waker/status`

## Troubleshooting

```bash
curl -H "X-API-Key: your-api-key" http://waker_url:51339/waker/status
# Expected: {"op": "status", "state": "OFF", "homekit": "off"}
```
