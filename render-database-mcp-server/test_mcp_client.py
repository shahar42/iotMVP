#!/usr/bin/env python3
"""
MCP Client to test the render MCP server
Connects to the server and tests all available tools
"""

import asyncio
import json
import subprocess
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_mcp_server():
    """Test MCP server by connecting as a client"""

    # Server parameters - connect to our running server
    server_params = StdioServerParameters(
        command="python",
        args=["render_mcp_server.py"],
        env={
            "RENDER_API_KEY": "rnd_j6WyOXSMG0bGFbqyYKMBaxUgzF4s",
            "SERVICE_ID": "srv-d2chm8mr433s73anlc0g",
            "OWNER_ID": "tea-ctl9m2rv2p9s738eghng",
            "BACKGROUND_SERVICE_ID": "srv-d2f1fh0dl3ps73e363g0"
        }
    )

    print("🚀 Starting MCP Client Test")
    print("=" * 60)

    try:
        # Connect to the MCP server
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                print("✅ Connected to MCP server successfully!")

                # Initialize the session
                await session.initialize()
                print("✅ Session initialized")

                # List available tools
                tools_result = await session.list_tools()
                print(f"\n📋 Available Tools ({len(tools_result.tools)} found):")
                print("-" * 40)

                for tool in tools_result.tools:
                    print(f"🔧 {tool.name}")
                    if tool.description:
                        print(f"   📝 {tool.description[:100]}...")
                    print()

                # Test 1: Scaffolding Tool
                print("\n🏗️  TEST 1: Project Scaffolding")
                print("-" * 40)

                try:
                    scaffold_result = await session.call_tool(
                        "scaffold_project",
                        arguments={
                            "project_name": "test-task-manager",
                            "project_type": "node"
                        }
                    )
                    print("✅ Scaffold tool result:")
                    for content in scaffold_result.content:
                        if hasattr(content, 'text'):
                            print(f"   {content.text}")
                except Exception as e:
                    print(f"❌ Scaffold tool error: {e}")

                # Test 2: Database Tool
                print("\n🗄️  TEST 2: Database Operations")
                print("-" * 40)

                try:
                    # Test database connection
                    db_test_result = await session.call_tool(
                        "test_database_connection",
                        arguments={
                            "db_connection_string": "/tmp/claude/test_app.db"
                        }
                    )
                    print("✅ Database connection test:")
                    for content in db_test_result.content:
                        if hasattr(content, 'text'):
                            print(f"   {content.text}")

                    # Create a table
                    table_result = await session.call_tool(
                        "create_database_table",
                        arguments={
                            "db_connection_string": "/tmp/claude/test_app.db",
                            "table_name": "tasks",
                            "columns": json.dumps([
                                {"name": "id", "type": "INTEGER", "options": "PRIMARY KEY AUTOINCREMENT"},
                                {"name": "title", "type": "TEXT", "options": "NOT NULL"},
                                {"name": "completed", "type": "BOOLEAN", "options": "DEFAULT 0"}
                            ])
                        }
                    )
                    print("✅ Table creation result:")
                    for content in table_result.content:
                        if hasattr(content, 'text'):
                            print(f"   {content.text[:200]}...")

                except Exception as e:
                    print(f"❌ Database tool error: {e}")

                # Test 3: Render Service Status
                print("\n☁️  TEST 3: Render Service Tools")
                print("-" * 40)

                try:
                    status_result = await session.call_tool("render_service_status")
                    print("✅ Render service status:")
                    for content in status_result.content:
                        if hasattr(content, 'text'):
                            print(f"   {content.text[:300]}...")
                except Exception as e:
                    print(f"❌ Render status error: {e}")

                # Test 4: List Services
                try:
                    services_result = await session.call_tool("render_list_all_services")
                    print("✅ Render services list:")
                    for content in services_result.content:
                        if hasattr(content, 'text'):
                            print(f"   {content.text[:300]}...")
                except Exception as e:
                    print(f"❌ Services list error: {e}")

                print("\n🎉 MCP Server Test Completed!")
                print("=" * 60)

    except Exception as e:
        print(f"❌ MCP Client Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_mcp_server())