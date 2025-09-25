"""
Database Tools
Tools for interacting with databases.
"""

import psycopg2
from fastmcp import FastMCP

def register_database_tools(mcp: FastMCP):
    """Register database tools with FastMCP server"""

    @mcp.tool()
    def run_sql(db_connection_string: str, sql_statement: str) -> str:
        """
        Execute a SQL statement against the database.

        Args:
            db_connection_string: The connection string for the database.
            sql_statement: The SQL statement to execute.
        """

        try:
            conn = psycopg2.connect(db_connection_string)
            cur = conn.cursor()
            cur.execute(sql_statement)
            conn.commit()
            cur.close()
            conn.close()
            return f"SUCCESS: Successfully executed SQL statement."
        except Exception as e:
            return f"ERROR: Failed to execute SQL statement: {str(e)}"

    @mcp.tool()
    def generate_schema(table_name: str, columns: str) -> str:
        """
        Generate a SQL CREATE TABLE statement.

        Args:
            table_name: The name of the table to create.
            columns: A JSON string representing a list of columns.
                     Each column should be a dictionary with 'name', 'type', and 'options' keys.
        """

        try:
            columns_list = json.loads(columns)
            sql = f"CREATE TABLE {table_name} ("
            for i, column in enumerate(columns_list):
                sql += f"{column['name']} {column['type']} {column.get('options', '')}"
                if i < len(columns_list) - 1:
                    sql += ", "
            sql += ");"
            return sql
        except Exception as e:
            return f"ERROR: Failed to generate schema: {str(e)}"
