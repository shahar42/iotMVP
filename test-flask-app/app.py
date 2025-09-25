from flask import Flask, jsonify, request, render_template
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import json

app = Flask(__name__)

def get_db_connection():
    """Get database connection using environment variable"""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        return None

    try:
        conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

def init_database():
    """Initialize database tables"""
    conn = get_db_connection()
    if not conn:
        return False

    try:
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS test_records (
                id SERIAL PRIMARY KEY,
                message TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Database initialization error: {e}")
        return False

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api')
def api_hello():
    return jsonify({
        "message": "Hello from Flask with Database!",
        "status": "success",
        "app": "test-deployment-fullstack",
        "database": "connected" if get_db_connection() else "not connected"
    })

@app.route('/health')
def health():
    db_status = "connected" if get_db_connection() else "disconnected"
    return jsonify({
        "status": "healthy",
        "database": db_status
    }), 200

@app.route('/records', methods=['GET'])
def get_records():
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database not available"}), 500

    try:
        cur = conn.cursor()
        cur.execute('SELECT * FROM test_records ORDER BY created_at DESC LIMIT 10')
        records = cur.fetchall()
        cur.close()
        conn.close()

        return jsonify({
            "records": [dict(record) for record in records],
            "count": len(records)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/records', methods=['POST'])
def add_record():
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database not available"}), 500

    try:
        data = request.get_json()
        message = data.get('message', 'Test message')

        cur = conn.cursor()
        cur.execute(
            'INSERT INTO test_records (message) VALUES (%s) RETURNING *',
            (message,)
        )
        new_record = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({
            "status": "created",
            "record": dict(new_record)
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/init-db')
def initialize_db():
    """Endpoint to initialize database (for testing)"""
    success = init_database()
    return jsonify({
        "database_initialized": success,
        "message": "Database tables created" if success else "Failed to create tables"
    })

if __name__ == '__main__':
    # Initialize database on startup
    init_database()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)