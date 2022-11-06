# git-sync

This docker image allows you to synchronize a single source repository with one or more target repositories. It supports a cron-style run type as well as a single run.

## Pulling the image
Docker hub: https://hub.docker.com/r/daskaesebrot/git-sync
```bash
docker pull daskaesebrot/git-sync
```

## Configuration
The image can be partly configured using environment variables, but the main configuration has to be defined in the yaml- or json-based configuration file.

### Supported environment variables
Environment variables always take precedence over variables from the config file!

- `GITSYNC_RUN_TYPE`: Can be either `once` or `cron`. Defaults to `once`.
- `GITSYNC_CRON_INTERVAL`: Cron interval. Defaults to an empty value.
- `GITSYNC_KEYFILE`: Path to a keyfile to be used as the root file, unless it's overriden in a repository config. Defaults to an empty value.
- `GITSYNC_CACHE_ROOT_DIR`: Directory inside the container to use for caching repositories. Defaults to `/var/opt/gitsync/cache`
- `GITSYNC_CONFIG_FILE`: Config file to use when starting the image. Defaults to `/var/opt/gitsync/config/config.yml`

### Configuration file

For each entry in `repos`, you may give a simple human-readable name.
After that define your remotes, also using a human-readable name with the required key `url`. Only SSH-based Git URLs are supported for now. To define a source to be replicated across all other remotes for repository, add the key/value-pair `source: true`. If the source key is not defined for a remote, it will default to `false`.

#### YAML-based
```yml
# section can be omitted if environment variables are given instead
config:  
  # supported values: cron | once
  run_type: cron
  
  # ignored when run_type = once
  # allows you to define a cron-based interval
  cron_interval: "0 5 * * *"

  # container path to the ssh keyfile to use when pulling/pushing a remote
  keyfile: "/var/opt/gitsync/keys/id_rsa"

  # cache directory for synced repositories
  cache_root_dir: "/var/opt/gitsync/cache"

repos:
  my_repo_1:
    # optional keyfile override for repositories. If this key isn't defined, config.keyfile will be used.
    keyfile: "/var/opt/gitsync/keys/id_rsa"
    github:
      url: "git@github.com:torvalds/linux"
      # repos.[repo].[remote].source defaults to false if omitted, all other remotes are treated as sync targets
      # only a single source can be defined
      source: true
    gitlab: 
      url: "ssh://git@gitlab.example.com:54321/torvalds/linux.git"
```

#### JSON-based
```json
{
    "config": {
        "run_type": "cron",
        "cron_interval": "0 5 * * *",
        "keyfile": "/var/opt/gitsync/keys/id_rsa"
    },
    "repos": {
        "my_repo_1": {
            "github": {
                "url": "git@github.com:torvalds/linux",
                "source": true
            },
            "gitlab": {
                "url": "ssh://git@gitlab.example.com:54321/torvalds/linux.git"
            }
        }
    }
}
```

### Running the image

Either by using `docker run` directly:
```bash
docker run \
    -v /path/to/your/config/config.yml:/var/opt/gitsync/config/config.yml:ro \
    -v /path/to/your/keyfile/git_key_ed25519:/var/opt/gitsync/keys/git_key_ed25519:ro \
    -v myvolume:/var/opt/gitsync/cache \
    -e GITSYNC_KEYFILE="/var/opt/gitsync/keys/git_key_ed25519" \
    -e GITSYNC_RUN_TYPE="cron" \
    -e GITSYNC_CRON_INTERVAL="0 5 * * *" \
    daskaesebrot/git-sync
```

...or using a `docker-compose.yml`:
```yaml
version: '2'

services:
  gitsync:
    image: daskaesebrot/git-sync
    restart: always
    volumes:
      - /path/to/your/config/config.yml:/var/opt/gitsync/config/config.yml:ro
      - /path/to/your/keyfile/git_key_ed25519:/var/opt/gitsync/keys/git_key_ed25519:ro
      - myvolume:/var/opt/gitsync/cache
    environment:
      - GITSYNC_KEYFILE="/var/opt/gitsync/keys/git_key_ed25519"
      - GITSYNC_RUN_TYPE="cron"
      - GITSYNC_CRON_INTERVAL="0 5 * * *"

volumes:
  myvolume:
```