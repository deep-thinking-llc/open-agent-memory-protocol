"""Run the OAMP reference server.

Usage: python -m oamp_server [--host HOST] [--port PORT] [--db-path PATH]
"""

from __future__ import annotations

import argparse
import uvicorn

from .config import Settings


def main() -> None:
    parser = argparse.ArgumentParser(description="OAMP Reference Backend Server")
    parser.add_argument("--host", default=None, help="Host to bind (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=None, help="Port to bind (default: 8000)")
    parser.add_argument("--db-path", default=None, help="SQLite database path (default: oamp.db)")
    args = parser.parse_args()

    settings = Settings(
        host=args.host or "0.0.0.0",
        port=args.port or 8000,
        db_path=args.db_path or "oamp.db",
    )

    uvicorn.run(
        "oamp_server.main:create_app",
        factory=True,
        host=settings.host,
        port=settings.port,
    )


if __name__ == "__main__":
    main()