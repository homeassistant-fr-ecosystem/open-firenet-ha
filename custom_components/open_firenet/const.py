DOMAIN = "open_firenet"

DEFAULT_SCAN_INTERVAL = 30  # seconds

API_STATUS   = "/api/status"
API_SENSORS  = "/api/sensors"
API_CONTROLS = "/api/controls"

OPERATING_MODES = {
    0: "manual",
    1: "auto",
    2: "comfort",
}
OPERATING_MODES_REVERSE = {v: k for k, v in OPERATING_MODES.items()}

# Candidate sensor keys for current room temperature (×10 encoding, e.g. 195 = 19.5°C).
# f0 is sRoomTemp_ACT from POST_SENSORS (confirmed in firmware comments).
ROOM_TEMP_KEYS = ["f0", "sRoomTemp_ACT", "tRoom", "temperatureRoom", "room_temp", "T_room"]

# Wire range is 140–280 (×10), i.e. 14.0–28.0°C
TEMP_MIN = 14.0
TEMP_MAX = 28.0
TEMP_STEP = 1.0

# Firmware enforces heatingPower >= 50 in parseDesiredControls and adjPow
HEATING_POWER_MIN = 50
HEATING_POWER_MAX = 100
