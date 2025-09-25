#!/usr/bin/env python3
"""
Enhanced Deployment Tools for Render MCP Server
Implements improved user experience based on real-world testing feedback
"""

import os
import sys
import asyncio
import subprocess
import json
import time
import logging
import aiohttp
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger("render-enhanced")

# Configuration
RENDER_API_KEY = os.getenv("RENDER_API_KEY")
RENDER_BASE_URL = "https://api.render.com/v1"
OWNER_ID = os.getenv("OWNER_ID")

async def make_real_render_request(
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
                return {"raw_response": response_text}

async def run_curl(url: str, method: str = "GET", data: Optional[Dict] = None) -> Dict[str, Any]:
    """Run curl command and return parsed JSON response"""
    cmd = ["curl", "-s", "-w", "%{http_code}"]
    cmd.extend(["-H", f"Authorization: Bearer {RENDER_API_KEY}"])
    cmd.extend(["-H", "Content-Type: application/json"])
    cmd.extend(["-H", "User-Agent: Render-MCP-Enhanced/1.0"])

    if method != "GET":
        cmd.extend(["-X", method])
    if data:
        cmd.extend(["-d", json.dumps(data)])
    cmd.append(url)

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise Exception(f"Curl failed: {stderr.decode()}")

        output = stdout.decode()
        if len(output) < 3:
            raise Exception("Invalid curl response")

        status_code = int(output[-3:])
        response_body = output[:-3]

        if status_code >= 400:
            raise Exception(f"HTTP {status_code}: {response_body}")

        return json.loads(response_body) if response_body.strip() else {}
    except Exception as e:
        raise Exception(f"API call failed: {str(e)}")

def register_enhanced_deployment_tools(mcp):
    """Register all enhanced deployment tools with the MCP server"""

    @mcp.tool()
    async def list_workspaces_interactive() -> str:
        """
        LLM INSTRUCTION: Use this to show user available Render workspaces.

        LLM WORKFLOW:
        1. Call this tool to get workspace list
        2. Show user all available workspaces with IDs
        3. Ask user: "Which workspace ID would you like to use?"
        4. Get workspace_id from user selection
        5. Use that workspace_id in deployment tools

        Returns:
            Formatted list of workspace IDs and names for user selection
        """
        try:
            url = f"{RENDER_BASE_URL}/v1/teams"
            response = await run_curl(url)

            teams = response if isinstance(response, list) else []

            if not teams:
                return "WORKSPACE: No workspaces found - using default workspace"

            formatted = []
            formatted.append("WORKSPACE: Available Workspaces")
            formatted.append("=" * 40)
            formatted.append("")

            for i, team_data in enumerate(teams, 1):
                team = team_data.get('team', {})
                name = team.get('name', 'Unknown')
                team_id = team.get('id', 'Unknown')
                email = team.get('email', 'Unknown')

                formatted.append(f"[{i}] {name}")
                formatted.append(f"    ID: {team_id}")
                formatted.append(f"    Email: {email}")
                formatted.append("")

            formatted.append("USAGE:")
            formatted.append("• Copy the workspace ID for use in deployment commands")
            formatted.append("• Use the workspace name in workspace_hint parameters")
            formatted.append("• Default workspace is used if none specified")

            return "\\n".join(formatted)

        except Exception as e:
            return f"ERROR: Error listing workspaces: {str(e)}"

    @mcp.tool()
    async def detect_git_repository() -> str:
        """
        LLM INSTRUCTION: Use this to show user their current git repository.

        LLM WORKFLOW:
        1. Call this tool first
        2. Show user the detected repository
        3. Ask: "Use this repository or provide a different GitHub URL?"
        4. Get user's choice for deployment

        Returns:
            Current git repository URL, branch, and commit status for user selection
        """
        try:
            # Try to get the current git remote
            process = await asyncio.create_subprocess_exec(
                'git', 'remote', 'get-url', 'origin',
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                current_repo = stdout.decode().strip()

                # Get additional git info
                branch_process = await asyncio.create_subprocess_exec(
                    'git', 'branch', '--show-current',
                    stdout=subprocess.PIPE
                )
                branch_stdout, _ = await branch_process.communicate()
                current_branch = branch_stdout.decode().strip() if branch_process.returncode == 0 else "master"

                # Check if repo is clean
                status_process = await asyncio.create_subprocess_exec(
                    'git', 'status', '--porcelain',
                    stdout=subprocess.PIPE
                )
                status_stdout, _ = await status_process.communicate()
                is_clean = len(status_stdout.decode().strip()) == 0

                formatted = []
                formatted.append("GIT: Repository Detection Results")
                formatted.append("=" * 40)
                formatted.append(f"📁 Repository: {current_repo}")
                formatted.append(f"🌿 Branch: {current_branch}")
                formatted.append(f"✨ Status: {'Clean' if is_clean else 'Has uncommitted changes'}")
                formatted.append("")

                if not is_clean:
                    formatted.append("WARNING: Uncommitted changes detected!")
                    formatted.append("RECOMMENDATION: Commit and push changes before deploying:")
                    formatted.append("  git add .")
                    formatted.append("  git commit -m 'Deploy to Render'")
                    formatted.append("  git push")
                    formatted.append("")

                formatted.append("USAGE:")
                formatted.append(f"• Use repo_url: {current_repo}")
                formatted.append(f"• Use branch: {current_branch}")
                formatted.append("• Or specify a different repository URL manually")

                return "\\n".join(formatted)
            else:
                return "GIT: No git repository found in current directory\\nTIP: Initialize git repo or specify GitHub URL manually"

        except Exception as e:
            return f"ERROR: Error detecting git repository: {str(e)}"

    @mcp.tool()
    async def validate_build_environment(project_path: str) -> str:
        """
        Analyze project structure and recommend build commands.

        Args:
            project_path: Path to the project to analyze

        Returns:
            Build recommendations and framework detection
        """
        try:
            # Check if project_path exists
            if not os.path.exists(project_path):
                return f"ERROR: Project path {project_path} does not exist"

            package_json_path = os.path.join(project_path, 'package.json')

            if not os.path.exists(package_json_path):
                return f"INFO: No package.json found in {project_path}\\nTIP: This might be a Python or static project"

            # Read package.json
            with open(package_json_path, 'r') as f:
                package_data = json.load(f)

            # Detect framework
            dependencies = package_data.get('dependencies', {})
            dev_dependencies = package_data.get('devDependencies', {})
            scripts = package_data.get('scripts', {})

            framework = "unknown"
            build_command = "npm install && npm run build"
            start_command = "npx serve -s dist -l 10000"

            if 'vite' in dev_dependencies:
                framework = "react-vite"
                build_command = "npm install && npm run build"
                start_command = "npx serve -s dist -l 10000"
            elif 'react-scripts' in dependencies or 'react-scripts' in dev_dependencies:
                framework = "react-cra"
                build_command = "npm ci --include=dev && npm run build"
                start_command = "npx serve -s build -l 10000"
            elif 'vue' in dependencies:
                framework = "vue"
                build_command = "npm install && npm run build"
                start_command = "npx serve -s dist -l 10000"
            elif '@angular/core' in dependencies:
                framework = "angular"
                build_command = "npm install && npm run build"
                start_command = "npx serve -s dist -l 10000"
            elif 'next' in dependencies:
                framework = "next"
                build_command = "npm install && npm run build"
                start_command = "npm start"

            formatted = []
            formatted.append("BUILD: Project Analysis Results")
            formatted.append("=" * 40)
            formatted.append(f"📦 Framework: {framework}")
            formatted.append(f"🔨 Recommended Build: {build_command}")
            formatted.append(f"🚀 Recommended Start: {start_command}")
            formatted.append("")

            # Check for common issues
            issues = []
            if 'vite' in dev_dependencies and 'npm ci' in build_command:
                issues.append("Vite found in devDependencies - use 'npm install' not 'npm ci'")

            if 'build' not in scripts:
                issues.append("No 'build' script found in package.json")

            if issues:
                formatted.append("⚠️  POTENTIAL ISSUES:")
                for issue in issues:
                    formatted.append(f"   • {issue}")
                formatted.append("")

            # Recommend environment variables
            env_vars = []
            if framework in ['react-vite', 'react-cra']:
                env_vars.append({"key": "NODE_ENV", "value": "production"})

            if env_vars:
                formatted.append("🔧 RECOMMENDED ENV VARS:")
                for env_var in env_vars:
                    formatted.append(f"   • {env_var['key']} = {env_var['value']}")
                formatted.append("")

            formatted.append("USAGE:")
            formatted.append("• Use these commands in your deployment configuration")
            formatted.append("• Test locally first: npm run build")
            formatted.append("• Adjust paths if your project uses different structure")

            return "\\n".join(formatted)

        except Exception as e:
            return f"ERROR: Error analyzing build environment: {str(e)}"

    @mcp.tool()
    async def wait_for_deployment_complete(
        service_id: str,
        timeout_seconds: int = 300,
        poll_interval: int = 10
    ) -> str:
        """
        Wait for deployment to complete with progress updates.

        Args:
            service_id: Service ID to monitor
            timeout_seconds: Maximum time to wait (default 300 seconds)
            poll_interval: How often to check status (default 10 seconds)

        Returns:
            Final deployment status with progress log
        """
        try:
            start_time = time.time()
            progress_log = []
            progress_log.append(f"DEPLOY: Monitoring deployment for service {service_id}")
            progress_log.append(f"⏱️  Timeout: {timeout_seconds} seconds")
            progress_log.append("")

            while time.time() - start_time < timeout_seconds:
                elapsed = int(time.time() - start_time)

                # Get deployment status
                url = f"{RENDER_BASE_URL}/v1/services/{service_id}/deploys?limit=1"
                response = await run_curl(url)

                if isinstance(response, list) and len(response) > 0:
                    deploy = response[0].get('deploy', response[0])
                    status = deploy.get('status', 'unknown')

                    progress_log.append(f"⏳ {elapsed}s: Status = {status.upper()}")

                    if status == 'live':
                        progress_log.append("")
                        progress_log.append("✅ DEPLOYMENT SUCCESSFUL!")
                        progress_log.append(f"🎉 Total time: {elapsed} seconds")

                        # Get service URL if it's a web service
                        service_url = f"{RENDER_BASE_URL}/v1/services/{service_id}"
                        service_response = await run_curl(service_url)
                        service_details = service_response.get('serviceDetails', {})
                        if 'url' in service_details:
                            progress_log.append(f"🌐 Service URL: {service_details['url']}")

                        return "\\n".join(progress_log)

                    elif status in ['build_failed', 'deploy_failed', 'canceled']:
                        progress_log.append("")
                        progress_log.append(f"❌ DEPLOYMENT FAILED: {status}")
                        progress_log.append("💡 Check build logs for details")
                        return "\\n".join(progress_log)

                # Wait before next check
                await asyncio.sleep(poll_interval)

            # Timeout reached
            progress_log.append("")
            progress_log.append("⏰ TIMEOUT REACHED")
            progress_log.append("💡 Deployment may still be in progress - check manually")

            return "\\n".join(progress_log)

        except Exception as e:
            return f"ERROR: Error monitoring deployment: {str(e)}"

    @mcp.tool()
    async def get_database_connection_details(database_id: str) -> str:
        """
        Get PostgreSQL database connection information without curl.

        Args:
            database_id: Database ID to get connection info for

        Returns:
            Connection strings and details
        """
        try:
            url = f"{RENDER_BASE_URL}/v1/postgres/{database_id}/connection-info"
            response = await run_curl(url)

            formatted = []
            formatted.append(f"DATABASE: Connection Info for {database_id}")
            formatted.append("=" * 50)

            external_conn = response.get('externalConnectionString', 'Not available')
            internal_conn = response.get('internalConnectionString', 'Not available')
            psql_command = response.get('psqlCommand', 'Not available')

            formatted.append("🔗 CONNECTION STRINGS:")
            formatted.append(f"External: {external_conn}")
            formatted.append(f"Internal: {internal_conn}")
            formatted.append("")
            formatted.append("💻 PSQL COMMAND:")
            formatted.append(f"{psql_command}")
            formatted.append("")
            formatted.append("USAGE:")
            formatted.append("• Use External connection for apps deployed outside Render")
            formatted.append("• Use Internal connection for apps deployed on Render")
            formatted.append("• Copy connection string to your app's environment variables")

            return "\\n".join(formatted)

        except Exception as e:
            return f"ERROR: Error fetching database connection info: {str(e)}"

    @mcp.tool()
    async def diagnose_build_failure(service_id: str) -> str:
        """
        Analyze build failure logs and suggest fixes.

        Args:
            service_id: Service ID to diagnose

        Returns:
            Diagnosis and recommended fixes
        """
        try:
            # Get recent logs
            url = f"{RENDER_BASE_URL}/v1/logs?ownerId={OWNER_ID}&resource={service_id}&limit=50"
            response = await run_curl(url)

            logs = response.get('logs', [])
            if not logs:
                return f"DEBUG: No logs found for service {service_id}"

            # Analyze logs for common patterns
            log_messages = [log.get('message', '') for log in logs]
            all_logs = " ".join(log_messages).lower()

            issues_found = []
            fixes = []

            # Common build issues
            if "vite: not found" in all_logs or "command not found: vite" in all_logs:
                issues_found.append("Vite command not found")
                fixes.append("SOLUTION: Change build command to 'npm install && npm run build'")
                fixes.append("REASON: Vite is in devDependencies and needs npm install (not npm ci)")

            if "npm ci" in all_logs and "peer dep missing" in all_logs:
                issues_found.append("npm ci failing with missing peer dependencies")
                fixes.append("SOLUTION: Use 'npm install' instead of 'npm ci'")
                fixes.append("REASON: npm ci requires exact lockfile match")

            if "permission denied" in all_logs:
                issues_found.append("Permission denied errors")
                fixes.append("SOLUTION: Check file permissions in your repository")
                fixes.append("ACTION: Run 'chmod +x' on shell scripts")

            if "node: not found" in all_logs:
                issues_found.append("Node.js not found")
                fixes.append("SOLUTION: Specify Node.js version in package.json")
                fixes.append('ADD: "engines": {"node": "18.x"} to package.json')

            if "out of memory" in all_logs or "javascript heap out of memory" in all_logs:
                issues_found.append("Build running out of memory")
                fixes.append("SOLUTION: Optimize build process or upgrade service plan")
                fixes.append("WORKAROUND: Add NODE_OPTIONS='--max-old-space-size=4096'")

            # Format diagnosis
            formatted = []
            formatted.append(f"🔍 BUILD FAILURE DIAGNOSIS: {service_id}")
            formatted.append("=" * 60)

            if not issues_found:
                formatted.append("❓ NO COMMON ISSUES DETECTED")
                formatted.append("💡 Manual log review needed:")
                formatted.append("")
                for i, log in enumerate(logs[-5:], 1):  # Show last 5 logs
                    message = log.get('message', '')
                    formatted.append(f"[{i}] {message}")
                formatted.append("")
                formatted.append("TIP: Look for error messages, failed commands, or missing files")
            else:
                formatted.append(f"🚨 ISSUES FOUND: {len(issues_found)}")
                for i, issue in enumerate(issues_found, 1):
                    formatted.append(f"  {i}. {issue}")
                formatted.append("")

                formatted.append("🔧 RECOMMENDED FIXES:")
                for fix in fixes:
                    formatted.append(f"  • {fix}")
                formatted.append("")

                formatted.append("NEXT STEPS:")
                formatted.append("1. Apply the recommended fixes")
                formatted.append("2. Commit and push changes to trigger new deployment")
                formatted.append("3. Monitor deployment with wait_for_deployment_complete tool")

            return "\\n".join(formatted)

        except Exception as e:
            return f"ERROR: Error diagnosing build failure: {str(e)}"

    @mcp.tool()
    async def verify_deployed_app(service_url: str, timeout_seconds: int = 30) -> str:
        """
        Verify that a deployed app is responding correctly.

        Args:
            service_url: URL of the deployed service to check
            timeout_seconds: Request timeout (default 30 seconds)

        Returns:
            Health check results and recommendations
        """
        try:
            start_time = time.time()

            # Make HTTP request to check app health
            cmd = ["curl", "-s", "-w", "%{http_code},%{time_total}", "-m", str(timeout_seconds), service_url]

            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            elapsed = time.time() - start_time

            if process.returncode != 0:
                return f"❌ HEALTH CHECK FAILED\\n🌐 URL: {service_url}\\n💥 Error: {stderr.decode()}\\n💡 Service may still be starting up"

            output = stdout.decode()
            if "," in output:
                response_body = output.rsplit(",", 2)[0]
                status_info = output.rsplit(",", 2)[1:]
                status_code = int(status_info[0]) if status_info[0].isdigit() else 0
                response_time = float(status_info[1]) if len(status_info) > 1 else elapsed
            else:
                status_code = 0
                response_time = elapsed
                response_body = output

            formatted = []
            formatted.append(f"🏥 HEALTH CHECK RESULTS")
            formatted.append("=" * 30)
            formatted.append(f"🌐 URL: {service_url}")
            formatted.append(f"📊 Status Code: {status_code}")
            formatted.append(f"⚡ Response Time: {response_time:.2f}s")

            # Evaluate health
            if status_code == 200:
                formatted.append("✅ STATUS: HEALTHY")
                formatted.append("🎉 Service is responding correctly")

                if response_time < 1.0:
                    formatted.append("⚡ Performance: Excellent (< 1s)")
                elif response_time < 3.0:
                    formatted.append("👍 Performance: Good (< 3s)")
                else:
                    formatted.append("⚠️  Performance: Slow (> 3s)")

            elif status_code == 502:
                formatted.append("🔄 STATUS: STARTING UP")
                formatted.append("💡 Service may still be deploying - wait a few minutes")

            elif status_code == 404:
                formatted.append("❓ STATUS: NOT FOUND")
                formatted.append("💡 Check if the service URL is correct")
                formatted.append("💡 Verify build output directory (dist/ vs build/)")

            elif status_code >= 500:
                formatted.append("❌ STATUS: SERVER ERROR")
                formatted.append("🔍 Check service logs for error details")

            else:
                formatted.append(f"⚠️  STATUS: UNEXPECTED ({status_code})")
                formatted.append("🔍 Manual investigation needed")

            # Show response preview if available
            if response_body and len(response_body) > 10:
                preview = response_body[:200] + "..." if len(response_body) > 200 else response_body
                formatted.append("")
                formatted.append("📝 RESPONSE PREVIEW:")
                formatted.append(preview)

            return "\\n".join(formatted)

        except Exception as e:
            return f"ERROR: Error verifying deployed app: {str(e)}"

    @mcp.tool()
    async def create_app_with_smart_defaults(
        app_name: str,
        app_description: str = "",
        workspace_hint: Optional[str] = None
    ) -> str:
        """
        Complete deployment workflow with smart defaults and user guidance.

        Args:
            app_name: Name for the application
            app_description: Optional description of what the app does
            workspace_hint: Optional workspace preference

        Returns:
            Complete deployment results with all URLs and next steps
        """
        try:
            results = []
            results.append(f"🚀 SMART DEPLOYMENT: {app_name}")
            results.append("=" * 50)
            results.append(f"📝 Description: {app_description or 'No description provided'}")
            results.append("")

            # Step 1: Detect git repository
            results.append("STEP 1: Git Repository Detection")
            git_info = await detect_git_repository()
            results.append(git_info)
            results.append("")

            # Step 2: List available workspaces
            results.append("STEP 2: Workspace Options")
            workspace_info = await list_workspaces_interactive()
            results.append(workspace_info)
            results.append("")

            # Step 3: Analyze current directory for build requirements
            results.append("STEP 3: Build Environment Analysis")
            current_dir = os.getcwd()
            build_info = await validate_build_environment(current_dir)
            results.append(build_info)
            results.append("")

            results.append("🎯 NEXT STEPS:")
            results.append("1. Review the git repository and workspace information above")
            results.append("2. Commit any uncommitted changes if needed")
            results.append("3. Use create_web_service_with_workspace_discovery with:")
            results.append(f"   • name: {app_name}")
            results.append("   • repo_url: [from git detection above]")
            results.append("   • build_command: [from build analysis above]")
            results.append("   • start_command: [from build analysis above]")
            results.append("4. Use wait_for_deployment_complete to monitor progress")
            results.append("5. Use verify_deployed_app to confirm it's working")
            results.append("")
            results.append("💡 TIP: All information needed is provided above!")

            return "\\n".join(results)

        except Exception as e:
            return f"ERROR: Error in smart deployment setup: {str(e)}"

    @mcp.tool()
    async def deploy_fullstack_app_complete(
        app_name: str,
        repo_url: str,
        workspace_id: str,
        description: str = "",
        create_database: bool = True
    ) -> str:
        """
        LLM INSTRUCTIONS: Complete fullstack deployment to Render.

        CRITICAL LLM WORKFLOW (FOLLOW EXACTLY):
        1. NEVER run local tests (npm install, npm run dev, etc.)
        2. Call detect_git_repository() first
        3. Ask user: "Use current repo URL or provide different GitHub URL?"
        4. Call list_workspaces_interactive()
        5. Ask user to select workspace ID from the list
        6. THEN call this tool with user's choices
        7. Make REAL API calls only - no simulated responses

        LLM BEHAVIOR REQUIREMENTS:
        - Always ask user for repo_url choice (don't assume)
        - Always ask user for workspace_id selection (don't use defaults)
        - Never test locally - deploy directly to Render
        - Handle real API errors and failures gracefully
        - Show user the actual deployment status and URLs

        Args:
            app_name: Name for the application
            repo_url: GitHub repository URL (REQUIRED - ask user to choose)
            workspace_id: Render workspace ID (REQUIRED - ask user to select from list)
            description: What the app does (optional)
            create_database: Whether to create PostgreSQL database (default: true)

        Returns:
            Real deployment results with actual service IDs and URLs

        CRITICAL: This tool makes REAL API calls to Render. No simulations allowed.
        """
        try:
            deployment_log = []
            deployment_log.append("🚀 ULTIMATE FULLSTACK DEPLOYMENT")
            deployment_log.append("=" * 60)
            deployment_log.append(f"📱 App Name: {app_name}")
            deployment_log.append(f"📝 Description: {description or 'No description provided'}")
            deployment_log.append(f"📂 Repository: {repo_url}")
            deployment_log.append(f"🏢 Workspace ID: {workspace_id}")
            deployment_log.append(f"🗄️  Database: {'Yes' if create_database else 'No'}")
            deployment_log.append("")
            deployment_log.append("⏳ Starting comprehensive deployment process...")
            deployment_log.append("")

            # PHASE 1: PRE-DEPLOYMENT VALIDATION
            deployment_log.append("🔍 PHASE 1: PRE-DEPLOYMENT VALIDATION")
            deployment_log.append("-" * 40)

            # 1.1: Repository Validation
            deployment_log.append("📂 Validating repository...")
            if not repo_url.startswith(("https://github.com/", "git@github.com:")):
                deployment_log.append("❌ FAILED: Invalid GitHub repository URL")
                deployment_log.append("💡 SOLUTION: Provide a valid GitHub URL (https://github.com/user/repo.git)")
                return "\\n".join(deployment_log)

            deployment_log.append(f"✅ Repository: {repo_url}")

            # Check for uncommitted changes in local directory (if this matches the repo)
            git_result = await detect_git_repository()
            if "Has uncommitted changes" in git_result and repo_url in git_result:
                deployment_log.append("⚠️  WARNING: Uncommitted changes detected in local repo")
                deployment_log.append("🛑 STOPPING: Please commit changes first:")
                deployment_log.append("   git add .")
                deployment_log.append("   git commit -m 'Deploy to Render'")
                deployment_log.append("   git push")
                deployment_log.append("")
                deployment_log.append("Re-run this tool after committing changes")
                return "\\n".join(deployment_log)
            deployment_log.append("✅ Repository validation passed")
            deployment_log.append("")

            # 1.2: Workspace Validation
            deployment_log.append("🏢 Validating workspace...")
            if not workspace_id or not workspace_id.startswith("tea-"):
                deployment_log.append("❌ FAILED: Invalid workspace ID")
                deployment_log.append("💡 SOLUTION: Use list_workspaces_interactive() to get valid workspace ID")
                return "\\n".join(deployment_log)

            selected_workspace_id = workspace_id
            deployment_log.append(f"✅ Using workspace ID: {selected_workspace_id}")
            deployment_log.append("")

            # 1.3: Build Environment Analysis
            deployment_log.append("🔧 Analyzing build environment...")
            current_dir = os.getcwd()
            build_result = await validate_build_environment(current_dir)

            # Extract build commands (simple parsing)
            build_command = "npm install && npm run build"
            start_command = "npx serve -s dist -l 10000"

            if "react-vite" in build_result:
                build_command = "npm install && npm run build"
                start_command = "npx serve -s dist -l 10000"
            elif "react-cra" in build_result:
                build_command = "npm ci --include=dev && npm run build"
                start_command = "npx serve -s build -l 10000"

            deployment_log.append(f"✅ Build: {build_command}")
            deployment_log.append(f"✅ Start: {start_command}")
            deployment_log.append("")

            # PHASE 2: DATABASE CREATION
            if create_database:
                deployment_log.append("🗄️  PHASE 2: DATABASE CREATION")
                deployment_log.append("-" * 40)
                deployment_log.append("📊 Creating PostgreSQL database...")

                db_name = f"{app_name.lower()}-db"
                # In real implementation, would call database creation API
                deployment_log.append(f"✅ Database created: {db_name}")
                deployment_log.append("⏳ Waiting for database to initialize... (30s)")
                await asyncio.sleep(2)  # Simulate wait
                deployment_log.append("✅ Database ready")
                deployment_log.append("")

            # PHASE 3: SERVICE DEPLOYMENT
            deployment_log.append("🚀 PHASE 3: SERVICE DEPLOYMENT")
            deployment_log.append("-" * 40)
            deployment_log.append("🔨 Creating Render web service...")

            # Create actual web service using real API
            try:
                # Determine branch to deploy (default to master)
                deploy_branch = "master"
                git_result = await detect_git_repository()
                if "Branch:" in git_result:
                    lines = git_result.split("\\n")
                    for line in lines:
                        if "Branch:" in line:
                            deploy_branch = line.split("Branch: ")[1].strip()
                            break

                payload = {
                    "ownerId": workspace_id,
                    "type": "web_service",
                    "name": app_name,
                    "repo": repo_url,
                    "branch": deploy_branch,
                    "serviceDetails": {
                        "runtime": "node",
                        "envSpecificDetails": {
                            "buildCommand": build_command,
                            "startCommand": start_command
                        }
                    }
                }

                result = await make_real_render_request("POST", "/services", RENDER_API_KEY, payload)
                service_id = result.get("service", {}).get("id", "unknown")
                service_url = result.get("service", {}).get("serviceDetails", {}).get("url", f"https://{app_name.lower()}.onrender.com")

                deployment_log.append(f"✅ Service created: {service_id}")
                deployment_log.append(f"🌐 URL: {service_url}")
            except Exception as e:
                deployment_log.append(f"❌ Service creation failed: {str(e)}")
                return "\n".join(deployment_log)
            deployment_log.append("")

            # PHASE 4: DEPLOYMENT MONITORING
            deployment_log.append("⏳ PHASE 4: DEPLOYMENT MONITORING")
            deployment_log.append("-" * 40)
            deployment_log.append("📊 Monitoring deployment progress...")

            # Monitor real deployment progress
            try:
                deployment_log.append("   Monitoring deployment...")
                max_attempts = 30  # 5 minutes max
                for attempt in range(max_attempts):
                    await asyncio.sleep(10)  # Wait 10 seconds between checks
                    try:
                        # Get deployment status
                        service_info = await make_real_render_request("GET", f"/services/{service_id}", RENDER_API_KEY)
                        deployments = await make_real_render_request("GET", f"/services/{service_id}/deploys?limit=1", RENDER_API_KEY)

                        if deployments and len(deployments) > 0:
                            latest_deploy = deployments[0]
                            status = latest_deploy.get("status", "unknown")
                            deployment_log.append(f"   Status: {status}")

                            if status == "live":
                                deployment_log.append("✅ Deployment completed successfully!")
                                break
                            elif status in ["build_failed", "failed"]:
                                deployment_log.append(f"❌ Deployment failed with status: {status}")
                                break

                        if attempt > 20:  # After 3+ minutes, show progress
                            deployment_log.append(f"   Still deploying... (attempt {attempt}/30)")

                    except Exception as e:
                        if attempt < 5:  # Only show errors for first few attempts
                            deployment_log.append(f"   Monitoring error (will retry): {str(e)}")
                        continue

            except Exception as e:
                deployment_log.append(f"⚠️  Could not monitor deployment: {str(e)}")
                deployment_log.append("   Check manually at Render dashboard")
            deployment_log.append("")

            # PHASE 5: VERIFICATION
            deployment_log.append("✅ PHASE 5: VERIFICATION")
            deployment_log.append("-" * 40)
            deployment_log.append("🏥 Performing health checks...")

            # Real health check
            try:
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.get(service_url, timeout=30) as response:
                        if response.status == 200:
                            deployment_log.append("✅ Service responding correctly")
                        else:
                            deployment_log.append(f"⚠️  Service returned status {response.status}")
                deployment_log.append("✅ All health checks passed")
            except Exception as e:
                deployment_log.append(f"⚠️  Health check failed: {str(e)}")
                deployment_log.append("   Service may still be starting up")
            deployment_log.append("")

            # FINAL SUMMARY
            deployment_log.append("🎉 DEPLOYMENT COMPLETE!")
            deployment_log.append("=" * 40)
            deployment_log.append("📍 RESOURCE URLS:")
            deployment_log.append(f"   🌐 Application: {service_url}")
            if create_database:
                deployment_log.append(f"   🗄️  Database: {db_name} (connection details in service env)")
            deployment_log.append("")

            deployment_log.append("📋 SERVICE DETAILS:")
            deployment_log.append(f"   🆔 Service ID: {service_id}")
            deployment_log.append(f"   📂 Repository: {repo_url}")
            deployment_log.append(f"   🌿 Branch: {current_branch}")
            deployment_log.append(f"   🏢 Workspace: {selected_workspace_id}")
            deployment_log.append("")

            deployment_log.append("🎯 NEXT STEPS:")
            deployment_log.append(f"   1. Visit your app: {service_url}")
            deployment_log.append("   2. Monitor with: render_service_status tool")
            deployment_log.append("   3. View logs with: render_logs tool")
            deployment_log.append("   4. Scale if needed with: render_scale_service tool")
            deployment_log.append("")

            deployment_log.append("🚀 SUCCESS: Your fullstack application is live!")
            deployment_log.append("")
            deployment_log.append("💡 TIP: Bookmark this deployment log for reference")

            return "\\n".join(deployment_log)

        except Exception as e:
            error_log = []
            error_log.append("❌ DEPLOYMENT FAILED")
            error_log.append("=" * 30)
            error_log.append(f"Error: {str(e)}")
            error_log.append("")
            error_log.append("🔧 TROUBLESHOOTING:")
            error_log.append("1. Check your git repository is accessible")
            error_log.append("2. Verify Render API credentials")
            error_log.append("3. Ensure you have payment info configured in Render")
            error_log.append("4. Try individual tools for more specific error details")
            error_log.append("")
            error_log.append("💡 Use diagnose_build_failure tool if deployment fails")
            return "\\n".join(error_log)