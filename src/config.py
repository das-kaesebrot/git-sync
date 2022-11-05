import logging
import os
import json
import yaml
from crontab import CronTab

class Config:
    REQUIRED_ARGS = [        
        "keyfile"
    ]

    OPTIONAL_ARGS = [
        "cron_interval",
        "run_type",
        "cache_root_dir",
        "config_file"
    ]

    ENV_PREFIX = "GITSYNC"
    
    ARGS = {}
    FILECONF = None

    cron_interval: str = None
    keyfile: str = None
    run_type: str = "once"
    cache_root_dir: str = "/var/opt/gitsync/cache"
    config_file: str = "/var/opt/gitsync/config/config.yml"

    run_cron: bool
    cron_interval_parsed: CronTab

    def __init__(self) -> None:
        self._get_config()

    def _get_config(self):
        for arg in self.REQUIRED_ARGS + self.OPTIONAL_ARGS:
            envkey = f"{self.ENV_PREFIX}_{arg.upper()}"
            logging.debug(f"Getting environment variable {envkey}")
            val = os.getenv(envkey)
            if not val:
                val = self._get_key_from_conf_file(arg)
            
            if val:
                self.__setattr__(arg, val.strip('\"'))
            
            logging.debug(f"Set value of '{arg}' to '{self.__getattribute__(arg)}'")
        
        for arg in self.REQUIRED_ARGS:
            missing_settings = []
            if not self.__getattribute__(arg):
                missing_settings.append(arg)
            
            if len(missing_settings) > 0:
                raise AttributeError(f"Missing required config setting(s): '{missing_settings}'")

        if self.cron_interval:
            self.cron_interval_parsed = CronTab(self.cron_interval)
        
        if self.run_type == "cron":
            self.run_cron = True
        else:
            self.run_cron = False

    def _get_key_from_conf_file(self, key):
        if not self.FILECONF:            
            file = self.config_file
            if not os.path.isfile(file):
                raise FileNotFoundError(f"Couldn't find config file at {file}")

            with open(file=file, mode='r') as f:
                if file.endswith(('.yaml', '.yml')):
                    self.FILECONF = yaml.safe_load(f)
                elif file.endswith('.json'):
                    self.FILECONF = json.load(f)
                else:
                    raise AttributeError(f"Unsupported file extension for config file: {file}")

        if key in self.FILECONF:
            return self.FILECONF.get(key)
        else: return None
                
    def print(self) -> str:
        for k, v in self.ARGS.items():
            logging.info(f"{k}={v}")

        logging.info(f"config file: {json.dumps(self.FILECONF, indent=4)}")