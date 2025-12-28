# AGENTS.md

## Project Overview

This is an MCP (Model Context Protocol) server that provides AI assistants with search and content retrieval capabilities for Igloo digital workplace instances.

MCP is a standardized protocol that allows AI models to interact with external data sources and tools through a consistent interface.

The server exposes two tools to MCP clients:
- `search` - Search Igloo content with filters (applications, dates, parent paths)
- `fetch` - Retrieve pages and convert HTML to Markdown for LLM consumption

For installation, configuration, and usage details, see [README.md](README.md).

## Project Development Requirements

- Python 3.12+ required
- uv (package manager)

## Development Commands

- `uv sync` - Install dependencies and create `.venv/`
- `uv run pytest` - Run all tests
- `igloo-mcp` - Run the MCP server (after `uv sync`)

## Entry Points

- [`igloo_mcp/main.py`](igloo_mcp/main.py) - FastMCP server setup, tool definitions
- [`igloo_mcp/igloo.py`](igloo_mcp/igloo.py) - `IglooClient` class for Igloo API communication
- [`igloo_mcp/config.py`](igloo_mcp/config.py) - Pydantic configuration with environment/CLI support

## Testing

- Mock data files are in `tests/tests_data/mock_data/`
- Use `mocker.patch.object()` with `new_callable=mocker.AsyncMock` for async HTTP mocking
- Run `uv run pytest` before committing - all tests must pass
