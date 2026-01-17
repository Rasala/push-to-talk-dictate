"""Entry point for running dictate as a module: python -m dictate"""

import logging
import sys
from pathlib import Path

# Load .env file if it exists (before importing config)
try:
    from dotenv import load_dotenv
    env_path = Path.cwd() / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass  # python-dotenv not installed, use environment variables directly

from dictate.app import DictationApp
from dictate.config import Config


def setup_logging(verbose: bool) -> None:
    """Configure logging based on verbosity setting."""
    # Only show warnings and above unless explicitly verbose
    level = logging.WARNING
    
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    
    # Reduce noise from all third-party libraries
    for name in ("urllib3", "httpx", "mlx", "transformers", "tokenizers", "sounddevice"):
        logging.getLogger(name).setLevel(logging.ERROR)


def main() -> int:
    """Main entry point."""
    # Load configuration (supports environment variables)
    config = Config.from_env()
    
    # Setup logging
    setup_logging(config.verbose)
    
    # Create and run application
    app = DictationApp(config)
    
    try:
        app.run()
        return 0
    except KeyboardInterrupt:
        print("\n👋 Interrupted")
        return 130
    except Exception as e:
        logging.exception("Fatal error: %s", e)
        return 1
    finally:
        app.shutdown()


if __name__ == "__main__":
    sys.exit(main())
