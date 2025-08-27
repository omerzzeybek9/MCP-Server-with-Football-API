# Football — TheSportsDB MCP Server

A TheSportsDB-backed MCP (Multi-Client-Plugin) server exposing football data as MCP tools.

## Overview
This project exposes TheSportsDB API through an MCP server implemented in [main.py](main.py). The server registers tools such as team search, player lists and event details that can be consumed by MCP clients.

## Requirements
- Python >= 3.10 (see [.python-version](.python-version))
- Dependencies are declared in [pyproject.toml](pyproject.toml)

## Installation
1. Create and activate a virtual environment:
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate

2. Install the package in editable mode:
   pip install -e .

## Configuration
- Environment variables:
  - THESPORTSDB_API_KEY — TheSportsDB API key (default in config: "123")
  - USER_AGENT — optional User-Agent header value

- The included VS Code MCP launch configuration is [/.vscode/mcp.json](.vscode/mcp.json). It runs:
  uv run main.py

## Running
From repository root:
uv run main.py

The server is started in stdio transport via `mcp.run(transport="stdio")` in [main.py](main.py).

## Available MCP tools (registered in main.py)
- Team search: [`search_teams`](main.py)
- List players: [`list_players`](main.py)
- Upcoming events: [`team_next`](main.py)
- Past events: [`team_last`](main.py)
- List leagues: [`list_leagues`](main.py)
- Full event details (concurrent lookups): [`event_full`](main.py)
- Raw API GET: [`raw_get`](main.py)

Helper functions and internals:
- HTTP helper: [`_get`](main.py)
- URL builder: [`_make_url`](main.py)
- MCP server instance: [`mcp`](main.py)
- MCP server class reference: [`FastMCP`](main.py)

## Example usage
Invoke `search_teams` from an MCP client and pass a team name. See tool signatures in [main.py](main.py).

## Development notes
- The MCP server instance is created as [`mcp`](main.py) using [`FastMCP`](main.py).
- Error responses are normalized and formatted by [`_fmt_err`](main.py).
- Concurrent event details are fetched with `asyncio.gather` inside [`event_full`](main.py).

## Files of interest
- Server code: [main.py](main.py)
- Project metadata: [pyproject.toml](pyproject.toml)
- VSCode MCP runner: [.vscode/mcp.json](.vscode/mcp.json)
- Python version pin: [.python-version](.python-version)
- Git ignore: [.gitignore](.gitignore)
- Lock file: [uv.lock](uv.lock)

## Contributing
Open issues for bugs or feature requests. Pull requests should include tests or a description of manual verification steps.