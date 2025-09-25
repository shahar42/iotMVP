"""
Render Database Deployment Tools
Tools for creating and managing Render PostgreSQL databases.
"""

import asyncio
import aiohttp
import json
from typing import Dict, List, Optional, Any
from fastmcp import FastMCP

# Render API configuration
RENDER_BASE_URL = "https://api.render.com/v1"

async def make_render_request(
    method: str,
    endpoint: str,
    api_key: str,
    data: Optional[Dict] = None
) -> Dict:
    """Make authenticated request to Render API"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json"
    }

    if data:
        headers["Content-Type"] = "application/json"

    url = f"{RENDER_BASE_URL}{endpoint}"

    async with aiohttp.ClientSession() as session:
        async with session.request(
            method=method,
            url=url,
            headers=headers,
            data=json.dumps(data) if data else None
        ) as response:
            response_text = await response.text()

            if not response.ok:
                raise Exception(f"Render API error {response.status}: {response_text}")

            try:
                return json.loads(response_text) if response_text else {}
            except json.JSONDecodeError:
                return {"message": response_text}

def register_db_deployment_tools(mcp: FastMCP):
    """Register database deployment tools with FastMCP server"""

    @mcp.tool()
    async def create_postgresql_database(
        name: str,
        region: str,
        plan: str,
        version: str,
        database_name: str,
        database_user: str,
        owner_id: str,
        api_key: str,
    ) -> str:
        """
        Create a new PostgreSQL database on Render.

        Args:
            name: Human-friendly display name for the Postgres instance.
            region: Region slug for where the database should be provisioned.
            plan: Postgres plan/tier identifier.
            version: Major version to provision (e.g., 15 or 16).
            database_name: The name of the initial database.
            database_user: The name of the initial database user.
            owner_id: The ID of the owner of the database.
            api_key: Render API key.
        """

        payload = {
            "name": name,
            "region": region,
            "plan": plan,
            "version": version,
            "databaseName": database_name,
            "databaseUser": database_user,
            "ownerId": owner_id
        }

        try:
            result = await make_render_request("POST", "/postgres", api_key, payload)
            postgres_id = result.get("id", "unknown")
            status = result.get("status", "creating")

            # Poll for the database to be ready
            while status == "creating":
                await asyncio.sleep(10)
                db_details = await make_render_request("GET", f"/postgres/{postgres_id}", api_key)
                status = db_details.get("status", "creating")

            if status != "available":
                return f"ERROR: Database creation failed with status: {status}"

            connection_info = await make_render_request("GET", f"/postgres/{postgres_id}/connection-info", api_key)
            external_connection_string = connection_info.get("externalConnectionString", "unknown")
            internal_connection_string = connection_info.get("internalConnectionString", "unknown")

            return f"""SUCCESS: PostgreSQL Database Created Successfully!

ID: {postgres_id}
Name: {name}
Status: {status}
Region: {region}
Plan: {plan}
Postgres Version: {version}
Database Name: {database_name}
Database User: {database_user}
External Connection String: {external_connection_string}
Internal Connection String: {internal_connection_string}
"""
        except Exception as e:
            return f"ERROR: Failed to create PostgreSQL database: {str(e)}"
