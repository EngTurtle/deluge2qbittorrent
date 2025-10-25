# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Torrent migrator from Deluge to qBittorrent. Both applications run in Docker containers on a remote server and are accessed via their respective Python client libraries:
- `deluge-client` for Deluge interaction
- `qbittorrent-api` for qBittorrent interaction

## Development Environment

This project uses `uv` for Python package management and is developed on Windows.

**Python Version:** >=3.14

### Common Commands

```
# Install dependencies
uv sync

# Run the main script
uv run python main.py

# Add a new dependency
uv add <package-name>
```

## Development Preferences

### Code Organization
- **Avoid premature abstraction**: Don't create wrapper classes, models, or abstractions until they're actually needed
- **Keep it simple**: Prefer simple functions over classes when possible
- **Separation of concerns**: Each module should have a single, clear responsibility

### Configuration
- **Use TOML over JSON**: TOML is cleaner and less verbose
- **No file logging**: Log to stdout (INFO/DEBUG) and stderr (WARNING+) only
- **Gitignore sensitive files**: Always exclude `config.toml` and `*.log` files

### Logging
- **Use loguru**: Already configured in `src/logging.py`
- **Keep messages concise**: No extraneous logging messages
- **Appropriate levels**: INFO for operations, WARNING for issues, ERROR for failures
- **No emojis**: Unless explicitly requested

## Code Architecture

### Project Structure

```
deluge2qbittorrent/
├── main.py                      # Entry point - orchestration only
├── config.toml                  # User configuration (gitignored)
├── config.example.toml          # Configuration template
└── src/
    ├── config.py                # Configuration loading & validation
    ├── logging.py               # Logging setup
    └── connections.py           # Connection management with error handling
```

### Module Responsibilities

**`main.py`**: Entry point - minimal orchestration code only

**`src/config.py`**:
- Load and validate TOML configuration
- Provide `Config` class with typed property access
- Exit with helpful errors if config is invalid

**`src/logging.py`**:
- Setup logging (INFO to stdout, WARNING+ to stderr)
- Export configured logger instance

**`src/connections.py`**:
- Connect to Deluge daemon with error handling
- Connect to qBittorrent Web UI with error handling
- Exit program with helpful messages on connection failure

### Key Implementation Details

**Renamed Files/Folders**:
- Deluge stores renamed files in the `mapped_files` field as a dict of {file_index: renamed_path}
- Access via `client.call('core.get_torrents_status', {}, ['mapped_files', ...])`
- Apply renames in qBittorrent using `rename_file()` method on torrent objects from qbittorrent-api

**Connection Management**:
- Each connection function handles its own errors and exits on failure
- Specific exception handling for common errors (ConnectionRefusedError, LoginFailed, APIConnectionError)
- Logs helpful diagnostic messages for troubleshooting

**Error Handling**:
- Use `sys.exit(1)` for fatal errors (missing config, connection failures)
- Provide clear error messages that help users fix the issue
- Catch specific exceptions before generic ones

### Key Considerations
- Connection handling to remote Docker services (host, port, authentication)
- Preserving torrent state during migration (paused/active, labels/categories, save paths, renamed files)
- Handling file path mapping between Deluge and qBittorrent (especially important with Docker volume mounts)
- Error handling for network issues and API failures
