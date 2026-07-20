# Project Rules: Open Firenet Home Assistant Integration

## 1. Project Context
This integration enables Home Assistant to control Rika pellet stoves via the [open-firenet](https://github.com/openfirenet/open-firenet) local WiFi bridge, replacing proprietary cloud dependencies with local control.

## 2. Standards
- Refer to `/.gemini/rules/shared_python.md` for all development, testing, linting, and type-checking standards.

## 3. Project-Specific Notes
- **Domain**: `open_firenet`
- **Pattern**: Follow existing patterns for climate, binary_sensor, and sensor entities.
