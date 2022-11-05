class GitRemote:    
    is_source: bool
    remote_url: str
    name: str

    def __init__(self, name, remote_url, is_source: bool = False) -> None:
        self.name = name

        self.remote_url = remote_url
        self.is_source = is_source