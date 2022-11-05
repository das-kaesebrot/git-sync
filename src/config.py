import logging
import os
import json
import yaml
from crontab import CronTab

class Config:
    ARGS_WITH_VALID_VALS = {
        "run_type": {
            "valid_vals": ["once", "cron"],
            "default": "once"
        },
        "cron_interval": {
            "valid_vals": None,
            "default": None
        },
        "cache_root_dir": {
            "valid_vals": None,
            "default": None
        },
        "config_file": {
            "valid_vals": None,
            "default": "/var/opt/gitsync/config/config.yml"
        },
        "keyfile": {
            "valid_vals": None,
            "default": None
        },
    }
    
    ENV_PREFIX = "GITSYNC"
    
    ARGS = {}
    FILECONF = {}

    CRON_INTERVAL: CronTab

    keyfile_root: str = None
    run_cron: bool
    cache_root_dir: str = "/var/opt/gitsync/cache"

    def __init__(self) -> None:
        # fix: evaluate file config first to give precedence to environment variables
        self._get_file_config()
        self._get_env_config()
    
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

        cron_interval = self.ARGS.get("cron_interval")
        if cron_interval:
            self.CRON_INTERVAL = CronTab(self.ARGS.get("cron_interval"))

        run_type = self.ARGS.get("run_type")
        if run_type == "cron":
            self.run_cron = True
        else:
            self.run_cron = False
        
        keyfile = self.ARGS.get("keyfile")
        if keyfile:
            self.keyfile_root = keyfile

        cache_root_dir = self.ARGS.get("cache_root_dir")
        if cache_root_dir:
            self.cache_root_dir = cache_root_dir

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

        conf = self.FILECONF.get("config")

        if "run_type" in conf:
            run_type = conf.get("run_type")
            if run_type == "cron":
                self.run_cron = True
            else:
                self.run_cron = False

        if "cron_interval" in conf:
            self.CRON_INTERVAL = CronTab(conf.get("cron_interval"))
        
        if "keyfile" in conf:
            self.keyfile_root = conf.get("keyfile")
        
        if "cache_root_dir" in conf:
            self.cache_root_dir = conf.get("cache_root_dir")
                
    def print(self) -> str:
        for k, v in self.ARGS.items():
            logging.info(f"{k}={v}")

        logging.info(f"config: {json.dumps(self.FILECONF)}")