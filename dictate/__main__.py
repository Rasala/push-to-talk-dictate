"""Entry point for running dictate as a module: python -m dictate"""

import logging
import sys

from dictate.app import DictationApp
from dictate.config import Config


def setup_logging(verbose: bool) -> None:
    """Configure logging based on verbosity setting."""
    level = logging.INFO if verbose else logging.WARNING
    
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    
    # Reduce noise from third-party libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


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
