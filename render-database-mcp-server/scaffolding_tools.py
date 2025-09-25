"""
Project Scaffolding Tools
Tools for creating the basic directory structure and configuration files for new projects.
"""

import os
import subprocess
from fastmcp import FastMCP

def register_scaffolding_tools(mcp: FastMCP):
    """Register scaffolding tools with FastMCP server"""

    @mcp.tool()
    def scaffold_project(project_name: str, project_type: str) -> str:
        """
        Create the basic directory structure and configuration files for a new project.

        LLM-FRIENDLY: Creates project in current working directory where LLM is operating.
        Returns absolute path so LLM knows exactly where files were created.

        Args:
            project_name: The name of the project.
            project_type: The type of the project (e.g., 'node', 'react').
        """

        try:
            # Get current working directory (where LLM is operating)
            current_dir = os.getcwd()
            project_path = os.path.join(current_dir, project_name)

            if project_type == 'node':
                # Create project directory and subdirectories
                os.makedirs(os.path.join(project_path, "src"), exist_ok=True)
                os.makedirs(os.path.join(project_path, "public"), exist_ok=True)

                # Create package.json with more comprehensive setup
                package_json = {
                    "name": project_name,
                    "version": "1.0.0",
                    "description": "A Node.js project created by LLM scaffolding",
                    "main": "server.js",
                    "scripts": {
                        "start": "node server.js",
                        "dev": "node server.js",
                        "test": "echo \"Error: no test specified\" && exit 1"
                    },
                    "dependencies": {
                        "express": "^4.18.2"
                    },
                    "engines": {
                        "node": ">=18.0.0"
                    },
                    "author": "LLM Generated",
                    "license": "MIT"
                }

                import json
                with open(os.path.join(project_path, "package.json"), 'w') as f:
                    json.dump(package_json, f, indent=2)

                # Create basic Express server
                server_js_content = '''const express = require('express');
const path = require('path');

const app = express();
const port = process.env.PORT || 3000;

// Middleware
app.use(express.json());
app.use(express.static('public'));

// Routes
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.get('/api/health', (req, res) => {
    res.json({ status: 'OK', message: 'Server is running!' });
});

// Start server
app.listen(port, () => {
    console.log(`Server running on port ${port}`);
});'''

                with open(os.path.join(project_path, "server.js"), 'w') as f:
                    f.write(server_js_content)

                # Create basic HTML file
                html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>''' + project_name + '''</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        h1 { color: #333; }
    </style>
</head>
<body>
    <h1>Welcome to ''' + project_name + '''!</h1>
    <p>Your Node.js project is ready to go.</p>
</body>
</html>'''

                with open(os.path.join(project_path, "public", "index.html"), 'w') as f:
                    f.write(html_content)

                return f"SUCCESS: Node.js project scaffolded at {project_path}\nFiles created: package.json, server.js, public/index.html\nRun: cd {project_name} && npm install && npm start"

            elif project_type == 'react':
                # Change to current directory before running npm create
                subprocess.run(["npm", "create", "vite@latest", project_name, "--", "--template", "react"],
                             cwd=current_dir, check=True)
                return f"SUCCESS: React project scaffolded at {project_path}\nRun: cd {project_name} && npm install && npm run dev"
            else:
                return f"ERROR: Invalid project type: {project_type}. Supported types: node, react"
        except Exception as e:
            return f"ERROR: Failed to scaffold project: {str(e)}\nAttempted to create at: {os.getcwd()}"

    @mcp.tool()
    def install_dependencies(project_path: str, dependencies: str, package_manager: str) -> str:
        """
        Install project dependencies using npm or pip.

        Args:
            project_path: The path to the project.
            dependencies: A space-separated string of dependencies to install.
            package_manager: The package manager to use (e.g., 'npm', 'pip').
        """

        try:
            if package_manager == 'npm':
                subprocess.run(["npm", "install", dependencies], cwd=project_path, check=True)
                return f"SUCCESS: Successfully installed npm dependencies: {dependencies}"
            elif package_manager == 'pip':
                subprocess.run(["pip", "install", dependencies], cwd=project_path, check=True)
                return f"SUCCESS: Successfully installed pip dependencies: {dependencies}"
            else:
                return f"ERROR: Invalid package manager: {package_manager}"
        except Exception as e:
            return f"ERROR: Failed to install dependencies: {str(e)}"

