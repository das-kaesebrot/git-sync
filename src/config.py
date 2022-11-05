import logging
import os
import json
import yaml
from crontab import CronTab

class Config:
    ARGS_WITH_VALID_VALS = {
        "run_type": {
            "valid_vals": ["once", "cron"],
            "default": "cron"
        },
        "config_file": {
            "valid_vals": None,
            "default": "/var/opt/gitsync/config.yml"
        },
    }
    
    ENV_PREFIX = "GITSYNC"
    
    ARGS = {}
    FILECONF = {}

    CRON_INTERVAL: CronTab

    def __init__(self) -> None:
        self._get_env_config()
        self._get_file_config()
    
    def _get_env_config(self) -> None:
        for arg, vals in self.ARGS_WITH_VALID_VALS.items():
            envkey = f"{self.ENV_PREFIX}_{arg.upper()}"
            logging.debug(f"Getting environment variable {envkey}")
            val = os.getenv(envkey)

            if vals.get("valid_vals") is not None:
                # validate value
                if val in vals:
                    self.ARGS[arg] = val
            
            # set value, or use fallback
            if val:
                self.ARGS[arg] = val
            else:
                self.ARGS[arg] = vals.get("default")

    def _get_file_config(self) -> None:
        file = self.ARGS.get("config_file")
        if not os.path.isfile(file):
            raise FileNotFoundError(f"Couldn't find config file at {file}")

        with open(file=file, mode='r') as f:

            if file.endswith(('.yaml', '.yml')):
                self.FILECONF = yaml.safe_load(f)
            elif file.endswith('.json'):
                self.FILECONF = json.load(f)
            else:
                raise AttributeError(f"Unsupported file extension for config file: {file}")

        
                
    def print(self) -> str:
        for k, v in self.ARGS.items():
            logging.info(f"{k}={v}")

        logging.info(f"config: {json.dumps(self.FILECONF)}")