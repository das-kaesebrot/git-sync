#!/usr/bin/env python3

from subprocess import CalledProcessError
import sys
import logging
import time
import os

from src.config import Config
from src.gitsynchelper import GitSyncHelper

def main():
    logging.basicConfig(format='[%(asctime)s] [%(levelname)s] %(message)s', level=logging.DEBUG)
    logging.warning("NOT PRODUCTION READY - USE WITH CAUTION")
    logging.debug(f"Running as UID {os.getuid()}")

    config = Config()
    config.print()

    helper = GitSyncHelper(config.FILECONF.get("repos"), config.cache_root_dir, config.keyfile)
    cron = config.cron_interval_parsed

    if config.run_cron:
        logging.debug(f"Running in cron mode with cron interval '{config.cron_interval}'")
        while True:
            helper.sync_all()
            sleeptime = cron.next(default_utc=True)
            next_run_date = cron.next(default_utc=True, return_datetime=True)
            logging.info(f"Sleeping for {sleeptime}s until next cron job run")
            logging.info(f"Next run at {next_run_date.astimezone().isoformat()}")
            time.sleep(sleeptime)

    else:
        logging.debug(f"Running once")
        helper.sync_all()

if __name__ == "__main__":
    try:
        main()
        
    except (KeyboardInterrupt, InterruptedError) as e:
        print(f"{e=}")
        sys.exit(0)

    except CalledProcessError as e:
        logging.exception(f"Encountered exception: {e=}, {e.stdout=}, {e.stderr=}")
        sys.exit(1)
        
    except Exception as e:
        logging.exception(f"Encountered exception: {e=}")
        sys.exit(1)

    finally:
        print("Shutting down")