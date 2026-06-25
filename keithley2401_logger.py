"""
keithley2401_logger.py
─────────────────────────────────────────────────────────────────────────────
Polls a Keithley Model 2401 SourceMeter over RS232 (via USB-serial adapter)
using PyVISA, and writes Voltage/Current/Resistance readings to QuestDB
every lab_config.POLL_INTERVAL_S seconds.

This logs whatever the instrument is currently configured to source/measure
— it does not change source settings, output state, or run a sweep. If you
need it to actively source/step values as part of logging, let me know and
I'll extend this.

Run standalone:
    python keithley2401_logger.py

Dependencies:
    pip install pyvisa pyvisa-py pyserial questdb

To run, edit lab_config.py:
    KEITHLEY_PORT        -> the COM port assigned to the adapter
    KEITHLEY_TERMINATION -> must match the instrument's front-panel RS232
                            terminator setting (MENU -> COMMUNICATION -> RS-232)
"""

import sys
import time
import signal

import pyvisa
from questdb.ingress import TimestampNanos

import lab_config as cfg
from questdb_client import get_sender

_PARITY_MAP = {
    "none": pyvisa.constants.Parity.none,
    "odd":  pyvisa.constants.Parity.odd,
    "even": pyvisa.constants.Parity.even,
}

_STOPBITS_MAP = {
    1: pyvisa.constants.StopBits.one,
    2: pyvisa.constants.StopBits.two,
}

# Keithley overflow placeholder for a measurement function that isn't
# currently enabled/active on the instrument.
_OVERFLOW = 9.9e37

_running = True


def _handle_shutdown(signum, frame):
    global _running
    print("\n[KEITHLEY] Shutdown signal received, finishing current cycle...")
    _running = False


signal.signal(signal.SIGINT, _handle_shutdown)
signal.signal(signal.SIGTERM, _handle_shutdown)


def connect_instrument():
    """Open the Keithley 2401 over RS232 via PyVISA and set the read format."""
    rm = pyvisa.ResourceManager("@py")
    resource_name = f"ASRL{cfg.KEITHLEY_PORT.replace('COM', '')}::INSTR"
    inst = rm.open_resource(resource_name)
    inst.baud_rate = cfg.KEITHLEY_BAUD
    inst.data_bits = cfg.KEITHLEY_DATA_BITS
    inst.parity = _PARITY_MAP[cfg.KEITHLEY_PARITY]
    inst.stop_bits = _STOPBITS_MAP[cfg.KEITHLEY_STOP_BITS]
    inst.write_termination = cfg.KEITHLEY_TERMINATION
    inst.read_termination = cfg.KEITHLEY_TERMINATION
    inst.timeout = cfg.KEITHLEY_TIMEOUT_MS

    # Fix which elements :READ? returns, in a known order, every time.
    elements = ",".join(cfg.KEITHLEY_ELEMENTS)
    inst.write(f":FORM:ELEM {elements}")

    return rm, inst


def read_measurement(inst) -> dict:
    """
    Sends :READ? and parses the comma-separated response according to
    lab_config.KEITHLEY_ELEMENTS. Returns a dict, e.g. {"voltage": ...,
    "current": ..., "resistance": ...}. Values equal to the Keithley's
    overflow placeholder (9.9e37) mean that function isn't active and are
    omitted rather than logged as a misleading number.
    """
    name_map = {"VOLT": "voltage", "CURR": "current", "RES": "resistance"}

    response = inst.query(":READ?").strip()
    raw_values = [v.strip() for v in response.split(",")]

    readings = {}
    for elem, raw in zip(cfg.KEITHLEY_ELEMENTS, raw_values):
        col_name = name_map.get(elem, elem.lower())
        try:
            val = float(raw)
            if abs(val) >= _OVERFLOW * 0.99:
                continue  # function not active on the instrument right now
            readings[col_name] = val
        except ValueError:
            print(f"[KEITHLEY] WARNING: could not parse {elem} value: '{raw}'")
    return readings


def main():
    print(f"[KEITHLEY] Starting — port={cfg.KEITHLEY_PORT}, "
          f"interval={cfg.POLL_INTERVAL_S}s, table='{cfg.KEITHLEY_TABLE}'")

    try:
        rm, inst = connect_instrument()
    except Exception as e:
        print(f"[KEITHLEY] FATAL: Could not open {cfg.KEITHLEY_PORT} — {e}")
        sys.exit(1)

    try:
        sender = get_sender().__enter__()
    except Exception as e:
        print(f"[KEITHLEY] FATAL: Could not connect to QuestDB — {e}")
        print(f"           Is QuestDB running at {cfg.QUESTDB_HOST}:{cfg.QUESTDB_PORT}?")
        inst.close()
        sys.exit(1)

    print("[KEITHLEY] Connected. Logging... (Ctrl+C to stop)")

    try:
        while _running:
            cycle_start = time.monotonic()
            try:
                readings = read_measurement(inst)
                if readings:
                    sender.row(
                        cfg.KEITHLEY_TABLE,
                        columns=readings,
                        at=TimestampNanos.now(),
                    )
                    sender.flush()
                    summary = ", ".join(f"{k}={v:.6g}" for k, v in readings.items())
                    print(f"[KEITHLEY] {summary}")
                else:
                    print("[KEITHLEY] WARNING: no active measurements parsed this cycle, skipping write")
            except pyvisa.errors.VisaIOError as e:
                print(f"[KEITHLEY] ERROR: instrument communication failed — {e}")
            except Exception as e:
                print(f"[KEITHLEY] ERROR: unexpected error this cycle — {e}")

            elapsed = time.monotonic() - cycle_start
            sleep_time = max(0.0, cfg.POLL_INTERVAL_S - elapsed)
            time.sleep(sleep_time)
    finally:
        print("[KEITHLEY] Cleaning up...")
        try:
            sender.__exit__(None, None, None)
        except Exception:
            pass
        try:
            inst.close()
            rm.close()
        except Exception:
            pass
        print("[KEITHLEY] Stopped.")


if __name__ == "__main__":
    main()
