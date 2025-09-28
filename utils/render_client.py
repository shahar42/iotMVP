#!/usr/bin/env python3
"""
Render API Client - Shared Utility

Handles all Render API interactions with proven curl commands.
Uses OWNER_ID from environment variables - NO hardcoded values.
"""

import os
import json
import asyncio
import subprocess
import tempfile
from typing import Dict, Any, Optional


class RenderClient:
    """Centralized Render API client with proven curl commands"""

    def __init__(self):
        self.api_key = os.getenv('RENDER_API_KEY')
        self.owner_id = os.getenv('OWNER_ID')
        self.base_url = "https://api.render.com/v1"

        if not self.api_key:
            raise ValueError("RENDER_API_KEY environment variable required")
        if not self.owner_id:
            raise ValueError("OWNER_ID environment variable required")

    async def get_services(self) -> list:
        """Get all services using proven curl command"""
        cmd = [
            'curl', '-H', f'Authorization: Bearer {self.api_key}',
            '-H', 'Accept: application/json',
            f'{self.base_url}/services'
        ]
        return await self._execute_curl(cmd)

    async def get_postgres_databases(self) -> list:
        """Get all PostgreSQL databases"""
        cmd = [
            'curl', '-H', f'Authorization: Bearer {self.api_key}',
            '-H', 'Accept: application/json',
            f'{self.base_url}/postgres'
        ]
        return await self._execute_curl(cmd)

    async def get_service(self, service_id: str) -> Dict[str, Any]:
        """Get specific service details"""
        cmd = [
            'curl', '-H', f'Authorization: Bearer {self.api_key}',
            '-H', 'Accept: application/json',
            f'{self.base_url}/services/{service_id}'
        ]
        return await self._execute_curl(cmd)

    async def create_database(self, name: str) -> Dict[str, Any]:
        """Create PostgreSQL database with OWNER_ID from environment"""
        payload = {
            "name": f"{name}-db",
            "region": "oregon",
            "plan": "free",
            "version": "16",
            "databaseName": f"{name.replace('-', '_')}_db",
            "databaseUser": f"{name.replace('-', '_')}_user",
            "ownerId": self.owner_id  # FROM ENVIRONMENT
        }
        return await self._post_with_payload(f'{self.base_url}/postgres', payload)

    async def get_database_connection(self, database_id: str) -> Dict[str, Any]:
        """Get database connection info"""
        cmd = [
            'curl', '-H', f'Authorization: Bearer {self.api_key}',
            f'{self.base_url}/postgres/{database_id}/connection-info'
        ]
        return await self._execute_curl(cmd)

    async def create_service(self, name: str, repo_url: str, database_url: str) -> Dict[str, Any]:
        """Create web service with OWNER_ID from environment"""
        payload = {
            "ownerId": self.owner_id,  # FROM ENVIRONMENT
            "type": "web_service",
            "name": name,
            "repo": repo_url,
            "serviceDetails": {
                "runtime": "python",
                "envSpecificDetails": {
                    "buildCommand": "cd test && pip install -r requirements.txt",
                    "startCommand": "cd test && gunicorn app:app"
                }
            },
            "envVars": [
                {"key": "DATABASE_URL", "value": database_url},
                {"key": "SECRET_KEY", "value": "your-secret-key-here"},
                {"key": "FLASK_ENV", "value": "production"}
            ]
        }

        # Use proven curl command with correct headers
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            json.dump(payload, temp_file)
            temp_file_path = temp_file.name

        try:
            cmd = [
                'curl', '-X', 'POST',
                '-H', f'Authorization: Bearer {self.api_key}',
                '-H', 'Accept: application/json',
                '-H', 'Content-Type: text/plain',  # CRITICAL!
                '-d', f'@{temp_file_path}',
                f'{self.base_url}/services'
            ]
            return await self._execute_curl(cmd)
        finally:
            os.unlink(temp_file_path)

    async def get_logs(self, service_id: str, limit: int = 50) -> list:
        """Get service logs using OWNER_ID from environment"""
        cmd = [
            'curl', '-H', f'Authorization: Bearer {self.api_key}',
            f'{self.base_url}/logs?ownerId={self.owner_id}&resource={service_id}&limit={limit}'
        ]
        result = await self._execute_curl(cmd)
        return result.get('logs', [])

    async def restart_service(self, service_id: str) -> Dict[str, Any]:
        """Restart service"""
        cmd = [
            'curl', '-X', 'POST',
            '-H', f'Authorization: Bearer {self.api_key}',
            '-H', 'Content-Type: application/json',
            '-d', '{}',
            f'{self.base_url}/services/{service_id}/restart'
        ]
        return await self._execute_curl(cmd)

    async def delete_service(self, service_id: str) -> Dict[str, Any]:
        """Delete service"""
        cmd = [
            'curl', '-X', 'DELETE',
            '-H', f'Authorization: Bearer {self.api_key}',
            f'{self.base_url}/services/{service_id}'
        ]
        return await self._execute_curl(cmd)

    async def delete_postgres_database(self, database_id: str) -> Dict[str, Any]:
        """Delete PostgreSQL database"""
        cmd = [
            'curl', '-X', 'DELETE',
            '-H', f'Authorization: Bearer {self.api_key}',
            f'{self.base_url}/postgres/{database_id}'
        ]
        return await self._execute_curl(cmd)

    async def _post_with_payload(self, url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """POST request with JSON payload"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            json.dump(payload, temp_file)
            temp_file_path = temp_file.name

        try:
            cmd = [
                'curl', '-X', 'POST',
                '-H', f'Authorization: Bearer {self.api_key}',
                '-H', 'Content-Type: application/json',
                '-d', f'@{temp_file_path}',
                url
            ]
            return await self._execute_curl(cmd)
        finally:
            os.unlink(temp_file_path)

    async def _execute_curl(self, cmd: list) -> Dict[str, Any]:
        """Execute curl command and return parsed JSON"""
        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise Exception(f"Curl failed: {stderr.decode()}")

        try:
            return json.loads(stdout.decode())
        except json.JSONDecodeError:
            return {"raw_response": stdout.decode()}