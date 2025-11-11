import logging
from src.gitremote import GitRemote
from src.gitrepo import GitRepo

class GitSyncHelper:

    KEY_SOURCE="source"
    KEY_KEYFILE="keyfile"
    KEY_EXCLUDED_REFS="excluded-refs"
    KEY_URL="url"
    
    _logger: logging.Logger

    gitrepos: list[GitRepo] = []

    def __init__(self, repos: dict, cache_root_dir: str, keyfile_root: str = None) -> None:
        self._logger = logging.getLogger(__name__)
        self._create_gitrepos_from_config(repos, cache_root_dir, keyfile_root)

    def sync_all(self):
        for repo in self.gitrepos:
            try:
                repo.sync()
            except Exception:
                self._logger.exception("Encountered exception")

    def _create_gitrepos_from_config(self, repos: dict, cache_root_dir: str, keyfile_root: str = None):
        if not isinstance(repos, dict):
            raise AttributeError(f"Repo definition is not a dict. Given value: {repos}")

        for repo_name, repo_definition in repos.items():
            if not isinstance(repo_definition, dict):
                raise AttributeError(f"Remote definition is not a dict. Given value: {repo_definition}")
            
            remotes = []
            for remote_name, remote_definition in repo_definition.items():
                source = False
                keyfile = None
                excluded_refs = None

                if GitSyncHelper.KEY_SOURCE in remote_definition:
                    source = remote_definition.get(GitSyncHelper.KEY_SOURCE)

                if GitSyncHelper.KEY_KEYFILE in remote_definition:
                    keyfile = remote_definition.get(GitSyncHelper.KEY_KEYFILE)
                
                if (GitSyncHelper.KEY_EXCLUDED_REFS in remote_definition) and (isinstance(remote_definition.get(GitSyncHelper.KEY_EXCLUDED_REFS), list)):
                    excluded_refs = remote_definition.get(GitSyncHelper.KEY_EXCLUDED_REFS)

                remotes.append(GitRemote(name=remote_name, remote_url=remote_definition.get(GitSyncHelper.KEY_URL), is_source=source, keyfile=keyfile, excluded_refs=excluded_refs))

            keyfile = None
            if GitSyncHelper.KEY_KEYFILE in repo_definition:
                keyfile = repo_definition.get(GitSyncHelper.KEY_KEYFILE)
    
            repo = GitRepo(repo_name, remotes=remotes, cache_root_dir=cache_root_dir, keyfile=keyfile, keyfile_root=keyfile_root)

            self.gitrepos.append(repo)