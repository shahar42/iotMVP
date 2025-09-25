"""
Render Service Deployment Tools
Full lifecycle management: create, configure, deploy services via API
"""

import asyncio
import aiohttp
import json
import requests
from typing import Dict, List, Optional, Any
from fastmcp import FastMCP

# Render API configuration
RENDER_BASE_URL = "https://api.render.com/v1"

def discover_workspaces_sync(api_key: str) -> Dict[str, Any]:
    """Synchronously discover all available workspaces for the API key"""
    try:
        headers = {"Authorization": f"Bearer {api_key}"}
        response = requests.get(f"{RENDER_BASE_URL}/owners", headers=headers)
        response.raise_for_status()

        workspaces = []
        for item in response.json():
            owner = item.get('owner', {})
            workspaces.append({
                'id': owner.get('id'),
                'name': owner.get('name'),
                'email': owner.get('email'),
                'type': owner.get('type')
            })

        return {
            'workspaces': workspaces,
            'count': len(workspaces),
            'default': workspaces[0]['id'] if workspaces else None
        }
    except Exception as e:
        return {'error': str(e), 'workspaces': [], 'count': 0}

def select_workspace_sync(workspace_hint: Optional[str], api_key: str) -> Dict[str, Any]:
    """Synchronously select workspace based on hint"""
    discovery = discover_workspaces_sync(api_key)

    if discovery.get('error'):
        return {'error': discovery['error']}

    workspaces = discovery['workspaces']
    if not workspaces:
        return {'error': 'No accessible workspaces found'}

    # If no hint provided, use default
    if not workspace_hint:
        return {
            'workspace': workspaces[0],
            'reason': f"Using default workspace from {len(workspaces)} available"
        }

    workspace_hint_lower = workspace_hint.lower()

    # Try exact match first
    for ws in workspaces:
        if ws['name'].lower() == workspace_hint_lower:
            return {
                'workspace': ws,
                'reason': f"Exact match for '{workspace_hint}'"
            }

    # Try partial match
    for ws in workspaces:
        if workspace_hint_lower in ws['name'].lower():
            return {
                'workspace': ws,
                'reason': f"Partial match: '{workspace_hint}' found in '{ws['name']}'"
            }

    # Try ID match
    for ws in workspaces:
        if ws['id'] == workspace_hint:
            return {
                'workspace': ws,
                'reason': f"ID match for '{workspace_hint}'"
            }

    # No match found, return default with suggestion
    available = ", ".join([f"{ws['name']}" for ws in workspaces])
    return {
        'workspace': workspaces[0],
        'reason': f"No match for '{workspace_hint}', using default. Available: {available}"
    }

def validate_service_commands(build_command: str, start_command: str) -> List[str]:
    """Validate build and start commands for common issues"""
    warnings = []

    # Check for local directory references that won't exist in the repo
    local_patterns = ['/home/', '/Users/', '/tmp/', './test_', './local']
    for pattern in local_patterns:
        if pattern in build_command:
            warnings.append(f"WARNING: Build command contains local path '{pattern}' - ensure this exists in your repository")
        if pattern in start_command:
            warnings.append(f"WARNING: Start command contains local path '{pattern}' - ensure this exists in your repository")

    # Check for common missing file references
    if 'package.json' in build_command and 'npm' not in build_command:
        warnings.append(f"WARNING: Build command references package.json but doesn't use npm/yarn")

    # Add git workflow reminder
    warnings.append(f"REMINDER: Ensure all local changes are committed and pushed to remote repository")
    warnings.append(f"   Run: git add . && git commit -m 'Deploy to Render' && git push")

    return warnings

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

def register_deployment_tools(mcp: FastMCP):
    """Register deployment tools with FastMCP server"""

    @mcp.tool()
    async def create_background_worker(
        name: str,
        repo_url: str,
        build_command: str,
        start_command: str,
        env_vars: List[Dict[str, str]],
        branch: str = "master",
        runtime: str = "python",
        owner_id: str = "tea-ctl9m2rv2p9s738eghng",
        api_key: str = "rnd_j6WyOXSMG0bGFbqyYKMBaxUgzF4s"
    ) -> str:
        """
        Create a new background worker service on Render.

        IMPORTANT: Ensure the GitHub repository URL is publicly accessible and the specified
        branch exists before creating the service. Verify the repository can be fetched at
        https://github.com/{owner}/{repo} and that the branch name is correct.

        USAGE PATTERN: User provides repository URL, LLM trusts that the current working directory
        corresponds to that repository. DO NOT question or validate the repository URL - trust
        the user's specification and use it directly.

        UX DESIGN PRINCIPLES: Prioritize intuitive user experience - make navigation effortless
        and every element purposeful. Use clear visual hierarchy and responsive design that
        works on all devices.

        VISUAL APPEAL: When creating web applications, focus on small actions with high visual
        impact - add CSS styling, use attractive colors, include nice typography, and add
        simple animations. These small touches make applications look professional and engaging
        with minimal effort.

        LAYOUT DESIGN: Default to creating full-width layouts for web applications.

        CRITICAL GIT WORKFLOW: Any new files or changes made locally MUST be committed and pushed
        to the remote repository BEFORE creating the service. Always remind the user:
        1. git add .
        2. git commit -m "Add files for deployment"
        3. git push
        Then create the service.

        Args:
            name: Service name (e.g., 'surf-lamp-monitoring')
            repo_url: GitHub repository URL (must be publicly accessible, format: https://github.com/{owner}/{repo})
            build_command: Command to build the service
            start_command: Command to start the service
            env_vars: List of environment variables [{"key": "NAME", "value": "VALUE"}]
            branch: Git branch to deploy from (verify this branch exists in the repository)
            runtime: Service runtime (python, node, etc.)
            owner_id: Render owner/team ID
            api_key: Render API key
        """

        payload = {
            "ownerId": owner_id,
            "type": "background_worker",
            "name": name,
            "repo": repo_url,
            "branch": branch,
            "serviceDetails": {
                "runtime": runtime,
                "envSpecificDetails": {
                    "buildCommand": build_command,
                    "startCommand": start_command
                }
            }
        }

        # Add env vars if provided
        if env_vars:
            payload["envVars"] = env_vars

        # Validate commands before creating service
        validation_warnings = validate_service_commands(build_command, start_command)

        try:
            result = await make_render_request("POST", "/services", api_key, payload)
            service_id = result.get("service", {}).get("id", "unknown")
            service_name = result.get("service", {}).get("name", name)

            response_parts = [f"""SUCCESS: Background Worker Created Successfully!

ID: Service ID: {service_id}
NAME: Service Name: {service_name}
REPO: Repository: {repo_url}
BRANCH: Branch: {branch}
BUILD: Build: {build_command}
START: Start: {start_command}
RUNTIME: Runtime: {runtime}
CONFIG: Environment Variables: {len(env_vars)} configured

The service is now building and will be available shortly.
Check the Render dashboard for build logs and deployment status."""]

            # Add warnings if any
            if validation_warnings:
                response_parts.append("\nWARNING: VALIDATION WARNINGS:")
                response_parts.extend([f"   {warning}" for warning in validation_warnings])

            return "\n".join(response_parts)
        except Exception as e:
            return f"ERROR: Failed to create background worker: {str(e)}"

    @mcp.tool()
    async def create_web_service_with_workspace_discovery(
        name: str,
        repo_url: str,
        build_command: str,
        start_command: str,
        env_vars: List[Dict[str, str]],
        workspace_hint: Optional[str] = None,
        branch: str = "master",
        runtime: str = "node",
        api_key: str = "rnd_j6WyOXSMG0bGFbqyYKMBaxUgzF4s"
    ) -> str:
        """
        LLM INSTRUCTION: Create Render web service with automatic workspace discovery.

        LLM BEHAVIOR:
        - NEVER run local tests (npm install, npm run dev) before deployment
        - This tool makes REAL API calls to Render (no simulations)
        - Use exact repository URLs provided by user
        - Handle real API errors gracefully
        - Return actual service IDs and URLs from Render API

        CRITICAL: This function makes real API calls. Service creation requires valid payment info.

        Args:
            name: Service name
            repo_url: GitHub repository URL (must be publicly accessible)
            build_command: Command to build the service
            start_command: Command to start the service
            env_vars: List of environment variables [{"key": "NAME", "value": "VALUE"}]
            workspace_hint: Optional workspace name/ID hint (uses fuzzy matching)
            branch: Git branch to deploy from (default: master)
            runtime: Service runtime (default: node)
            api_key: Render API key

        Example: create_web_service_with_workspace_discovery("my-app", "https://github.com/user/repo", "npm install", "npm start", [{"key": "NODE_ENV", "value": "production"}], "database")
        """
        try:
            # Step 1: Discover and select workspace
            workspace_selection = select_workspace_sync(workspace_hint, api_key)

            if workspace_selection.get('error'):
                return f"ERROR: Cannot select workspace: {workspace_selection['error']}"

            selected_workspace = workspace_selection['workspace']
            selection_reason = workspace_selection['reason']

            # Step 2: Validate commands
            validation_warnings = validate_service_commands(build_command, start_command)

            # Step 3: Create web service payload
            payload = {
                "ownerId": selected_workspace['id'],
                "type": "web_service",
                "name": name,
                "repo": repo_url,
                "branch": branch,
                "serviceDetails": {
                    "runtime": runtime,
                    "envSpecificDetails": {
                        "buildCommand": build_command,
                        "startCommand": start_command
                    }
                }
            }

            # Add env vars if provided
            if env_vars:
                payload["envVars"] = env_vars

            # Step 4: Create the service
            result = await make_render_request("POST", "/services", api_key, payload)
            service_id = result.get("service", {}).get("id", "unknown")
            service_name = result.get("service", {}).get("name", name)
            service_url = result.get("service", {}).get("serviceDetails", {}).get("url", "")

            response_parts = [f"""SUCCESS: Web Service Created with Workspace Discovery!

WORKSPACE_SELECTION:
  {selection_reason}
  Selected: {selected_workspace['name']} ({selected_workspace['id']})

SERVICE_INFO:
  ID: {service_id}
  Name: {service_name}
  URL: {service_url}
  Repository: {repo_url}
  Branch: {branch}
  Runtime: {runtime}

COMMANDS:
  Build: {build_command}
  Start: {start_command}

CONFIG:
  Environment Variables: {len(env_vars)} configured

STATUS: Service is now building and will be available at the URL above once deployed.

WORKSPACE: Service created in {selected_workspace['name']} workspace"""]

            # Add warnings if any
            if validation_warnings:
                response_parts.append("\nWARNING: VALIDATION WARNINGS:")
                response_parts.extend([f"   {warning}" for warning in validation_warnings])

            return "\n".join(response_parts)

        except Exception as e:
            error_msg = str(e)
            if "402" in error_msg and "Payment" in error_msg:
                return f"""ERROR: Payment information required for web service creation

ISSUE: Render API requires payment information to create web services via API, even for free tier services.

WORKSPACE_ATTEMPTED: {selected_workspace['name'] if 'selected_workspace' in locals() else 'Unknown'} ({selected_workspace['id'] if 'selected_workspace' in locals() else 'Unknown'})

SOLUTIONS:
1. Add payment information at: https://dashboard.render.com/billing
2. Create service manually through Render dashboard in the correct workspace
3. Use existing services and configure them manually

ORIGINAL_ERROR: {error_msg}"""
            else:
                return f"ERROR: Failed to create web service: {error_msg}\nWORKSPACE_ATTEMPTED: {selected_workspace['name'] if 'selected_workspace' in locals() else 'Unknown'}"

    @mcp.tool()
    async def create_web_service(
        name: str,
        repo_url: str,
        build_command: str,
        start_command: str,
        env_vars: List[Dict[str, str]],
        branch: str = "master",
        runtime: str = "python",
        owner_id: str = "tea-ctl9m2rv2p9s738eghng",
        api_key: str = "rnd_j6WyOXSMG0bGFbqyYKMBaxUgzF4s"
    ) -> str:
        """
        LLM INSTRUCTION: Create Render web service with specific configuration.

        LLM CRITICAL BEHAVIOR:
        - NEVER run local tests (npm install, npm run dev, yarn start, etc.)
        - NEVER test locally before deployment
        - Make REAL API calls to Render only
        - Trust user's repository URL exactly as provided
        - Ensure user has committed changes before calling this tool

        LLM WORKFLOW:
        1. User provides repository URL and configuration
        2. Verify user has committed and pushed changes
        3. Call this tool with exact parameters
        4. Handle real API responses and errors
        5. Return actual service ID and URL from Render

        CRITICAL: This makes real API calls to create actual Render services.

        Args:
            name: Service name
            repo_url: GitHub repository URL (must be publicly accessible, format: https://github.com/{owner}/{repo})
            build_command: Command to build the service
            start_command: Command to start the service
            env_vars: List of environment variables
            branch: Git branch to deploy from (verify this branch exists in the repository)
            runtime: Service runtime
            owner_id: Render owner/team ID
            api_key: Render API key
        """

        payload = {
            "ownerId": owner_id,
            "type": "web_service",
            "name": name,
            "repo": repo_url,
            "branch": branch,
            "serviceDetails": {
                "runtime": runtime,
                "envSpecificDetails": {
                    "buildCommand": build_command,
                    "startCommand": start_command
                }
            }
        }

        # Add env vars if provided
        if env_vars:
            payload["envVars"] = env_vars

        # Validate commands before creating service
        validation_warnings = validate_service_commands(build_command, start_command)

        try:
            result = await make_render_request("POST", "/services", api_key, payload)
            service_id = result.get("service", {}).get("id", "unknown")
            service_name = result.get("service", {}).get("name", name)
            service_url = result.get("service", {}).get("serviceDetails", {}).get("url", "")

            response_parts = [f"""SUCCESS: Web Service Created Successfully!

ID: Service ID: {service_id}
NAME: Service Name: {service_name}
URL: Service URL: {service_url}
REPO: Repository: {repo_url}
BRANCH: Branch: {branch}
BUILD: Build: {build_command}
START: Start: {start_command}
RUNTIME: Runtime: {runtime}
CONFIG: Environment Variables: {len(env_vars)} configured

The service is now building and will be available at the URL above once deployed."""]

            # Add warnings if any
            if validation_warnings:
                response_parts.append("\nWARNING: VALIDATION WARNINGS:")
                response_parts.extend([f"   {warning}" for warning in validation_warnings])

            return "\n".join(response_parts)
        except Exception as e:
            return f"ERROR: Failed to create web service: {str(e)}"

    @mcp.tool()
    async def update_service_env_vars(
        service_id: str,
        env_vars: List[Dict[str, str]],
        api_key: str = "rnd_j6WyOXSMG0bGFbqyYKMBaxUgzF4s"
    ) -> str:
        """
        Update environment variables for an existing service.

        Args:
            service_id: Render service ID
            env_vars: List of environment variables [{"key": "NAME", "value": "VALUE"}]
            api_key: Render API key
        """

        payload = {"envVars": env_vars}

        try:
            await make_render_request("PUT", f"/services/{service_id}/env-vars", api_key, payload)
            return f"""SUCCESS: Environment Variables Updated!

ID: Service ID: {service_id}
CONFIG: Updated Variables: {len(env_vars)}

Variables:
{chr(10).join([f'  • {var["key"]}: {"***" if "password" in var["key"].lower() or "key" in var["key"].lower() else var["value"]}' for var in env_vars])}

The service will automatically redeploy with the new configuration.
"""
        except Exception as e:
            return f"ERROR: Failed to update environment variables: {str(e)}"

    @mcp.tool()
    async def trigger_deploy(
        service_id: str,
        clear_cache: bool = False,
        api_key: str = "rnd_j6WyOXSMG0bGFbqyYKMBaxUgzF4s"
    ) -> str:
        """
        Trigger a manual deployment for a service.

        Args:
            service_id: Render service ID
            clear_cache: Whether to clear build cache
            api_key: Render API key
        """

        payload = {"clearCache": clear_cache}

        try:
            result = await make_render_request("POST", f"/services/{service_id}/deploys", api_key, payload)
            deploy_id = result.get("id", "unknown")

            return f"""SUCCESS: Deployment Triggered!

ID: Service ID: {service_id}
DEPLOY: Deploy ID: {deploy_id}
CACHE: Cache Cleared: {'Yes' if clear_cache else 'No'}

The deployment is now in progress.
Check the Render dashboard for build logs and status updates.
"""
        except Exception as e:
            return f"ERROR: Failed to trigger deployment: {str(e)}"

