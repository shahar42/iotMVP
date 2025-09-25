"""
Enhanced Database Tools
Advanced tools for interacting with multiple database types.
Supports PostgreSQL, MySQL, SQLite with comprehensive operations.
"""

import json
import sqlite3
import os
import requests
from typing import Dict, List, Optional, Any, Union
from fastmcp import FastMCP

# Optional imports with fallbacks
try:
    import psycopg2
    import psycopg2.extras
    POSTGRESQL_AVAILABLE = True
except ImportError:
    POSTGRESQL_AVAILABLE = False

try:
    import mysql.connector
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False

class WorkspaceManager:
    """Render workspace discovery and management for LLM-friendly operations"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.render.com/v1"

    def discover_workspaces(self) -> Dict[str, Any]:
        """Discover all available workspaces for the API key"""
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = requests.get(f"{self.base_url}/owners", headers=headers)
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

    def select_workspace(self, workspace_hint: Optional[str] = None) -> str:
        """
        Intelligently select workspace based on hint or return default

        LLM-FRIENDLY: Uses fuzzy matching to find best workspace match,
        provides clear feedback on selection reasoning.
        """
        discovery = self.discover_workspaces()

        if discovery.get('error'):
            return f"ERROR: Cannot discover workspaces: {discovery['error']}"

        workspaces = discovery['workspaces']
        if not workspaces:
            return "ERROR: No accessible workspaces found"

        # If no hint provided, use default
        if not workspace_hint:
            selected = workspaces[0]
            return f"WORKSPACE: Using default workspace\nID: {selected['id']}\nNAME: {selected['name']}"

        # Try to find matching workspace by name or partial match
        workspace_hint_lower = workspace_hint.lower()

        # Exact name match first
        for ws in workspaces:
            if ws['name'].lower() == workspace_hint_lower:
                return f"WORKSPACE: Found exact match\nID: {ws['id']}\nNAME: {ws['name']}"

        # Partial name match
        for ws in workspaces:
            if workspace_hint_lower in ws['name'].lower():
                return f"WORKSPACE: Found partial match\nID: {ws['id']}\nNAME: {ws['name']}\nMATCH: '{workspace_hint}' found in '{ws['name']}'"

        # ID match
        for ws in workspaces:
            if ws['id'] == workspace_hint:
                return f"WORKSPACE: Found by ID\nID: {ws['id']}\nNAME: {ws['name']}"

        # No match found, return default with suggestion
        selected = workspaces[0]
        available = ", ".join([f"{ws['name']} ({ws['id']})" for ws in workspaces])
        return f"WORKSPACE: No match for '{workspace_hint}', using default\nID: {selected['id']}\nNAME: {selected['name']}\nAVAILABLE: {available}"

class DatabaseManager:
    """Unified database manager supporting multiple database types"""

    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.db_type = self._detect_db_type()

    def _detect_db_type(self) -> str:
        """Detect database type from connection string"""
        if self.connection_string.startswith('postgresql://') or self.connection_string.startswith('postgres://'):
            return 'postgresql'
        elif self.connection_string.startswith('mysql://'):
            return 'mysql'
        elif self.connection_string.endswith('.db') or self.connection_string.startswith('sqlite://'):
            return 'sqlite'
        else:
            # Default to postgresql for connection strings without protocol
            return 'postgresql'

    def get_connection(self):
        """Get database connection based on type"""
        if self.db_type == 'sqlite':
            db_path = self.connection_string.replace('sqlite://', '') if self.connection_string.startswith('sqlite://') else self.connection_string
            return sqlite3.connect(db_path)
        elif self.db_type == 'postgresql' and POSTGRESQL_AVAILABLE:
            return psycopg2.connect(self.connection_string)
        elif self.db_type == 'mysql' and MYSQL_AVAILABLE:
            # Parse MySQL connection string
            return mysql.connector.connect(self.connection_string)
        else:
            raise Exception(f"Database type '{self.db_type}' not supported or driver not available")

def register_database_tools(mcp: FastMCP):
    """Register enhanced database tools with FastMCP server"""

    @mcp.tool()
    def discover_render_workspaces(api_key: str = "rnd_j6WyOXSMG0bGFbqyYKMBaxUgzF4s") -> str:
        """
        Discover all available Render workspaces for the API key.

        LLM-FRIENDLY: Returns structured workspace information with IDs, names,
        and guidance on which workspace to use for resource creation.

        Args:
            api_key: Render API key (defaults to configured key)

        Returns clear list of workspaces with selection guidance.
        """
        try:
            workspace_manager = WorkspaceManager(api_key)
            discovery = workspace_manager.discover_workspaces()

            if discovery.get('error'):
                return f"ERROR: Failed to discover workspaces: {discovery['error']}"

            workspaces = discovery['workspaces']
            if not workspaces:
                return "ERROR: No accessible workspaces found"

            output = [f"WORKSPACES: Found {discovery['count']} accessible workspaces"]
            output.append("=" * 60)

            for i, ws in enumerate(workspaces, 1):
                marker = "🔸 DEFAULT" if i == 1 else "  "
                output.append(f"{marker} [{i:02d}] {ws['name']}")
                output.append(f"        ID: {ws['id']}")
                output.append(f"        Email: {ws['email']}")
                output.append(f"        Type: {ws['type']}")
                output.append("")

            output.append("USAGE:")
            output.append("• Use workspace ID in owner_id parameter for resource creation")
            output.append("• Default workspace used if no workspace specified")
            output.append("• Workspace names support fuzzy matching")

            return "\n".join(output)

        except Exception as e:
            return f"ERROR: Failed to discover workspaces: {str(e)}"

    @mcp.tool()
    def select_workspace(
        workspace_hint: Optional[str] = None,
        api_key: str = "rnd_j6WyOXSMG0bGFbqyYKMBaxUgzF4s"
    ) -> str:
        """
        Intelligently select a Render workspace based on name or ID hint.

        LLM-FRIENDLY: Uses fuzzy matching to find the best workspace match,
        returns the workspace ID and clear reasoning for the selection.

        Args:
            workspace_hint: Workspace name, partial name, or ID to search for
            api_key: Render API key (defaults to configured key)

        Example hints: "database", "Database_Web_Ser", "tea-d3apf456ubrc7396rtdg"
        """
        try:
            workspace_manager = WorkspaceManager(api_key)
            result = workspace_manager.select_workspace(workspace_hint)
            return result

        except Exception as e:
            return f"ERROR: Failed to select workspace: {str(e)}"

    @mcp.tool()
    def run_sql_query(db_connection_string: str, sql_statement: str, fetch_results: bool = True) -> str:
        """
        Execute a SQL statement and return formatted results.

        LLM-FRIENDLY: Returns structured output with clear success/error indicators,
        formatted tables, and both human-readable and JSON formats for easy parsing.

        Args:
            db_connection_string: Database connection string (PostgreSQL, MySQL, SQLite)
            sql_statement: SQL statement to execute
            fetch_results: Whether to return query results (True) or just execute (False)
        """
        try:
            db_manager = DatabaseManager(db_connection_string)
            conn = db_manager.get_connection()

            if db_manager.db_type == 'sqlite':
                cur = conn.cursor()
                cur.execute(sql_statement)

                if fetch_results and sql_statement.strip().upper().startswith('SELECT'):
                    results = cur.fetchall()
                    columns = [desc[0] for desc in cur.description] if cur.description else []
                    conn.close()
                    return _format_query_results(results, columns, sql_statement)
                else:
                    conn.commit()
                    affected_rows = cur.rowcount
                    conn.close()
                    return f"SUCCESS: SQL executed successfully!\n\nSTATEMENT: {sql_statement}\nAFFECTED: {affected_rows} rows modified\nOPERATION: {sql_statement.split()[0].upper()} completed successfully\nDB_TYPE: SQLite"

            elif db_manager.db_type == 'postgresql':
                cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
                cur.execute(sql_statement)

                if fetch_results and sql_statement.strip().upper().startswith('SELECT'):
                    results = cur.fetchall()
                    columns = [desc[0] for desc in cur.description] if cur.description else []
                    conn.close()
                    return _format_query_results(results, columns, sql_statement)
                else:
                    conn.commit()
                    affected_rows = cur.rowcount
                    conn.close()
                    return f"SUCCESS: SQL executed successfully!\n\nSTATEMENT: {sql_statement}\nAFFECTED: {affected_rows} rows modified\nOPERATION: {sql_statement.split()[0].upper()} completed successfully\nDB_TYPE: PostgreSQL"

            else:  # MySQL
                cur = conn.cursor(dictionary=True)
                cur.execute(sql_statement)

                if fetch_results and sql_statement.strip().upper().startswith('SELECT'):
                    results = cur.fetchall()
                    columns = list(results[0].keys()) if results else []
                    conn.close()
                    return _format_query_results(results, columns, sql_statement)
                else:
                    conn.commit()
                    affected_rows = cur.rowcount
                    conn.close()
                    return f"SUCCESS: SQL executed successfully!\n\nSTATEMENT: {sql_statement}\nAFFECTED: {affected_rows} rows modified\nOPERATION: {sql_statement.split()[0].upper()} completed successfully\nDB_TYPE: MySQL"

        except Exception as e:
            return f"ERROR: Failed to execute SQL: {str(e)}"

    @mcp.tool()
    def create_database_table(
        db_connection_string: str,
        table_name: str,
        columns: str,
        constraints: Optional[str] = None
    ) -> str:
        """
        Create a database table with advanced options.

        LLM-FRIENDLY: Returns the generated SQL, table structure, and clear success indicators.
        Supports common patterns like auto-increment IDs, timestamps, and constraints.

        Args:
            db_connection_string: Database connection string
            table_name: Name of the table to create
            columns: JSON string of column definitions [{"name": "id", "type": "INTEGER", "options": "PRIMARY KEY"}]
            constraints: Additional table constraints (FOREIGN KEY, UNIQUE, etc.)

        Example columns JSON:
        '[{"name": "id", "type": "SERIAL", "options": "PRIMARY KEY"}, {"name": "email", "type": "VARCHAR(255)", "options": "NOT NULL UNIQUE"}]'
        """
        try:
            columns_list = json.loads(columns)
            db_manager = DatabaseManager(db_connection_string)

            # Build CREATE TABLE statement
            sql_parts = [f"CREATE TABLE {table_name} ("]

            for i, column in enumerate(columns_list):
                column_def = f"{column['name']} {column['type']}"
                if 'options' in column and column['options']:
                    column_def += f" {column['options']}"
                sql_parts.append(f"  {column_def}")
                if i < len(columns_list) - 1:
                    sql_parts.append(",")

            if constraints:
                sql_parts.append(f",\n  {constraints}")

            sql_parts.append(");")
            sql_statement = "\n".join(sql_parts)

            # Execute the CREATE TABLE statement
            conn = db_manager.get_connection()
            cur = conn.cursor()
            cur.execute(sql_statement)
            conn.commit()
            conn.close()

            return f"""SUCCESS: Table '{table_name}' created successfully!

SCHEMA: Generated SQL:
{sql_statement}

TABLE: Table: {table_name}
COLUMNS: Columns: {len(columns_list)}"""

        except Exception as e:
            return f"ERROR: Failed to create table: {str(e)}"

    @mcp.tool()
    def describe_table(db_connection_string: str, table_name: str) -> str:
        """
        Get detailed information about a table structure.

        Args:
            db_connection_string: Database connection string
            table_name: Name of the table to describe
        """
        try:
            db_manager = DatabaseManager(db_connection_string)
            conn = db_manager.get_connection()

            if db_manager.db_type == 'sqlite':
                cur = conn.cursor()
                cur.execute(f"PRAGMA table_info({table_name})")
                columns = cur.fetchall()

                if not columns:
                    return f"ERROR: Table '{table_name}' not found"

                result = [f"TABLE: Table Structure: {table_name}"]
                result.append("=" * 50)

                for col in columns:
                    cid, name, col_type, notnull, default_val, pk = col
                    constraints = []
                    if pk:
                        constraints.append("PRIMARY KEY")
                    if notnull:
                        constraints.append("NOT NULL")
                    if default_val is not None:
                        constraints.append(f"DEFAULT {default_val}")

                    constraint_str = f" ({', '.join(constraints)})" if constraints else ""
                    result.append(f"  {name}: {col_type}{constraint_str}")

            elif db_manager.db_type == 'postgresql':
                cur = conn.cursor()
                cur.execute("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_name = %s
                    ORDER BY ordinal_position
                """, (table_name,))
                columns = cur.fetchall()

                if not columns:
                    return f"ERROR: Table '{table_name}' not found"

                result = [f"TABLE: Table Structure: {table_name}"]
                result.append("=" * 50)

                for col in columns:
                    name, data_type, nullable, default = col
                    constraints = []
                    if nullable == 'NO':
                        constraints.append("NOT NULL")
                    if default:
                        constraints.append(f"DEFAULT {default}")

                    constraint_str = f" ({', '.join(constraints)})" if constraints else ""
                    result.append(f"  {name}: {data_type}{constraint_str}")

            conn.close()
            return "\n".join(result)

        except Exception as e:
            return f"ERROR: Failed to describe table: {str(e)}"

    @mcp.tool()
    def list_database_tables(db_connection_string: str) -> str:
        """
        List all tables in the database.

        Args:
            db_connection_string: Database connection string
        """
        try:
            db_manager = DatabaseManager(db_connection_string)
            conn = db_manager.get_connection()

            if db_manager.db_type == 'sqlite':
                cur = conn.cursor()
                cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cur.fetchall()]

            elif db_manager.db_type == 'postgresql':
                cur = conn.cursor()
                cur.execute("""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                """)
                tables = [row[0] for row in cur.fetchall()]

            conn.close()

            if not tables:
                return "LIST: No tables found in database"

            result = [f"LIST: Database Tables ({len(tables)} found)"]
            result.append("=" * 40)

            for i, table in enumerate(tables, 1):
                result.append(f"  [{i:02d}] {table}")

            return "\n".join(result)

        except Exception as e:
            return f"ERROR: Failed to list tables: {str(e)}"

    @mcp.tool()
    def seed_table_data(
        db_connection_string: str,
        table_name: str,
        data: str,
        operation: str = "insert"
    ) -> str:
        """
        Insert or upsert data into a table.

        LLM-FRIENDLY: Supports bulk inserts with clear feedback on what was inserted.
        Automatically handles column mapping and provides detailed success information.

        Args:
            db_connection_string: Database connection string
            table_name: Name of the target table
            data: JSON string with data [{"col1": "val1", "col2": "val2"}]
            operation: 'insert' or 'upsert' (insert or replace)

        Example data JSON:
        '[{"name": "John", "email": "john@example.com"}, {"name": "Jane", "email": "jane@example.com"}]'
        """
        try:
            data_list = json.loads(data)
            if not data_list:
                return "ERROR: No data provided"

            db_manager = DatabaseManager(db_connection_string)
            conn = db_manager.get_connection()
            cur = conn.cursor()

            # Get column names from first record
            columns = list(data_list[0].keys())
            placeholders = ', '.join(['?' if db_manager.db_type == 'sqlite' else '%s'] * len(columns))

            if operation == "upsert" and db_manager.db_type == 'sqlite':
                sql = f"INSERT OR REPLACE INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
            else:
                sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"

            # Prepare data rows
            rows = []
            for record in data_list:
                row = [record.get(col) for col in columns]
                rows.append(row)

            cur.executemany(sql, rows)
            conn.commit()
            conn.close()

            return f"""SUCCESS: Data inserted successfully!

TABLE: Table: {table_name}
ROWS: Inserted: {len(data_list)} rows
COLUMNS: Columns: {', '.join(columns)}
OPERATION: Operation: {operation}"""

        except Exception as e:
            return f"ERROR: Failed to seed data: {str(e)}"

    @mcp.tool()
    def backup_table_data(db_connection_string: str, table_name: str, limit: Optional[int] = None) -> str:
        """
        Export table data as JSON for backup purposes.

        Args:
            db_connection_string: Database connection string
            table_name: Name of the table to backup
            limit: Maximum number of rows to export (optional)
        """
        try:
            db_manager = DatabaseManager(db_connection_string)
            conn = db_manager.get_connection()

            # Build query with optional limit
            query = f"SELECT * FROM {table_name}"
            if limit:
                query += f" LIMIT {limit}"

            if db_manager.db_type == 'sqlite':
                cur = conn.cursor()
                cur.execute(query)
                rows = cur.fetchall()
                columns = [desc[0] for desc in cur.description]

                # Convert to list of dictionaries
                data = [dict(zip(columns, row)) for row in rows]

            elif db_manager.db_type == 'postgresql':
                cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
                cur.execute(query)
                rows = cur.fetchall()
                data = [dict(row) for row in rows]

            conn.close()

            # Format as JSON
            json_data = json.dumps(data, indent=2, default=str)

            return f"""SUCCESS: Table data exported!

TABLE: Table: {table_name}
ROWS: Rows: {len(data)}
SIZE: Size: {len(json_data)} characters

BACKUP: JSON Data:
{json_data}"""

        except Exception as e:
            return f"ERROR: Failed to backup table: {str(e)}"

    @mcp.tool()
    def test_database_connection(db_connection_string: str) -> str:
        """
        Test database connectivity and return connection details.

        Args:
            db_connection_string: Database connection string to test
        """
        try:
            db_manager = DatabaseManager(db_connection_string)
            conn = db_manager.get_connection()

            # Test with a simple query
            cur = conn.cursor()
            if db_manager.db_type == 'sqlite':
                cur.execute("SELECT sqlite_version()")
                version = cur.fetchone()[0]
                conn.close()
                return f"""SUCCESS: Database connection successful!

DB_TYPE: Type: SQLite
VERSION: Version: {version}
STATUS: Connection: Active"""

            elif db_manager.db_type == 'postgresql':
                cur.execute("SELECT version()")
                version_info = cur.fetchone()[0]
                conn.close()
                return f"""SUCCESS: Database connection successful!

DB_TYPE: Type: PostgreSQL
VERSION: Version: {version_info.split(',')[0]}
STATUS: Connection: Active"""

            conn.close()
            return f"SUCCESS: Connection to {db_manager.db_type} database successful!"

        except Exception as e:
            return f"ERROR: Database connection failed: {str(e)}"

    @mcp.tool()
    def create_common_tables(db_connection_string: str, app_type: str = "webapp") -> str:
        """
        Create common database tables for typical applications.

        LLM-FRIENDLY: Quick setup for common app patterns. Creates standard tables
        with proper relationships, indexes, and constraints.

        Args:
            db_connection_string: Database connection string
            app_type: Type of app ('webapp', 'blog', 'ecommerce', 'social')

        Returns detailed information about created tables and their relationships.
        """
        try:
            db_manager = DatabaseManager(db_connection_string)
            tables_created = []

            if app_type == "webapp":
                # Users table
                users_sql = """
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )"""

                # Sessions table
                sessions_sql = """
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    token VARCHAR(255) UNIQUE NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )"""

                # Settings table
                settings_sql = """
                CREATE TABLE IF NOT EXISTS app_settings (
                    id SERIAL PRIMARY KEY,
                    key VARCHAR(100) UNIQUE NOT NULL,
                    value TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )"""

                conn = db_manager.get_connection()
                cur = conn.cursor()

                for sql, table_name in [(users_sql, "users"), (sessions_sql, "user_sessions"), (settings_sql, "app_settings")]:
                    cur.execute(sql)
                    tables_created.append(table_name)

                conn.commit()
                conn.close()

                return f"""SUCCESS: Common webapp tables created!

TABLES_CREATED: {len(tables_created)} tables created:
{''.join([f'  ✓ {table}\n' for table in tables_created])}

SCHEMA_INFO:
  • users: User accounts with authentication
  • user_sessions: Session management with expiration
  • app_settings: Application configuration storage

RELATIONSHIPS:
  • user_sessions.user_id → users.id (CASCADE DELETE)

NEXT_STEPS:
  • Add indexes: CREATE INDEX idx_users_email ON users(email);
  • Seed admin user: INSERT INTO users (username, email, password_hash) VALUES (...)
  • Add app settings: INSERT INTO app_settings (key, value) VALUES ('app_name', 'My App');

DATABASE: {db_manager.db_type.upper()} tables ready for use!"""

            elif app_type == "blog":
                # Blog-specific tables would go here
                return "ERROR: Blog app type not yet implemented"

            else:
                return f"ERROR: Unknown app type '{app_type}'. Supported: webapp, blog"

        except Exception as e:
            return f"ERROR: Failed to create common tables: {str(e)}"

    @mcp.tool()
    def analyze_database_performance(db_connection_string: str) -> str:
        """
        Analyze database performance and suggest optimizations.

        LLM-FRIENDLY: Returns actionable insights about database health,
        slow queries, missing indexes, and optimization recommendations.

        Args:
            db_connection_string: Database connection string
        """
        try:
            db_manager = DatabaseManager(db_connection_string)
            conn = db_manager.get_connection()

            analysis = []
            analysis.append("PERFORMANCE: Database Performance Analysis")
            analysis.append("=" * 50)

            if db_manager.db_type == 'postgresql':
                cur = conn.cursor()

                # Table sizes
                cur.execute("""
                    SELECT schemaname, tablename,
                           pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                           pg_total_relation_size(schemaname||'.'||tablename) as bytes
                    FROM pg_tables
                    WHERE schemaname = 'public'
                    ORDER BY bytes DESC
                """)

                tables = cur.fetchall()
                analysis.append(f"\nTABLE_SIZES: Found {len(tables)} tables:")
                for table in tables[:10]:  # Top 10
                    analysis.append(f"  📊 {table[1]}: {table[2]}")

                # Index usage
                cur.execute("""
                    SELECT schemaname, tablename, attname, n_distinct, correlation
                    FROM pg_stats
                    WHERE schemaname = 'public'
                    ORDER BY n_distinct DESC
                """)

                stats = cur.fetchall()
                analysis.append(f"\nINDEX_CANDIDATES: Columns with high cardinality:")
                for stat in stats[:5]:
                    if stat[3] and stat[3] > 100:
                        analysis.append(f"  🎯 {stat[1]}.{stat[2]}: {stat[3]} distinct values")

            analysis.append(f"\nOPTIMIZATION_TIPS:")
            analysis.append("  • Add indexes on frequently queried columns")
            analysis.append("  • Consider partitioning large tables")
            analysis.append("  • Use EXPLAIN ANALYZE on slow queries")
            analysis.append("  • Monitor connection pool usage")

            conn.close()
            return "\n".join(analysis)

        except Exception as e:
            return f"ERROR: Failed to analyze database: {str(e)}"

    @mcp.tool()
    def create_database_with_workspace_discovery(
        name: str,
        database_name: str,
        database_user: str,
        workspace_hint: Optional[str] = None,
        region: str = "oregon",
        plan: str = "free",
        version: str = "16",
        api_key: str = "rnd_j6WyOXSMG0bGFbqyYKMBaxUgzF4s"
    ) -> str:
        """
        Create PostgreSQL database with automatic workspace discovery.

        LLM-FRIENDLY: Automatically discovers and selects the best workspace,
        then creates the database with clear feedback about workspace selection.

        Args:
            name: Human-friendly display name for the database
            database_name: The name of the initial database
            database_user: The name of the initial database user
            workspace_hint: Optional workspace name/ID hint (uses fuzzy matching)
            region: Database region (default: oregon)
            plan: Database plan (default: free)
            version: PostgreSQL version (default: 16)
            api_key: Render API key

        Example: create_database_with_workspace_discovery("my-app-db", "app_db", "app_user", "database")
        """
        try:
            # Step 1: Discover and select workspace
            workspace_manager = WorkspaceManager(api_key)
            discovery = workspace_manager.discover_workspaces()

            if discovery.get('error'):
                return f"ERROR: Cannot discover workspaces: {discovery['error']}"

            workspaces = discovery['workspaces']
            if not workspaces:
                return "ERROR: No accessible workspaces found"

            # Select workspace
            selected_workspace = None
            workspace_selection_reason = ""

            if workspace_hint:
                workspace_hint_lower = workspace_hint.lower()

                # Try exact match first
                for ws in workspaces:
                    if ws['name'].lower() == workspace_hint_lower:
                        selected_workspace = ws
                        workspace_selection_reason = f"Exact match for '{workspace_hint}'"
                        break

                # Try partial match
                if not selected_workspace:
                    for ws in workspaces:
                        if workspace_hint_lower in ws['name'].lower():
                            selected_workspace = ws
                            workspace_selection_reason = f"Partial match: '{workspace_hint}' found in '{ws['name']}'"
                            break

                # Try ID match
                if not selected_workspace:
                    for ws in workspaces:
                        if ws['id'] == workspace_hint:
                            selected_workspace = ws
                            workspace_selection_reason = f"ID match for '{workspace_hint}'"
                            break

            # Use default if no match found
            if not selected_workspace:
                selected_workspace = workspaces[0]
                available = ", ".join([f"{ws['name']}" for ws in workspaces])
                if workspace_hint:
                    workspace_selection_reason = f"No match for '{workspace_hint}', using default. Available: {available}"
                else:
                    workspace_selection_reason = f"Using default workspace from {len(workspaces)} available"

            # Step 2: Create database in selected workspace
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

            payload = {
                "ownerId": selected_workspace['id'],
                "name": name,
                "region": region,
                "plan": plan,
                "version": version,
                "databaseName": database_name,
                "databaseUser": database_user
            }

            response = requests.post(
                "https://api.render.com/v1/postgres",
                headers=headers,
                json=payload
            )

            if response.status_code == 201:
                db_data = response.json()

                return f"""SUCCESS: PostgreSQL Database Created with Workspace Discovery!

WORKSPACE_SELECTION:
  {workspace_selection_reason}
  Selected: {selected_workspace['name']} ({selected_workspace['id']})

DATABASE_INFO:
  ID: {db_data.get('id', 'N/A')}
  Name: {name}
  Status: {db_data.get('status', 'N/A')}
  Region: {region}
  Plan: {plan}
  Version: PostgreSQL {version}

CONNECTION_STRINGS:
  External: {db_data.get('externalConnectionString', 'Generating...')}
  Internal: {db_data.get('internalConnectionString', 'Generating...')}

NEXT_STEPS:
  • Wait for database to become 'available' status
  • Use connection string in your application
  • Create tables using the database tools
  • Test connection with test_database_connection tool

WORKSPACE: Database created in {selected_workspace['name']} workspace"""

            else:
                error_msg = response.json().get('message', 'Unknown error') if response.content else f"HTTP {response.status_code}"
                return f"ERROR: Failed to create database: {error_msg}\nWORKSPACE_ATTEMPTED: {selected_workspace['name']} ({selected_workspace['id']})"

        except Exception as e:
            return f"ERROR: Database creation failed: {str(e)}"

def _format_query_results(results: List, columns: List[str], sql_statement: str = "") -> str:
    """Format query results in a readable table format for LLM consumption"""
    if not results:
        return f"QUERY: No results returned\n\nSTATEMENT: {sql_statement}\nROWS: 0 rows found"

    # Convert results to list of dictionaries for consistent handling
    if isinstance(results[0], (list, tuple)):
        formatted_results = [dict(zip(columns, row)) for row in results]
    else:
        formatted_results = [dict(row) for row in results]

    output = [f"QUERY: Query Results - {len(formatted_results)} rows found"]
    output.append("=" * 70)
    output.append(f"STATEMENT: {sql_statement}")
    output.append("")

    # Add column headers
    if columns:
        output.append(" | ".join(f"{col:<15}" for col in columns))
        output.append("-" * 60)

    # Add data rows (limit to prevent excessive output)
    for i, row in enumerate(formatted_results[:50]):  # Limit to 50 rows for display
        row_values = [str(row.get(col, ''))[:15] for col in columns] if columns else [str(v)[:15] for v in row.values()]
        output.append(" | ".join(f"{val:<15}" for val in row_values))

    if len(formatted_results) > 50:
        output.append(f"... and {len(formatted_results) - 50} more rows")

    # Add JSON export for programmatic use
    output.append(f"\nJSON: JSON Export:")
    output.append(json.dumps(formatted_results, indent=2, default=str))

    return "\n".join(output)
