"""Main entry point for the Code Combiner application."""

import logging
from src.code_combiner import parse_arguments, run_code_combiner
from src.config_builder import load_and_merge_config

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    args = parse_arguments()
    config = load_and_merge_config(args)
    run_code_combiner(config)
