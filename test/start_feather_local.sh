#!/bin/bash
# Local Feather MCP Server Startup Script for test directory
# Wrapper that changes to parent directory before starting the server

# Change to the parent directory where the server files are located
cd "$(dirname "$0")/.."

# Run the original startup script
exec ./start_feather.sh