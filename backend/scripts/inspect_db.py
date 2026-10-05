import psycopg2
from psycopg2.extras import RealDictCursor

conn = psycopg2.connect("postgresql://postgres.hfgfqzpjkndwmukmjvjg:89046911338088@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres")
cur = conn.cursor(cursor_factory=RealDictCursor)

cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name")
tables = [r['table_name'] for r in cur.fetchall()]
print("Found tables:", len(tables))
for t in tables:
    cur.execute(f'SELECT count(*) FROM "{t}"')
    cnt = cur.fetchone()['count']
    print(f"  {t}: {cnt}")
