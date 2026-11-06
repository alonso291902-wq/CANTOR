import argparse
import logging
import sys

from app.server import HTTPServer


def setup_logging(level_name: str = "INFO"):
    level = getattr(logging, level_name.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(threadName)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def main():
    parser = argparse.ArgumentParser(
        description="Build Your Own HTTP Server in Python from scratch."
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host address to bind the server to (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=4221,
        help="Port number to listen on (default: 4221)",
    )
    parser.add_argument(
        "--directory",
        type=str,
        default=None,
        help="Directory to serve and store files from (optional)",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)",
    )

    args = parser.parse_args()
    setup_logging(args.log_level)

    server = HTTPServer(host=args.host, port=args.port, directory=args.directory)
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nShutdown requested by user. Exiting...")
        server.stop()
        sys.exit(0)


if __name__ == "__main__":
    main()
