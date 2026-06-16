import json
import sys

from loguru import logger


def _json_sink(message) -> None:
    record = message.record
    payload = {
        "timestamp": record["time"].isoformat(),
        "level": record["level"].name,
        "event": record["message"],
        **record["extra"],
    }
    sys.stderr.write(json.dumps(payload, ensure_ascii=True) + "\n")


# Logs go to stderr (not stdout) so they never corrupt machine-readable output
# such as the CLI's JSON result, while still being captured by process managers.
logger.remove()
logger.add(
    _json_sink,
    level="INFO",
)
