import os

class GitRemote:    
    is_source: bool
    remote_url: str
    name: str
    keyfile: str

    def __init__(self, name, remote_url, is_source: bool = False, keyfile: str = None) -> None:
        self.name = name

        self.remote_url = remote_url
        self.is_source = is_source
        
        if keyfile:
            if not os.path.isfile(keyfile):
                raise FileNotFoundError(f"Couldn't find key file at {keyfile}")
            self.keyfile = keyfile
