import psycopg2
from psycopg2.extras import RealDictCursor

conn = psycopg2.connect("postgresql://postgres.hfgfqzpjkndwmukmjvjg:89046911338088@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres")
cur = conn.cursor(cursor_factory=RealDictCursor)

tables = ["municipalities", "departments", "user_profiles", "workers", "skills", "worker_skills", "wards"]
for t in tables:
    cur.execute(f"SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name = '{t}' ORDER BY ordinal_position")
    cols = cur.fetchall()
    print(f"\nTABLE: {t}")
    for c in cols:
        print(f"  {c['column_name']} ({c['data_type']}) nullable={c['is_nullable']}")
