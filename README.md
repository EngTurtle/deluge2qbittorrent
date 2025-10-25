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

- Python 3.14 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- Access to remote server running Deluge and qBittorrent Docker containers
- Deluge daemon credentials (host, port, username, password)
- qBittorrent Web UI credentials (host, port, username, password)

## Installation

1. Clone this repository:

```bash
git clone <repository-url>
cd deluge2qbittorrent
```

2. Install dependencies:

```bash
uv sync
```

## Configuration

### Create config.toml

1. Copy the example configuration file to `config.toml`

2. Edit `config.toml` with your credentials for Deluge RPC and qBittorrent web UI.

### Configuration Notes

- **Deluge port**: The default Deluge daemon port is 58846
- **qBittorrent host**: Must include the protocol (`http://` or `https://`) and port
- **File paths**: Ensure file paths are accessible to both torrent clients (especially important with Docker volumes)
- **Network access**: Verify both services are reachable from your machine

## Usage

```bash
uv run python main.py
```

## Important Notes

### Backup First

**Always backup your qBittorrent configuration before running any migration!**

### Torrent State

- Paused torrents will be added as paused in qBittorrent
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
