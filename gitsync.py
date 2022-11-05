#!/usr/bin/env python3

import sys
import logging

from src.config import Config

def main():
    logging.basicConfig(format='[%(asctime)s] [%(levelname)s] %(message)s', level=logging.DEBUG)

    config = Config()
    config.print()

if __name__ == "__main__":
    try:
        main()
        
    except (KeyboardInterrupt, InterruptedError) as e:
        print(f"{e=}")
        sys.exit(0)
        
    except Exception as e:
        print(f"Encountered exception: {e=}")
        sys.exit(1)
