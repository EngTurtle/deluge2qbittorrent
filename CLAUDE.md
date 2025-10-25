# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Torrent migrator from Deluge to qBittorrent. Both applications run in Docker containers on a remote server and are accessed via their respective Python client libraries:
- `deluge-client` for Deluge interaction
- `python-qbittorrent` for qBittorrent interaction

## Development Environment

This project uses `uv` for Python package management and is developed on Windows using PowerShell.

**Python Version:** >=3.14

### Common Commands

```powershell
# Install dependencies
uv sync

# Run the main script
uv run python main.py

# Add a new dependency
uv add <package-name>
```

## Architecture Notes

### Remote Docker Context
Both Deluge and qBittorrent are running in Docker containers on a remote server. The migration tool operates by:
1. Connecting to the remote Deluge instance via `deluge-client`
2. Extracting torrent metadata and state
3. Adding torrents to the remote qBittorrent instance via `python-qbittorrent`

### Key Considerations
- Connection handling to remote Docker services (host, port, authentication)
- Preserving torrent state during migration (paused/active, labels/categories, save paths)
- Handling file path mapping between Deluge and qBittorrent (especially important with Docker volume mounts)
- Error handling for network issues and API failures
