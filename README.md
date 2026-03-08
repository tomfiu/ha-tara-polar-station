# Tara Polar Station Tracker

Home Assistant custom integration that tracks the Tara Polar Station and enriches raw telemetry with polar expedition analytics.

## Features

- Real-time latitude, longitude, speed, course, and report timestamp
- Derived metrics: distance from home, distance to North Pole, bearing from home
- Expedition analytics: mission phase and days since departure
- Polar context: Arctic Circle status, polar day/night, stationary detection
- Optional webcam entity
- Event publishing for milestones and movement state changes

## Screenshots

Add screenshots in `docs/images/` and reference them here.

![Map Example](docs/images/map-example.png)
![Entities Example](docs/images/entities-example.png)

## Installation

### HACS (recommended)

1. Open HACS in Home Assistant.
2. Go to `Integrations`.
3. Add custom repository: `https://github.com/tomasfiurasek/ha-tara-polar-station`.
4. Select category `Integration`.
5. Install `Tara Polar Station Tracker`.
6. Restart Home Assistant.
7. Add integration from `Settings -> Devices & Services`.

### Manual

1. Copy `custom_components/tara_polar_station` into your Home Assistant `custom_components` directory.
2. Restart Home Assistant.
3. Add integration from `Settings -> Devices & Services`.

## Configuration

Initial setup uses UI config flow with no required fields.

Options:

- `poll_interval` (minutes, default: 15)
- `home_coordinates_override` (`<lat>,<lon>`)
- `enable_webcam` (default: false)

## Entities

### Sensors

- `sensor.tara_latitude`
- `sensor.tara_longitude`
- `sensor.tara_speed`
- `sensor.tara_course`
- `sensor.tara_last_report`
- `sensor.tara_distance_from_home`
- `sensor.tara_distance_to_north_pole`
- `sensor.tara_bearing_from_home`
- `sensor.tara_days_since_departure`
- `sensor.tara_solar_elevation`
- `sensor.tara_mission_phase`

### Binary sensors

- `binary_sensor.tara_in_arctic_circle`
- `binary_sensor.tara_in_polar_day`
- `binary_sensor.tara_in_polar_night`
- `binary_sensor.tara_stationary`

### Optional camera

- `camera.tara_polar_station`

## Events

- `tara_position_updated`
- `tara_entered_arctic_circle`
- `tara_entered_polar_night`
- `tara_stationary`
- `tara_resumed_transit`

Example payload:

```json
{
  "latitude": 79.332,
  "longitude": -23.992,
  "speed": 0.3,
  "distance_to_pole": 1180,
  "timestamp": "2026-03-08T12:30:00+00:00"
}
```

## Example Automations

### Notify when station enters polar night

```yaml
trigger:
  - platform: state
    entity_id: binary_sensor.tara_in_polar_night
    to: "on"
action:
  - service: notify.mobile_app
    data:
      message: "Tara Polar Station has entered polar night"
```

### Display station distance

```jinja2
Distance to North Pole: {{ states('sensor.tara_distance_to_north_pole') }} km
```

## Development

Run tests:

```bash
pytest
```

## Notes on Data Sources

Telemetry endpoints can change. The integration tries a small list of public endpoints and marks entities unavailable when no valid telemetry can be fetched.
