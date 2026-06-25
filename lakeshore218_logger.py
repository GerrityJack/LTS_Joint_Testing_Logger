"""
lakeshore218_logger.py
─────────────────────────────────────────────────────────────────────────────
Polls a LakeShore Model 218 Temperature Monitor over RS232 (via USB-serial
adapter) using PyVISA, and writes Kelvin readings for all 8 input channels
to QuestDB every lab_config.POLL_INTERVAL_S seconds.

Run standalone:
    python lakeshore218_logger.py

Dependencies:
    pip install pyvisa pyvisa-py pyserial questdb

To run, edit lab_config.py:
    LAKESHORE_PORT  -> the COM port assigned to the adapter (Device Manager)
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

_running = True


def _handle_shutdown(signum, frame):
    global _running
    print("\n[LAKESHORE] Shutdown signal received, finishing current cycle...")
    _running = False


signal.signal(signal.SIGINT, _handle_shutdown)
signal.signal(signal.SIGTERM, _handle_shutdown)


def connect_instrument():
    """Open the LakeShore 218 over RS232 via PyVISA."""
    rm = pyvisa.ResourceManager("@py")  # pyvisa-py backend, no NI-VISA needed
    resource_name = f"ASRL{cfg.LAKESHORE_PORT.replace('COM', '')}::INSTR"
    inst = rm.open_resource(resource_name)
    inst.baud_rate = cfg.LAKESHORE_BAUD
    inst.data_bits = cfg.LAKESHORE_DATA_BITS
    inst.parity = _PARITY_MAP[cfg.LAKESHORE_PARITY]
    inst.stop_bits = _STOPBITS_MAP[cfg.LAKESHORE_STOP_BITS]
    inst.write_termination = "\r\n"
    inst.read_termination = "\r\n"
    inst.timeout = cfg.LAKESHORE_TIMEOUT_MS
    return rm, inst


def read_all_channels(inst) -> dict:
    """
    Queries KRDG? 0, which returns all 8 input readings (Kelvin) in one
    comma-separated response. Returns a dict like {"ch1": 4.21, ..., "ch8": ...}.
    """
    response = inst.query("KRDG? 0").strip()
    values = [v.strip() for v in response.split(",")]

    readings = {}
    for i, raw in enumerate(values[: cfg.LAKESHORE_NUM_CHANNELS], start=1):
        try:
            readings[f"ch{i}"] = float(raw)
        except ValueError:
            print(f"[LAKESHORE] WARNING: could not parse channel {i} value: '{raw}'")
    return readings


def main():
    print(f"[LAKESHORE] Starting — port={cfg.LAKESHORE_PORT}, "
          f"interval={cfg.POLL_INTERVAL_S}s, table='{cfg.LAKESHORE_TABLE}'")

    try:
        rm, inst = connect_instrument()
    except Exception as e:
        print(f"[LAKESHORE] FATAL: Could not open {cfg.LAKESHORE_PORT} — {e}")
        sys.exit(1)

    try:
        sender = get_sender().__enter__()
    except Exception as e:
        print(f"[LAKESHORE] FATAL: Could not connect to QuestDB — {e}")
        print(f"            Is QuestDB running at {cfg.QUESTDB_HOST}:{cfg.QUESTDB_PORT}?")
        inst.close()
        sys.exit(1)

    print("[LAKESHORE] Connected. Logging... (Ctrl+C to stop)")

    try:
        while _running:
            cycle_start = time.monotonic()
            try:
                readings = read_all_channels(inst)
                if readings:
                    sender.row(
                        cfg.LAKESHORE_TABLE,
                        columns=readings,
                        at=TimestampNanos.now(),
                    )
                    sender.flush()
                    summary = ", ".join(f"{k}={v:.3f}K" for k, v in readings.items())
                    print(f"[LAKESHORE] {summary}")
                else:
                    print("[LAKESHORE] WARNING: no readings parsed this cycle, skipping write")
            except pyvisa.errors.VisaIOError as e:
                print(f"[LAKESHORE] ERROR: instrument communication failed — {e}")
            except Exception as e:
                print(f"[LAKESHORE] ERROR: unexpected error this cycle — {e}")

            elapsed = time.monotonic() - cycle_start
            sleep_time = max(0.0, cfg.POLL_INTERVAL_S - elapsed)
            time.sleep(sleep_time)
    finally:
        print("[LAKESHORE] Cleaning up...")
        try:
            sender.__exit__(None, None, None)
        except Exception:
            pass
        try:
            inst.close()
            rm.close()
        except Exception:
            pass
        print("[LAKESHORE] Stopped.")


if __name__ == "__main__":
    main()
