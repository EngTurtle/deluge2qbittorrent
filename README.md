# deluge2qbittorrent

A Python utility to migrate torrents from Deluge to qBittorrent via their respective APIs.

## Features

- **Remote and Local instance support**: Connects to Deluge and qBittorrent instances via API
- **Renamed Files/Folders Support**: Preserves file and folder renames from Deluge to qBittorrent
- **State Preservation**: Maintains torrent state including:
  - Paused/active status
  - Labels/categories
  - Save paths
  - Progress tracking
  - Renamed files and folders
- **Python-based**: Uses Python client libraries (`deluge-client` and `qbittorrent-api`)

## Prerequisites

- Docker (for Docker-based installation)
- Network access to Deluge and qBittorrent instances

### OR

- Python 3.14+ and [uv](https://github.com/astral-sh/uv) (for local installation)
- Network access to Deluge and qBittorrent instances
- Deluge daemon credentials (host, port, username, password)
- qBittorrent Web UI credentials (host, username, password)
- Access to Deluge state folder (contains `.torrent` files)

## Run Instructions

### Option 1: Docker (Recommended for servers)

1. Clone this repository on your server:

```bash
git clone https://github.com/engturtle/deluge2qbittorrent.git
cd deluge2qbittorrent
```

2. Copy and configure `config.toml`:

```bash
cp config.example.toml config.toml
nano config.toml  # Edit with your settings
```

3. Run the migration:

```bash
docker run --rm \
  -v "$(pwd):/app" \
  -v /path/to/deluge/state:/config/state:ro \
  -w /app \
  -e UV_LINK_MODE=copy \
  ghcr.io/astral-sh/uv:trixie \
  uv run python main.py
```

**Volume mount notes:**
- First `-v` mounts your project directory (contains config.toml and code)
- Second `-v` mounts Deluge state folder:
  - Change `/path/to/deluge` to your Deluge config folder state path, it needs to contain the `state` folder with all of
    Deluge's hash.torrent files. 
  - `:ro` flag mounts read-only for safety

### Option 2: Local Execution

1. Clone this repository:

```bash
git clone https://github.com/engturtle/deluge2qbittorrent.git
cd deluge2qbittorrent
```

2. Install dependencies:

```bash
uv sync
```

3. Copy and configure `config.toml`:

```bash
cp config.example.toml config.toml
# Edit config.toml with your settings
```

4. Run the migration:

```bash
uv run python main.py
```

## Configuration

### config.toml Settings

Edit `config.toml` with your connection details:

```toml
[logging]
log_level = "INFO"  # DEBUG for detailed output

[deluge]
host = "192.168.1.100"
port = 58846
username = "admin"
password = "your_password"
state_path = "/config/state"  # update if running localy

[qbittorrent]
host = "http://192.168.1.100:8080"  # Include protocol
username = "admin"
password = "your_password"

[migration]
test_mode = true                    # Test with one torrent first
test_torrent_name = "test torrent"  # Name of test torrent
auto_delete = false                 # Delete from Deluge after migration
auto_resume = false                 # Resume in qBittorrent after migration
```

### Configuration Notes

- **Deluge port**: Default daemon port is 58846
- **qBittorrent host**: Must include protocol (`http://` or `https://`)
- **state_path**: 
  - Docker: Use container mount point (e.g., `/config/state`)
  - Local: Use actual filesystem path
- **Test mode**: Always test with one torrent first before full migration
- **Network access**: Verify both services are reachable

## Usage

### First Run (Test Mode)

1. Set `test_mode = true` in config.toml
2. Set `test_torrent_name` to a specific torrent
3. Run migration and verify the test torrent migrated correctly
4. Check that files, paths, and progress match

### Full Migration

1. Set `test_mode = false` in config.toml
2. Optionally enable `auto_delete` and `auto_resume`
3. Run migration
4. Monitor output for any warnings or errors

### Troubleshooting

**Debug logging:**
```toml
[logging]
log_level = "DEBUG"
```

**Docker network issues:**
- If containers can't reach Deluge/qBittorrent, try `--network host`
- Verify firewall rules allow connections

**Permission errors:**
- Remove `:ro` from state volume mount
- Check file permissions on state folder

## Important Notes

### Backup First

**Always backup your qBittorrent configuration before running any migration!**

### Torrent State

- The migration preserves labels/categories where possible
- You may need to recheck torrents after migration if file paths differ

## Development

This project uses `uv` for dependency management.

```bash
# Add a new dependency
uv add <package-name>

# Update dependencies
uv sync
```

## Acknowledgments

Inspired by [rumanzo/deluge2qbt](https://github.com/rumanzo/deluge2qbt)
