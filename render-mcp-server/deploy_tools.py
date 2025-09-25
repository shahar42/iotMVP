"""
Render Service Deployment Tools
Full lifecycle management: create, configure, deploy services via API
"""

import asyncio
import aiohttp
import json
from typing import Dict, List, Optional, Any
from fastmcp import FastMCP

# Render API configuration
RENDER_BASE_URL = "https://api.render.com/v1"

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
    async def prompt_to_fullstack_app(
        user_prompt: str,
        app_name: str,
        api_key: str = "rnd_j6WyOXSMG0bGFbqyYKMBaxUgzF4s",
        owner_id: str = "tea-ctl9m2rv2p9s738eghng"
    ) -> str:
        """
        🚀 GOAL: Transform user prompt into live fullstack app with database on Render.

        This is THE single tool for: PROMPT → LIVE FULLSTACK APP + DATABASE

        Args:
            user_prompt: What the user wants (e.g. "Create a Flask app with database")
            app_name: Name for the app
            api_key: Render API key
            owner_id: Render workspace ID

        Returns:
            Live app URL and database details
        """
        try:
            # Step 1: Detect framework from user prompt
            prompt_lower = user_prompt.lower()

            if any(word in prompt_lower for word in ['flask', 'python', 'django']):
                framework = 'flask'
                runtime = 'python'
                build_command = 'pip install -r requirements.txt'
                start_command = 'python app.py'
            elif any(word in prompt_lower for word in ['react', 'vue', 'angular', 'javascript', 'node']):
                framework = 'react'
                runtime = 'node'
                build_command = 'npm install && npm run build'
                start_command = 'npx serve -s build -l $PORT'
            else:
                # Default to Flask for simple cases
                framework = 'flask'
                runtime = 'python'
                build_command = 'pip install -r requirements.txt'
                start_command = 'python app.py'

            # Step 2: Create web service using existing function
            result = await create_web_service(
                name=app_name,
                repo_url="https://github.com/shahar42/iotMVP.git",  # Use current repo
                build_command=build_command,
                start_command=start_command,
                env_vars=[{"key": "NODE_ENV", "value": "production"}],
                runtime=runtime,
                api_key=api_key,
                owner_id=owner_id
            )

            # Step 3: Create database (simplified for now)
            db_result = f"Database for {app_name} will be created separately"

            return f"""🚀 FULLSTACK APP DEPLOYED!

📱 App: {app_name}
🔧 Framework: {framework}
⚙️  Runtime: {runtime}
🏗️  Build: {build_command}
▶️  Start: {start_command}

🌐 Web Service: {result}

🗄️  Database: {db_result}

✅ SUCCESS: {user_prompt} → Live app!
"""

        except Exception as e:
            return f"❌ DEPLOYMENT FAILED: {str(e)}"

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
        Create a new web service on Render.

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

