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

        Args:
            project_name: The name of the project.
            project_type: The type of the project (e.g., 'node', 'react').
        """

        try:
            if project_type == 'node':
                os.makedirs(f"{project_name}/src")
                with open(f"{project_name}/package.json", 'w') as f:
                    f.write('{\n  "name": "' + project_name + '",\n  "version": "1.0.0",\n  "description": "",\n  "main": "src/index.js",\n  "scripts": {\n    "start": "node src/index.js"\n  },\n  "author": "",\n  "license": "ISC"\n}')
                with open(f"{project_name}/src/index.js", 'w') as f:
                    f.write('console.log("Hello, World!");')
                return f"SUCCESS: Successfully scaffolded Node.js project: {project_name}"
            elif project_type == 'react':
                subprocess.run(["npm", "create", "vite@latest", project_name, "--", "--template", "react"], check=True)
                return f"SUCCESS: Successfully scaffolded React project: {project_name}"
            else:
                return f"ERROR: Invalid project type: {project_type}"
        except Exception as e:
            return f"ERROR: Failed to scaffold project: {str(e)}"

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

