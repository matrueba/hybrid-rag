import asyncio
import argparse
import logging
from dotenv import load_dotenv
from settings import load_settings
from cli import run_cli_mode

load_dotenv(override=True)

logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Hybrid RAG — CLI & API")
    parser.add_argument("--cli", action="store_true", help="Start the CLI instead of the FastAPI server.")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="API host (default: 0.0.0.0).")
    parser.add_argument("--port", type=int, default=8000, help="API port (default: 8000).")
    parser.add_argument("--session", type=str, default="default", help="Session ID for conversation persistence.")
    args = parser.parse_args()

    if args.cli:
        settings = load_settings()
        asyncio.run(run_cli_mode(settings, args.session))
    else:
        import uvicorn
        from api.app import create_app
        app = create_app()
        logger.info("Starting API server on %s:%s", args.host, args.port)
        uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
