import psycopg2
import sys
import os

DB_URL = "postgresql://postgres.hfgfqzpjkndwmukmjvjg:89046911338088@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres"

def run_migration():
    print(f"Connecting to Supabase PostgreSQL at aws-0-ap-southeast-1.pooler.supabase.com...")
    try:
        conn = psycopg2.connect(DB_URL, connect_timeout=15)
        conn.autocommit = True
        cur = conn.cursor()
        print("Connected successfully!")
        
        # Test query
        cur.execute("SELECT version();")
        ver = cur.fetchone()
        print(f"PostgreSQL Version: {ver[0]}")
        
        # Read schema file
        schema_path = os.path.join(os.path.dirname(__file__), "migrations", "001_core_schema.sql")
        print(f"Reading migration file: {schema_path}...")
        with open(schema_path, "r", encoding="utf-8") as f:
            sql_content = f.read()
        
        print("Executing migration script (creating tables, enums, triggers, PostGIS extensions)...")
        cur.execute(sql_content)
        print("Migration executed successfully!")
        
        # Verify created tables
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        tables = [row[0] for row in cur.fetchall()]
        print(f"\nCreated {len(tables)} tables in public schema:")
        for t in tables:
            print(f" - {t}")
            
        cur.close()
        conn.close()
        return 0
    except Exception as e:
        print(f"Error executing migration: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(run_migration())
