"""Main entry point for the Code Combiner application."""

import logging
import sys
from src.code_combiner import parse_arguments, run_code_combiner
from src.config_builder import load_and_merge_config
from src.config import CodeCombinerError

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    try:
        args = parse_arguments()
        config = load_and_merge_config(args)
        run_code_combiner(config)
    except CodeCombinerError as e:
        logging.error(str(e))
        sys.exit(1)
    except KeyboardInterrupt:
        logging.info("\nOperation cancelled by user.")
        sys.exit(130)
