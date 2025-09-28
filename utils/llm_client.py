#!/usr/bin/env python3
"""
LLM Client - Shared Utility

Handles all LLM API interactions with proper configuration.
Uses LLM_API_KEY from environment variables - NO hardcoded values.
"""

import os
import json
import aiohttp
from typing import Dict, Any, Optional


class LLMClient:
    """Centralized LLM API client"""

    def __init__(self):
        from dotenv import load_dotenv

        # Try multiple ways to get the API key
        print("DEBUG: Trying to load API key...")

        # Method 1: Direct environment check
        self.api_key = os.getenv('LLM_API_KEY')
        print(f"DEBUG: Method 1 (direct env): {'Found' if self.api_key else 'Not found'}")

        # Method 2: Load .env from default location
        if not self.api_key:
            load_dotenv()
            self.api_key = os.getenv('LLM_API_KEY')
            print(f"DEBUG: Method 2 (load_dotenv): {'Found' if self.api_key else 'Not found'}")

        # Method 3: Load .env from current working directory
        if not self.api_key:
            env_path = os.path.join(os.getcwd(), '.env')
            print(f"DEBUG: Method 3 trying path: {env_path}")
            print(f"DEBUG: .env exists at cwd: {os.path.exists(env_path)}")
            load_dotenv(env_path)
            self.api_key = os.getenv('LLM_API_KEY')
            print(f"DEBUG: Method 3 (cwd .env): {'Found' if self.api_key else 'Not found'}")

        self.api_url = os.getenv('LLM_API_URL', 'https://api.openai.com/v1/chat/completions')
        self.model = os.getenv('LLM_MODEL', 'gpt-3.5-turbo')

        print(f"DEBUG: Final API key status: {'YES' if self.api_key else 'NO'}")
        if self.api_key:
            print(f"DEBUG: API key starts with: {self.api_key[:10]}...")

        if not self.api_key:
            raise ValueError("LLM_API_KEY environment variable required")

    async def analyze_requirements(self, user_prompt: str) -> Dict[str, Any]:
        """Analyze user prompt and return structured requirements"""
        system_prompt = """You are an expert Flask developer and system architect.
Analyze user prompts and create COMPLETE technical specifications following the AGREED FRAMEWORK.

🎯 MANDATORY FRAMEWORK - NO EXCEPTIONS:
- Flask web application with PostgreSQL database
- SQLAlchemy ORM with Flask-Migrate
- Bootstrap CSS framework for UI
- Render cloud deployment with database integration
- Gunicorn WSGI server
- Environment variable configuration

📋 REQUIRED JSON FORMAT (MUST FOLLOW EXACTLY):
{
  "app_name": "descriptive-app-name",
  "description": "Brief app description",
  "database_models": [
    {
      "name": "ModelName",
      "table_name": "model_names",
      "fields": [
        {"name": "id", "type": "db.Integer", "constraints": "primary_key=True"},
        {"name": "field_name", "type": "db.String(100)|db.Integer|db.DateTime|db.Text|db.Boolean", "constraints": "nullable=False"}
      ],
      "relationships": [
        {"type": "one_to_many|many_to_one|many_to_many", "model": "RelatedModel", "description": "relationship purpose"}
      ]
    }
  ],
  "api_endpoints": [
    {
      "path": "/", "method": "GET", "description": "Homepage with app overview", "template": "index.html"
    },
    {
      "path": "/api/endpoint", "method": "POST", "description": "API functionality", "returns": "JSON response"
    }
  ],
  "templates_needed": [
    {"name": "base.html", "purpose": "Bootstrap base layout"},
    {"name": "index.html", "purpose": "Homepage"},
    {"name": "model_list.html", "purpose": "List view"}
  ],
  "required_packages": [
    "Flask==2.3.3",
    "Flask-SQLAlchemy==3.0.5",
    "Flask-Migrate==4.0.5",
    "psycopg2-binary==2.9.7",
    "gunicorn==21.2.0"
  ],
  "environment_variables": [
    {"name": "DATABASE_URL", "description": "PostgreSQL connection string"},
    {"name": "SECRET_KEY", "description": "Flask session secret"},
    {"name": "FLASK_ENV", "description": "Environment (production)"}
  ],
  "deployment_config": {
    "build_command": "pip install -r requirements.txt",
    "start_command": "gunicorn app:app",
    "database_required": true,
    "port": 10000
  }
}

🔧 CONSISTENCY REQUIREMENTS:
- Always use PostgreSQL with SQLAlchemy
- Always include id field as primary key
- Always use Bootstrap for styling
- Always include base.html template
- Always use environment variables (no hardcoded values)
- Always structure for Render deployment

Analyze the user's prompt and return the JSON specification following the AGREED FRAMEWORK:"""

        return await self._make_request(system_prompt, f"User prompt: '{user_prompt}'")

    async def generate_code(self, specifications: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Flask application code from specifications"""
        system_prompt = """You are an expert Flask developer implementing the AGREED FRAMEWORK.
Generate a complete, production-ready Flask application following EXACT specifications.

🎯 MANDATORY FRAMEWORK - MUST FOLLOW:
- Flask app.py with SQLAlchemy models
- PostgreSQL database with environment variables
- Bootstrap CSS framework (CDN)
- Gunicorn ready (app:app)
- Environment variable configuration
- Migration support with Flask-Migrate

📋 REQUIRED OUTPUT FORMAT (EXACT JSON):
{
  "app_py": "complete Flask app.py file with routes, database config, and error handling",
  "models_py": "complete SQLAlchemy models with relationships and methods",
  "requirements_txt": "exact package versions from specifications",
  "sql_schema": "complete PostgreSQL CREATE statements with indexes",
  "html_templates": {
    "base.html": "Bootstrap base template with navbar and responsive design",
    "index.html": "homepage extending base.html",
    "additional_template.html": "other templates as needed"
  },
  "static_files": {
    "style.css": "custom CSS to complement Bootstrap"
  },
  "config_py": "Flask configuration class with environment variables"
}

🔧 CODE REQUIREMENTS:
- app.py MUST use os.environ for DATABASE_URL, SECRET_KEY
- models.py MUST include __repr__ methods and proper relationships
- base.html MUST use Bootstrap 5 CDN and responsive navbar
- requirements.txt MUST match specifications exactly
- All templates MUST extend base.html
- Include proper error handling and logging
- Ready for Render deployment (port from env)

🚀 RENDER DEPLOYMENT READY:
- Use os.environ.get('PORT', 5000) for port
- Include if __name__ == '__main__': app.run()
- Database URL from environment
- No hardcoded values anywhere

Generate complete, working code following the AGREED FRAMEWORK:"""

        spec_text = f"Specifications: {json.dumps(specifications, indent=2)}"
        return await self._make_request(system_prompt, spec_text)

    async def _make_request(self, system_prompt: str, user_message: str, max_tokens: int = 3000) -> Dict[str, Any]:
        """Make LLM API request"""
        async with aiohttp.ClientSession() as session:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }

            payload = {
                'model': self.model,
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_message}
                ],
                'temperature': 0.1,
                'max_tokens': max_tokens
            }

            async with session.post(self.api_url, headers=headers, json=payload) as response:
                if response.status != 200:
                    raise Exception(f"LLM API error {response.status}: {await response.text()}")

                result = await response.json()
                llm_response = result['choices'][0]['message']['content']

                try:
                    return json.loads(llm_response)
                except json.JSONDecodeError:
                    raise Exception(f"LLM returned invalid JSON: {llm_response}")