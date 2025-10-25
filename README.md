# deluge2qbittorrent

A Python utility to migrate torrents from Deluge to qBittorrent via their respective APIs.

## Features

- **Remote and Local instance support**: Connects to Deluge and qBittorrent instances via API
- **State Preservation**: Maintains torrent state including:
  - Paused/active status
  - Labels/categories
  - Save paths
  - Progress tracking
- **Python-based**: Uses Python client libraries (`deluge-client` and `python-qbittorrent`)

## Prerequisites

- Python 3.14 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- Access to remote server running Deluge and qBittorrent Docker containers
- Deluge daemon credentials (host, port, username, password)
- qBittorrent Web UI credentials (host, port, username, password)

## Installation

1. Clone this repository:

```powershell
git clone <repository-url>
cd deluge2qbittorrent
```

2. Install dependencies:

```powershell
uv sync
```

## Configuration

Before running the migration, ensure you have:

1. Network access to both Deluge daemon and qBittorrent Web UI
2. Valid credentials for both services
3. Verified that download file paths are accessible to both torrent clients

## Usage

```powershell
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

```powershell
# Add a new dependency
uv add <package-name>

# Update dependencies
uv sync
```

## Acknowledgments

Inspired by [rumanzo/deluge2qbt](https://github.com/rumanzo/deluge2qbt)
