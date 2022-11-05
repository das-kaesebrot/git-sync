import logging
import os
import random
import stat
import string
import subprocess
from src.gitremote import GitRemote
import shutil
import giturlparse

class GitRepo:
    remotes: list[GitRemote]
    cached_path: str
    primary_remote: GitRemote = None
    secondary_remotes: list[GitRemote] = None
    keyfile: str = None
    name: str = None

    def __init__(self, name, remotes, cache_root_dir, keyfile = None) -> None:
        self.name = name
        self.remotes = remotes

        if keyfile:
            if not os.path.isfile(keyfile):
                raise FileNotFoundError(f"Couldn't find key file at {keyfile}")
            self.keyfile = keyfile

        self.cached_path = os.path.join(cache_root_dir, name)

        self._setup()

    def _setup(self):
        self._add_trusted_host_keys()
        self._create_cached_dir()
        self._initial_clone()
        self._add_secondary_remotes_to_repo()

    def sync(self):
        self._pull_primary_remote()
        self._push_secondary_remotes()

    def _initial_clone(self):
        used_remote = self._get_primary_remote()
        args = f"clone --mirror {used_remote.remote_url} {self.cached_path}"
        self._run_git_command(args, run_in_dir=False)

    def _pull_primary_remote(self):
        # self._fetch_prune_on_primary()
        used_remote = self._get_primary_remote()
        return self._run_git_command(f"remote update --prune origin")

    def _fetch_prune_on_primary(self) -> subprocess.CompletedProcess:        
        used_remote = self._get_primary_remote()
        return self._run_git_command(f"git fetch --prune {used_remote.name}")

    def _push_secondary_remotes(self):
        secondary_remotes = self._get_secondary_remotes()

        for remote in secondary_remotes:
            self._run_git_command(f"push --mirror {remote.name}")

    def _add_secondary_remotes_to_repo(self):
        secondary_remotes = self._get_secondary_remotes()

        for remote in secondary_remotes:
            self._run_git_command(f"remote add --mirror=push {remote.name} {remote.remote_url}")

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

            cmd = "ssh-keyscan"
            giturl = giturlparse.parse(remote.remote_url)

            host = giturl.host
            if giturl.port:
                cmd += f" -p {giturl.port}"

            cmd += f" {host}"

            logging.info(f"Getting host keys for '{remote.remote_url}': '{host}'")
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
        # clean the directory before creating
        if os.path.exists(self.cached_path):
            shutil.rmtree(self.cached_path)
        
        os.makedirs(self.cached_path, exist_ok=False)

    @staticmethod
    def _get_random_string(length: int = 6) -> str:
        return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(length))

    def _run_git_command(self, cmd: str, run_in_dir: bool = True) -> subprocess.CompletedProcess:
        env = os.environ.copy()

        # keyfile override
        if self.keyfile:
            logging.debug(f"Using keyfile '{self.keyfile}'")
            env = {**env, "GIT_SSH_COMMAND": f"ssh -i {self.keyfile} -o IdentitiesOnly=yes"}

        cmd = f"git {cmd}"
        logging.debug(f"Executing command '{cmd}'")

        if run_in_dir:
            logging.debug(f"Running in directory '{self.cached_path}'")
            result = subprocess.run(args=cmd.split(' '), env=env, cwd=self.cached_path, capture_output=True)
        else:
            result = subprocess.run(args=cmd.split(' '), env=env, capture_output=True)

        result.check_returncode()
        return result