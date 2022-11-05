class GitRepo:
    remote_paths: dict
    cached_path: str

    def __init__(self, remote_paths, cached_path) -> None:
        self.remote_paths = remote_paths
        self.cached_path = cached_path
        