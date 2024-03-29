import logging
import os
import random
import stat
import string
import subprocess
from src.gitremote import GitRemote
import shutil
import re
from re import Match

class GitRepo:
    remotes: list[GitRemote]
    cached_path: str
    primary_remote: GitRemote = None
    secondary_remotes: list[GitRemote] = None
    keyfile: str = None
    keyfile_root: str = None
    name: str = None
    trust_all_host_keys: bool = True

    def __init__(self, name, remotes, cache_root_dir, keyfile = None, keyfile_root = None, trust_all_host_keys = True) -> None:
        self.name = name
        self.remotes = remotes
        self.trust_all_host_keys

        if keyfile:
            if not os.path.isfile(keyfile):
                raise FileNotFoundError(f"Couldn't find key file at {keyfile}")
            self.keyfile = keyfile

        if keyfile_root:
            if not os.path.isfile(keyfile_root):
                raise FileNotFoundError(f"Couldn't find key file at {keyfile_root}")
            self.keyfile_root = keyfile_root

        self.cached_path = os.path.join(cache_root_dir, name)

        self._setup()

    def _setup(self):
        if self.trust_all_host_keys: self._add_trusted_host_keys()
        
        self._create_cached_dir()
        self._initial_clone()
        self._do_fsck()
        self._add_secondary_remotes_to_repo()

    def sync(self):
        logging.info(f"Starting repo sync")
        self._pull_primary_remote()
        self._do_fsck()
        self._push_secondary_remotes()

    def _initial_clone(self):
        used_remote = self._get_primary_remote()
        
        logging.info(f"Setup: Cloning source repo '{used_remote.remote_url}'")
        args = f"clone --mirror {used_remote.remote_url} {self.cached_path}"
        self._run_git_command(args, run_in_dir=False, keyfile=self._get_keyfile(used_remote))

    def _pull_primary_remote(self):
        used_remote = self._get_primary_remote()
        logging.info(f"Pulling remote '{used_remote.name}' ({used_remote.remote_url})")
        return self._run_git_command(f"remote update --prune origin", keyfile=self._get_keyfile(used_remote))
    
    def _do_fsck(self):
        return self._run_git_command(f"fsck")

    def _fetch_prune_on_primary(self) -> subprocess.CompletedProcess:        
        used_remote = self._get_primary_remote()
        return self._run_git_command(f"fetch --prune {used_remote.name}", keyfile=self._get_keyfile(used_remote))

    def _push_secondary_remotes(self):
        secondary_remotes = self._get_secondary_remotes()

        for remote in secondary_remotes:
            logging.info(f"Pushing to remote '{remote.name}' ({remote.remote_url})")
            self._run_git_command(f"push --mirror {remote.name}", keyfile=self._get_keyfile(remote))

    def _add_secondary_remotes_to_repo(self):
        secondary_remotes = self._get_secondary_remotes()

        for remote in secondary_remotes:
            logging.info(f"Adding push remote '{remote.name}' ({remote.remote_url})")
            self._run_git_command(f"remote add --mirror=push {remote.name} {remote.remote_url}", keyfile=self._get_keyfile(remote))

    def _get_primary_remote(self) -> GitRemote:
        if not self.primary_remote:
            for remote in self.remotes:
                if remote.is_source:
                    self.primary_remote = remote
                    break

        return self.primary_remote

    def _get_secondary_remotes(self) -> list[GitRemote]:
        if not self.secondary_remotes:
            self.secondary_remotes = []
            for remote in self.remotes:
                if not remote.is_source:
                    self.secondary_remotes.append(remote)

        return self.secondary_remotes

    def _add_trusted_host_keys(self):
        trusted_keys = ""
        for remote in self.remotes:
            
            giturl_match: Match = re.match(r"(\w+:\/\/)?(.+@)*([\w\d\.]+)(:[\d]+){0,1}\/*(.*)", remote.remote_url)
            
            if not giturl_match:
                raise ValueError(f"Remote URL '{remote.remote_url}' is not a valid git URL")
            
            logging.debug(f"Regex match result: {giturl_match.groups()}")
            
            if giturl_match.group(1) and giturl_match.group(1) != "ssh://":
                logging.info(f"Skipping remote '{remote.remote_url}' as it's not a ssh URL")
                continue

            host = giturl_match.group(3)
            port = giturl_match.group(4)[1:] if giturl_match.group(4) else 22
            
            # catch false positives for ports
            if port > 65535 or port < 0:
                port = 22
            
            cmd = f"ssh-keyscan -p {port} {host}"

            logging.info(f"Getting host keys for '{remote.remote_url}' host: '{host}:{port}'")
            result = subprocess.run(cmd.split(' '), capture_output=True)
            result.check_returncode()
            trusted_keys += result.stdout.decode()

        dirpath = "/home/gitsync/.ssh"
        path = os.path.join(dirpath, "known_hosts")

        logging.debug(f"Trusted keys: \n{trusted_keys}")

        if not os.path.exists(dirpath):
            os.mkdir(path=dirpath, mode=stat.S_IRWXU)

        with open(path, 'a') as f:
            f.write(trusted_keys)

        uniquelines = None
        with open(path) as f:
            uniquelines = set(f.readlines())

        with open(path, 'w') as f:
            f.writelines(uniquelines)

        os.chmod(path, stat.S_IWUSR | stat.S_IRUSR)

    def _create_cached_dir(self):
        
        logging.info(f"Setting up cache directory for repo '{self.name}': '{self.cached_path}'")

        # clean the directory before creating
        if os.path.exists(self.cached_path):
            shutil.rmtree(self.cached_path)
        
        os.makedirs(self.cached_path, exist_ok=False)

    @staticmethod
    def _get_random_string(length: int = 6) -> str:
        return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(length))

    def _get_keyfile(self, remote: GitRemote) -> str:
        # remote keyfile takes precedence
        if remote.keyfile:
            return remote.keyfile
        
        # next up, the repo keyfile
        if self.keyfile:
            return self.keyfile
        
        # finally as a last ditch effort, the root keyfile
        return self.keyfile_root

    def _run_git_command(self, cmd: str, keyfile: str = None, run_in_dir: bool = True) -> subprocess.CompletedProcess:
        env = os.environ.copy()

        # keyfile override
        if keyfile:
            logging.debug(f"Using keyfile '{keyfile}'")
            env = {**env, "GIT_SSH_COMMAND": f"ssh -i {keyfile} -o IdentitiesOnly=yes"}

        cmd = f"git {cmd}"
        logging.debug(f"Executing command '{cmd}'")

        if run_in_dir:
            logging.debug(f"Running in directory '{self.cached_path}'")
            result = subprocess.run(args=cmd.split(' '), env=env, cwd=self.cached_path, capture_output=True)
        else:
            result = subprocess.run(args=cmd.split(' '), env=env, capture_output=True)

        result.check_returncode()
        return result
    