from src.gitremote import GitRemote
from src.gitrepo import GitRepo

class GitSyncHelper:
    gitrepos: list[GitRepo] = []

    def __init__(self, repos: dict, cache_root_dir: str, keyfile_root: str = None) -> None:
        self._create_gitrepos_from_config(repos, cache_root_dir, keyfile_root)
        self._setup_all()

    def sync_all(self):
        for repo in self.gitrepos:
            repo.sync()

    def _setup_all(self):
        for repo in self.gitrepos:
            repo.setup()

    def _create_gitrepos_from_config(self, repos: dict, cache_root_dir: str, keyfile_root: str = None):
        if not isinstance(repos, dict):
            raise AttributeError(f"Repo definition is not a dict. Given value: {repos}")

        for name, definition in repos.items():
            if not isinstance(definition, dict):
                raise AttributeError(f"Remote definition is not a dict. Given value: {definition}")
            
            remotes = []
            for repo_name, repo_def in definition.items():
                source = False

                if "source" in repo_def:
                    source = repo_def.get("source")

                remotes.append(GitRemote(name=repo_name, remote_url=repo_def.get("url"), is_source=source))

            keyfile = keyfile_root
            if "keyfile" in definition:
                keyfile = definition.get("keyfile")
    
            repo = GitRepo(name, remotes=remotes, cache_root_dir=cache_root_dir, keyfile=keyfile)

            self.gitrepos.append(repo)