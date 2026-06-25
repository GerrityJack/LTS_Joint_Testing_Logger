"""
questdb_client.py
─────────────────────────────────────────────────────────────────────────────
Creates a configured QuestDB Sender. Imported by both logger scripts.

Uses the ILP (InfluxDB Line Protocol) interface over HTTP, which is the
fastest ingestion path for time-series writes into QuestDB.
"""

from questdb.ingress import Sender
import lab_config as cfg


def get_sender() -> Sender:
    """
    Returns a Sender instance pointed at the QuestDB server in lab_config.
    Use as a context manager:
        with get_sender() as sender:
            sender.row(...)
            sender.flush()
    """
    conf = f"http::addr={cfg.QUESTDB_HOST}:{cfg.QUESTDB_PORT};"
    return Sender.from_conf(conf)
