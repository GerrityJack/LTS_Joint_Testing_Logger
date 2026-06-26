"""
lab_config.py
─────────────────────────────────────────────────────────────────────────────
Central settings for the LakeShore 218 / Keithley 2401 logging system.
Edit the values below to match your hardware. Every script imports this
file — change it once and both loggers pick it up.
"""

# ── Serial ports ──────────────────────────────────────────────────────────────
# Check Device Manager -> Ports (COM & LPT) to confirm these after plugging
# in the RS232-to-USB adapters. Windows may reassign the COM number if an
# adapter is moved to a different USB port.
LAKESHORE_PORT = "COM3"
KEITHLEY_PORT  = "COM4"

# ── LakeShore 218 serial settings ─────────────────────────────────────────────
# Factory default per the Model 218 manual: 9600 baud, 7 data bits, odd
# parity, 1 stop bit. Confirm against the rear-panel DIP switches if the
# instrument doesn't respond.
LAKESHORE_BAUD       = 9600
LAKESHORE_DATA_BITS  = 7
LAKESHORE_PARITY     = "odd"      # "odd", "even", or "none"
LAKESHORE_STOP_BITS  = 1
LAKESHORE_TIMEOUT_MS = 5000

# Which input channels to log (LakeShore 218 has 8). KRDG? 0 returns all
# eight in one query, so leaving this at 8 has no extra cost even if some
# channels have no sensor wired up (those just read ~0 or an out-of-range
# value, which is fine to log).
LAKESHORE_NUM_CHANNELS = 8

# ── Keithley 2401 interface ───────────────────────────────────────────────────
# "GPIB" (via a GPIB controller card + cable, e.g. Keysight 10833F cable into a
# PCIe GPIB card) or "RS232" (via USB-to-serial adapter). GPIB requires the
# card vendor's VISA runtime installed (e.g. Keysight IO Libraries Suite, or
# NI-VISA) -- pyvisa-py does NOT support GPIB, only the RS232 path below uses it.
KEITHLEY_INTERFACE = "GPIB"

# GPIB address set on the instrument's front panel:
# MENU -> COMMUNICATION -> GPIB. Default on the 2401 is commonly 24, but
# confirm against what's actually shown on the panel.
KEITHLEY_GPIB_ADDRESS = 24
# GPIB controller/board index. "GPIB0" is correct if there's only one GPIB
# card/controller installed on the machine (the normal case).
KEITHLEY_GPIB_BOARD = 0

# ── Keithley 2401 RS232 settings (only used if KEITHLEY_INTERFACE = "RS232") ──
# Must match what's set on the instrument's front panel:
# MENU -> COMMUNICATION -> RS-232 -> BAUD / BITS / PARITY / TERMINATOR
KEITHLEY_BAUD       = 9600
KEITHLEY_DATA_BITS  = 8
KEITHLEY_PARITY     = "none"
KEITHLEY_STOP_BITS  = 1
KEITHLEY_TIMEOUT_MS = 5000
# Terminator the 2401 is configured to send/expect. Common options are
# "\r\n" or "\n" depending on the front-panel LFEED/terminator setting.
KEITHLEY_TERMINATION = "\r\n"

# Which measurement elements to request each read. The 2401 returns these
# comma-separated, in this order, in response to :READ?
KEITHLEY_ELEMENTS = ["VOLT", "CURR", "RES"]

# ── QuestDB ────────────────────────────────────────────────────────────────────
QUESTDB_HOST = "localhost"
QUESTDB_PORT = 9000   # HTTP/ILP port used by the questdb Python client

QUESTDB_EXE_PATH = r"C:\Users\scuser\Program\questdb\bin\questdb.exe"

# ── Grafana (dashboard) ────────────────────────────────────────────────────────
GRAFANA_HOME = r"C:\Users\scuser\Program\grafana"
GRAFANA_EXE_PATH = r"C:\Users\scuser\Program\grafana\bin\grafana-server.exe"
GRAFANA_PORT = 3000

LAKESHORE_TABLE = "lakeshore218_temps"
KEITHLEY_TABLE  = "keithley2401_smu"

# ── Polling ────────────────────────────────────────────────────────────────────
POLL_INTERVAL_S = 10
