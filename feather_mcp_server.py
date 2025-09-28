#!/usr/bin/env python3
"""
Feather MCP Server - Clean, Modular Architecture

Each tool is focused, small, and leverages shared utilities.
Follows the "sharpen the axe 90%" principle with proper separation of concerns.
"""

import os
import sys
import json
import logging
import asyncio
import subprocess
from datetime import datetime
from typing import Dict, Any

# Add utils to path
sys.path.append(os.path.dirname(__file__))

# Configure logging FIRST
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("feather")

from fastmcp import FastMCP
from utils.render_client import RenderClient
from utils.llm_client import LLMClient
from dotenv import load_dotenv

# Load environment and initialize
logger.info("Loading environment variables...")
load_result = load_dotenv()
logger.info(f"dotenv load result: {load_result}")

# DEBUG: Check if environment variables are loaded
import os
llm_api_key = os.getenv('LLM_API_KEY')
logger.info(f"LLM_API_KEY loaded: {'YES' if llm_api_key else 'NO'}")
if llm_api_key:
    logger.info(f"API key starts with: {llm_api_key[:10]}...")
else:
    logger.error("LLM_API_KEY not found in environment")
    # Try to load .env explicitly
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    logger.info(f"Trying to load .env from: {env_path}")
    logger.info(f".env file exists: {os.path.exists(env_path)}")

    if os.path.exists(env_path):
        from dotenv import load_dotenv
        load_dotenv(env_path)
        llm_api_key = os.getenv('LLM_API_KEY')
        logger.info(f"After explicit load - LLM_API_KEY: {'YES' if llm_api_key else 'NO'}")
    else:
        logger.error("Could not find .env file")

mcp = FastMCP("feather")


# ============================================================================
# VALIDATION FUNCTIONS (Production Quality Assurance)
# ============================================================================

def _validate_generated_code(code: Dict[str, Any]) -> Dict[str, Any]:
    """Validate generated Flask code for production readiness"""
    warnings = []

    # Check requirements.txt
    requirements = code.get('requirements_txt', '')
    required_deps = ['gunicorn', 'Flask', 'Werkzeug', 'Flask-SQLAlchemy']
    for dep in required_deps:
        if dep not in requirements:
            warnings.append(f"Missing critical dependency: {dep}")

    # Check app.py
    app_py = code.get('app_py', '')
    if 'app.route' not in app_py:
        warnings.append("No routes found in app.py")
    if 'gunicorn' not in requirements and 'if __name__' in app_py:
        warnings.append("Development server config without gunicorn")
    if 'models import' not in app_py and 'from models' not in app_py:
        warnings.append("Models not imported in app.py")

    # Check templates
    templates = code.get('html_templates', {})
    if not templates:
        warnings.append("No HTML templates generated")
    elif 'base.html' not in templates:
        warnings.append("Missing base.html template")

    # Check models
    models = code.get('models_py', '')
    if not models or 'class' not in models:
        warnings.append("No database models defined")

    return {
        'all_passed': len(warnings) == 0,
        'warnings': '\n'.join(f"• {w}" for w in warnings) if warnings else "None"
    }


# ============================================================================
# TOOL 1: ANALYZE APP REQUIREMENTS (Clean & Focused)
# ============================================================================

@mcp.tool()
async def analyze_app_requirements(user_prompt: str) -> str:
    """
    Enhanced Framework-Aware Planner Tool

    Analyzes user prompt and creates a comprehensive creative prompt for the code generation LLM.
    Always uses the fixed stack: Flask + PostgreSQL + HTML/CSS/JS for Render deployment.

    Args:
        user_prompt: Natural language app description

    Returns:
        Framework-aware creative prompt and technical specifications
    """
    try:
        llm = LLMClient()

        # PRODUCTION-READY enhanced prompt with mandatory requirements
        enhanced_prompt = """
        You are an expert Flask application architect. Create a PRODUCTION-READY creative prompt for code generation.

        USER REQUEST: """ + user_prompt + """

        MANDATORY TECHNICAL STACK (NEVER CHANGE):
        - Backend: Flask 2.3+ + Python 3.12.7 EXACTLY (NO other Python versions)
        - Database: PostgreSQL (with SQLite fallback)
        - Frontend: HTML + Bootstrap 5 + JavaScript
        - Deployment: Render platform with gunicorn

        CRITICAL PRODUCTION REQUIREMENTS (FAILURE IS NOT ACCEPTABLE):

        ⚠️  CRITICAL: PYTHON VERSION REQUIREMENT ⚠️
        - MUST create .python-version file with content "3.12.7" (no other version)
        - Python 3.13+ causes SQLAlchemy compatibility errors and deployment failures
        - This is NON-NEGOTIABLE - always use Python 3.12.7 exactly

        ⚠️  IMPORTANT: THE LLM MUST MANUALLY WRITE ALL CODE FILES ⚠️
        - The MCP tools DO NOT generate code automatically
        - The LLM must create every file: app.py, models.py, requirements.txt, templates/*.html
        - Write complete, working code for each file before using deployment tools
        - Tools only handle deployment/management, NOT code generation

        ⚠️  CRITICAL: DATABASE INITIALIZATION MUST BE WRITTEN MANUALLY ⚠️
        - The LLM must write db.create_all() code in app.py startup
        - Database tables will NOT exist unless explicitly created in code
        - Add proper database initialization with error handling
        - Include seed/default data creation in the initialization code

        🚀 DEPLOY-FIRST WORKFLOW (NO LOCAL TESTING):
        - NO local requirements installation - expensive and unnecessary
        - NO local Flask server testing - deployment environment handles all validation
        - Deploy-first approach - let production environment be the testing ground
        - User feedback driven development - real issues come from actual usage, not synthetic tests
        - Workflow: generate code → deploy to production → user reports issues → iterate
        - Trust the deployment process - if code follows standards, it will work

        1. COMPLETE DEPENDENCIES (requirements.txt MUST include):
           - Flask==2.3.3 (tested compatibility)
           - Werkzeug==2.3.8 (explicit version to prevent conflicts)
           - SQLAlchemy==2.0.21 (pure SQLAlchemy, NOT Flask-SQLAlchemy)
           - psycopg2-binary==2.9.7 (Python 3.12 compatible)
           - gunicorn==21.2.0 (ESSENTIAL for deployment)

        2. FUNCTIONAL FLASK APPLICATION (app.py MUST have):
           - Pure SQLAlchemy setup with create_engine and SessionLocal
           - Session management with try/finally blocks
           - Database initialization with default/seed data (CRITICAL)
           - WORKING ROUTES (not just error handlers)
           - Database table creation with Base.metadata.create_all()
           - Environment variables with fallbacks
           - SECRET_KEY configuration

        3. COMPLETE TEMPLATE SET (ALL referenced templates MUST exist):
           - base.html with Bootstrap 5 CDN
           - All templates referenced in routes
           - Proper Jinja2 syntax and inheritance
           - Responsive navigation with return/home buttons on all pages
           - Consistent navigation allowing users to return to main page
           - VISUAL DESIGN: Use colored backgrounds with textures, NOT plain white
           - Apply gradients, patterns, or subtle textures for professional appearance
           - Ensure good contrast and readability with background styling

        4. PRODUCTION DATABASE MODELS (models.py MUST have):
           - Pure SQLAlchemy with declarative_base() (NOT Flask-SQLAlchemy)
           - Complete models inheriting from Base
           - Proper relationships with back_populates
           - DateTime fields with default values
           - __repr__ methods for debugging

        5. DEPLOYMENT VALIDATION:
           - .python-version file with 3.12.7 EXACTLY (CRITICAL - Python 3.13+ breaks SQLAlchemy)
           - NEVER use Python 3.13+ - causes SQLAlchemy compatibility errors
           - SQLite fallback: 'sqlite:///app.db'
           - Database initialization function that creates default users/data
           - Health check endpoint
           - Proper error handling with rollback

        Analyze the user request and return a JSON structure with complete technical specifications.

        Output ONLY valid JSON in this exact format:
        {{
          "app_name": "kebab-case-app-name",
          "description": "Brief description of the application",
          "database_models": [
            {{
              "name": "ModelName",
              "table_name": "table_name",
              "fields": [
                {{"name": "id", "type": "Integer", "constraints": "primary_key=True"}},
                {{"name": "field_name", "type": "String(100)", "constraints": "nullable=False"}}
              ],
              "relationships": ["belongs_to User", "has_many Items"]
            }}
          ],
          "api_endpoints": [
            {{
              "path": "/",
              "method": "GET",
              "description": "Homepage with overview",
              "template": "index.html",
              "model_operations": ["read"]
            }}
          ],
          "templates_needed": [
            {{
              "name": "base.html",
              "purpose": "Bootstrap base layout with navigation"
            }},
            {{
              "name": "index.html",
              "purpose": "Homepage with app overview"
            }}
          ],
          "required_packages": [
            "Flask==2.3.3",
            "Werkzeug==2.3.8",
            "SQLAlchemy==2.0.21",
            "psycopg2-binary==2.9.7",
            "gunicorn==21.2.0"
          ],
          "deployment_config": {{
            "python_version": "3.12.7",
            "start_command": "gunicorn app:app",
            "environment_variables": ["DATABASE_URL", "SECRET_KEY"]
          }}
        }}
        """

        # Get structured analysis from LLM
        analysis_result = await llm.analyze_requirements(enhanced_prompt)

        # Parse the analysis into clean JSON structure
        import json
        try:
            # Try to extract JSON from the analysis
            if '{' in analysis_result and '}' in analysis_result:
                start = analysis_result.find('{')
                end = analysis_result.rfind('}') + 1
                json_part = analysis_result[start:end]
                parsed_data = json.loads(json_part)
            else:
                # Fallback structure if no JSON found
                parsed_data = {
                    "app_name": user_prompt.lower().replace(' ', '-')[:30],
                    "description": user_prompt,
                    "database_models": [],
                    "api_endpoints": [],
                    "templates_needed": [],
                    "required_packages": [
                        "Flask==2.3.3",
                        "Werkzeug==2.3.8",
                        "SQLAlchemy==2.0.21",
                        "psycopg2-binary==2.9.7",
                        "gunicorn==21.2.0"
                    ]
                }
        except:
            # Emergency fallback
            parsed_data = {
                "app_name": "flask-app",
                "description": user_prompt,
                "database_models": [],
                "api_endpoints": [],
                "templates_needed": [],
                "required_packages": [
                    "Flask==2.3.3",
                    "Werkzeug==2.3.8",
                    "SQLAlchemy==2.0.21",
                    "psycopg2-binary==2.9.7",
                    "gunicorn==21.2.0"
                ]
            }

        # Return clean JSON specifications for Claude to use
        return json.dumps(parsed_data, indent=2)

    except Exception as e:
        return f"❌ Enhanced planning failed: {str(e)}"


# ============================================================================
# TOOL 2: WRITE FLASK FILES (Clean & Focused)
# ============================================================================

@mcp.tool()
async def write_flask_files(app_py: str, models_py: str = "", requirements_txt: str = "", templates: str = "{}") -> str:
    """
    DUMB FILE WRITER: Takes actual Flask code from Claude and writes files to disk.

    This tool does NO intelligent processing - just mechanical file operations.
    Claude generates the actual Flask code, this tool just saves it.

    Args:
        app_py: Complete Flask application code
        models_py: SQLAlchemy models code (optional)
        requirements_txt: Dependencies list (optional)
        templates: JSON string of templates {"filename.html": "content"}

    Returns:
        File creation status and git push result
    """
    try:
        import os
        import json

        # Ensure we're in the test directory
        test_dir = os.path.join(os.getcwd(), 'test')
        os.makedirs(test_dir, exist_ok=True)
        os.chdir(test_dir)

        # Write app.py (add SQLite fallback if not present)
        if 'sqlite:///' not in app_py and 'DATABASE_URL' in app_py:
            app_content = app_py.replace(
                "os.environ.get('DATABASE_URL')",
                "os.environ.get('DATABASE_URL', 'sqlite:///app.db')"
            )
        else:
            app_content = app_py

        with open('app.py', 'w') as f:
            f.write(app_content)

        # Write models.py if provided
        if models_py.strip():
            with open('models.py', 'w') as f:
                f.write(models_py)

        # Write requirements.txt if provided
        if requirements_txt.strip():
            with open('requirements.txt', 'w') as f:
                f.write(requirements_txt)

        # Create templates directory and files
        os.makedirs('templates', exist_ok=True)
        try:
            template_dict = json.loads(templates)
            for filename, content in template_dict.items():
                with open(f'templates/{filename}', 'w') as f:
                    f.write(content)
        except:
            pass  # If no templates or invalid JSON, skip

        # Create static directory
        os.makedirs('static', exist_ok=True)

        # Create empty SQLite database file
        with open('app.db', 'w') as f:
            f.write('')

        # Count created files
        file_count = 1  # app.py always created
        file_count += 1 if models_py.strip() else 0
        file_count += 1 if requirements_txt.strip() else 0
        template_count = 0
        try:
            template_dict = json.loads(templates)
            template_count = len(template_dict)
        except:
            template_count = 0
        file_count += template_count
        file_count += 1  # app.db

        # Auto git push
        try:
            # Add all files
            await asyncio.create_subprocess_exec('git', 'add', '.')

            # Commit with message
            await asyncio.create_subprocess_exec('git', 'commit', '-m', 'Add generated Flask app files')

            # Push to origin
            push_process = await asyncio.create_subprocess_exec(
                'git', 'push', 'origin', 'main',
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            stdout, stderr = await push_process.communicate()

            if push_process.returncode == 0:
                git_status = "✅ Pushed to GitHub successfully"
            else:
                git_status = f"⚠️ Git push failed: {stderr.decode()}"

        except Exception as e:
            git_status = f"⚠️ Git push failed: {str(e)}"

        return f"✅ FILES WRITTEN & PUSHED SUCCESSFULLY\n\nCreated {file_count} files:\n• app.py (with SQLite fallback)\n• models.py\n• requirements.txt\n• templates/ ({template_count} files)\n• static/ (0 files)\n• app.db (SQLite placeholder)\n\n{git_status}\n\n🚀 Ready for deployment with deploy_flask_app!"
    except Exception as e:
        return f"❌ File writing failed: {str(e)}"


# ============================================================================
# TOOL 4: DEPLOY FLASK APP (Clean & Focused)
# ============================================================================

@mcp.tool()
async def deploy_flask_app(github_repo_url: str, app_name: str = "") -> str:
    """
    DUMB DEPLOYER: Takes GitHub repo URL and deploys to Render with PostgreSQL.

    This tool does NO intelligent processing - just mechanical deployment operations.
    Claude provides the repo URL, this tool just deploys it.

    Args:
        github_repo_url: GitHub repository URL with Flask app code
        app_name: Optional app name (auto-generated if not provided)

    Returns:
        Deployment status with live URLs
    """
    try:
        # Validate GitHub URL
        if not github_repo_url.startswith('https://github.com/'):
            return "❌ Invalid GitHub URL. Must start with 'https://github.com/' and be a real repository.\n\nExample: https://github.com/yourusername/recipe-sharing-app\n\nPlease create a GitHub repository, push your Flask code, and provide the actual repository URL."

        if github_repo_url.endswith('.git'):
            github_repo_url = github_repo_url[:-4]  # Remove .git suffix if present

        if '/example/' in github_repo_url or github_repo_url.count('/') < 4:
            return "❌ Please provide a REAL GitHub repository URL, not an example.\n\nSteps:\n1. Create a new GitHub repository\n2. Push your Flask app code to it\n3. Use that repository URL here\n\nExample: https://github.com/yourusername/my-flask-app"

        render = RenderClient()

        # Get current working directory for build context
        current_dir = os.getcwd()
        # Check if we need to report the test subdirectory
        if os.path.exists(os.path.join(current_dir, 'test')):
            test_dir = os.path.join(current_dir, 'test')
            if os.path.exists(os.path.join(test_dir, 'app.py')):
                current_dir = test_dir

        # Include directory info in deployment status for LLM visibility
        directory_info = f"Working directory: {current_dir}"

        # Generate app name if not provided
        if not app_name:
            app_name = f"flask-app-{int(datetime.now().timestamp())}"

        # Create database
        db_result = await render.create_database(app_name)
        database_id = db_result.get('id')

        # Validate database creation
        if not database_id:
            return f"❌ DATABASE CREATION FAILED!\n\nDatabase result: {db_result}\n\nPossible issues:\n- Render API limits reached\n- Invalid database configuration\n- Authentication problems"

        # Get connection info
        db_connection = await render.get_database_connection(database_id)
        internal_url = db_connection.get('internalConnectionString')

        # Validate database connection
        if not internal_url:
            return f"❌ DATABASE CONNECTION FAILED!\n\nDatabase ID: {database_id}\nConnection result: {db_connection}\n\nCannot get database URL for service deployment."

        # Create service
        service_result = await render.create_service(app_name, github_repo_url, internal_url)
        # Extract service ID - it's nested in service.id, not top-level id
        service_id = service_result.get('service', {}).get('id') or service_result.get('id')

        # Validate service creation
        if not service_id:
            return f"❌ SERVICE CREATION FAILED!\n\nDatabase created successfully (ID: {database_id})\nBut web service creation failed.\n\nService result: {service_result}\n\nPossible issues:\n- Repository might not be accessible\n- Build configuration problems\n- Render API limitations\n\nCheck your repository and try again."

        app_url = f"https://{app_name}.onrender.com"
        dashboard_url = f"https://dashboard.render.com/web/{service_id}"

        return f"✅ DEPLOYMENT COMPLETE!\n\n{directory_info}\nApp URL: {app_url}\nDashboard: {dashboard_url}\nService ID: {service_id}\nDatabase ID: {database_id}\n\n🔍 VALIDATION REQUIRED:\nDO NOT test locally. Wait for deployment validation using runtime logs.\n\nUse these tools to verify deployment:\n• get_runtime_logs('{service_id}') - Check for startup errors\n• debug_flask_app('{service_id}') - Get health report\n\nThe deployment environment will reveal any real issues through runtime logs."

    except Exception as e:
        return f"❌ Deployment failed: {str(e)}"


# ============================================================================
# TOOL 4: DEBUG FLASK APP (Clean & Focused)
# ============================================================================

@mcp.tool()
async def debug_flask_app(service_id: str) -> str:
    """
    Debug and monitor deployed Flask application.

    Args:
        service_id: Render service ID

    Returns:
        Debugging report with actionable insights
    """
    try:
        render = RenderClient()

        # Get service info
        service = await render.get_service(service_id)
        service_name = service.get('name', 'Unknown')
        service_status = service.get('status', 'unknown')

        # Analyze logs
        logs = await render.get_logs(service_id, limit=20)
        error_count = sum(1 for log in logs if 'error' in log.get('message', '').lower())

        # Generate report
        health = "🟢 Healthy" if service_status == 'available' and error_count == 0 else "🔴 Issues detected"

        report = [
            f"🔧 DEBUG REPORT: {service_name}",
            f"Status: {service_status}",
            f"Health: {health}",
            f"Recent logs: {len(logs)}",
            f"Errors: {error_count}",
            f"Dashboard: https://dashboard.render.com/web/{service_id}"
        ]

        if error_count > 0:
            report.append("\n🚨 Recent errors found - check dashboard for details")

        return "\n".join(report)

    except Exception as e:
        return f"❌ Debug failed: {str(e)}"


# ============================================================================
# TOOL: GET RUNTIME LOGS (Essential for Debugging)
# ============================================================================
@mcp.tool()
async def get_runtime_logs(service_id: str, limit: int = 50) -> str:
    """
    Get runtime logs from a deployed Flask service for debugging.

    Args:
        service_id: Render service ID
        limit: Number of recent log entries to retrieve (default: 50)

    Returns:
        Recent runtime logs with timestamps
    """
    try:
        render = RenderClient()

        # Get service info first
        service = await render.get_service(service_id)
        service_name = service.get('name', 'Unknown')

        # Get logs
        logs = await render.get_logs(service_id, limit=limit)

        if not logs:
            return f"📝 No logs found for service {service_name} ({service_id})"

        # Format logs for readability
        formatted_logs = []
        formatted_logs.append(f"📝 RUNTIME LOGS: {service_name}")
        formatted_logs.append(f"Service ID: {service_id}")
        formatted_logs.append(f"Recent entries: {len(logs)}")
        formatted_logs.append("=" * 60)

        # Show most recent logs first
        for log in logs[-limit:]:
            timestamp = log.get('timestamp', 'No timestamp')
            message = log.get('message', 'No message')
            formatted_logs.append(f"{timestamp} {message}")

        return "\n".join(formatted_logs)

    except Exception as e:
        return f"❌ Failed to get runtime logs: {str(e)}"


# ============================================================================
# TOOL 5: DISCOVER WORKSPACES (Clean & Focused)
# ============================================================================

@mcp.tool()
async def discover_workspaces() -> str:
    """
    Discover Render workspaces and recommend OWNER_ID.

    Returns:
        Workspace information with setup instructions
    """
    try:
        render = RenderClient()
        services = await render.get_services()

        # Group by workspace
        workspaces = {}
        for service in services:
            owner_id = service.get('ownerId')
            if owner_id:
                workspaces[owner_id] = workspaces.get(owner_id, 0) + 1

        if not workspaces:
            return "❌ No workspaces found. Check RENDER_API_KEY."

        # Find most active workspace
        recommended = max(workspaces.items(), key=lambda x: x[1])

        result = [
            "🔍 WORKSPACE DISCOVERY",
            f"Found {len(workspaces)} workspace(s)\n"
        ]

        for i, (owner_id, count) in enumerate(sorted(workspaces.items(), key=lambda x: x[1], reverse=True), 1):
            prefix = "⭐" if owner_id == recommended[0] else "📁"
            result.append(f"{prefix} Workspace {i}: {owner_id} ({count} services)")

        result.extend([
            f"\n🎯 RECOMMENDED:",
            f"OWNER_ID={recommended[0]}",
            "\nAdd this to your .env file!"
        ])

        return "\n".join(result)

    except Exception as e:
        return f"❌ Discovery failed: {str(e)}"


# ============================================================================
# SERVICE MANAGEMENT TOOLS (Clean & Focused)
# ============================================================================

@mcp.tool()
async def list_services() -> str:
    """List all services in current workspace."""
    try:
        render = RenderClient()
        # Get web services
        services_response = await render.get_services()

        services = []
        if isinstance(services_response, list):
            for item in services_response:
                if 'service' in item:
                    services.append({**item['service'], 'type': 'web_service'})
                else:
                    services.append({**item, 'type': 'web_service'})
        else:
            services = [{**services_response, 'type': 'web_service'}] if services_response else []

        # Get PostgreSQL databases
        try:
            databases_response = await render.get_postgres_databases()
            if isinstance(databases_response, list):
                for item in databases_response:
                    # Handle nested structure: {"postgres": {...}}
                    if 'postgres' in item:
                        db = item['postgres']
                        # Extract ownerId from nested owner object
                        owner_id = db.get('owner', {}).get('id', 'Unknown') if isinstance(db.get('owner'), dict) else 'Unknown'
                        services.append({
                            'name': db.get('name', db.get('databaseName', 'Unknown')),  # Use 'name' field for display
                            'id': db.get('id', 'Unknown'),
                            'status': db.get('status', 'available'),
                            'ownerId': owner_id,
                            'type': 'postgres'
                        })
                    else:
                        services.append({**item, 'type': 'postgres'})
            elif databases_response:
                services.append({**databases_response, 'type': 'postgres'})
        except Exception:
            # Continue even if database fetch fails
            pass

        # Filter by current workspace
        workspace_services = [s for s in services if s.get('ownerId') == render.owner_id]

        if not workspace_services:
            return f"📋 No services in workspace {render.owner_id}"

        result = [f"📋 SERVICES ({len(workspace_services)} total)\n"]

        for i, service in enumerate(workspace_services, 1):
            status = service.get('status', 'unknown')
            name = service.get('name', 'Unknown')
            service_id = service.get('id', 'Unknown')
            service_type = service.get('type', 'unknown')

            # Different icons for different service types
            if service_type == 'postgres':
                icon = "🗄️" if status == 'available' else "🔴"
                type_label = "DB"
            else:
                icon = "🟢" if status == 'available' else "🔴"
                type_label = "WEB"

            result.append(f"{i}. {icon} {name} ({service_id}) [{type_label}]")

        return "\n".join(result)

    except Exception as e:
        return f"❌ Listing failed: {str(e)}"


@mcp.tool()
async def restart_service(service_id: str) -> str:
    """Restart a service."""
    try:
        render = RenderClient()
        service = await render.get_service(service_id)
        await render.restart_service(service_id)

        return f"🔄 Restart initiated for {service.get('name', service_id)}"

    except Exception as e:
        return f"❌ Restart failed: {str(e)}"


@mcp.tool()
async def delete_service(service_id: str, confirmation: str) -> str:
    """Delete a service (requires confirmation='DELETE')."""
    if confirmation != "DELETE":
        return "❌ Safety check: Set confirmation='DELETE' to proceed"

    try:
        render = RenderClient()

        # Determine if this is a PostgreSQL database (starts with 'dpg-') or web service
        if service_id.startswith('dpg-'):
            # PostgreSQL database
            await render.delete_postgres_database(service_id)
            return f"💀 Deleted PostgreSQL database: {service_id}"
        else:
            # Web service
            service = await render.get_service(service_id)
            await render.delete_service(service_id)
            return f"💀 Deleted service: {service.get('name', service_id)}"

    except Exception as e:
        return f"❌ Deletion failed: {str(e)}"


# ============================================================================
# SERVER STARTUP
# ============================================================================

if __name__ == "__main__":
    # Validate environment
    required_vars = ["RENDER_API_KEY", "OWNER_ID", "LLM_API_KEY"]
    missing = [var for var in required_vars if not os.getenv(var)]

    if missing:
        logger.error(f"❌ Missing environment variables: {', '.join(missing)}")
        sys.exit(1)

    logger.info("🪶 Feather MCP Server (Clean Architecture)")
    logger.info(f"📊 Workspace: {os.getenv('OWNER_ID')}")
    logger.info("🛠️ Tools: 8 focused tools with shared utilities")

    mcp.run()