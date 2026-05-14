## 1. Compose File

- [x] 1.1 Add `/dev/snd` to the `devices:` list in `docker/compose.prod.yml`

## 2. Install Script

- [x] 2.1 Add `/dev/snd` to the `devices:` list in the embedded compose heredoc inside `scripts/install.sh`

## 3. Documentation

- [x] 3.1 Add a "Required Host Devices" table to `docs/deployment-and-updates.md` listing `/dev/snd`, `/dev/gpiochip0`, `/dev/net/tun` with descriptions
