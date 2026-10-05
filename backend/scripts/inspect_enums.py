import psycopg2
from psycopg2.extras import RealDictCursor

conn = psycopg2.connect('postgresql://postgres.hfgfqzpjkndwmukmjvjg:89046911338088@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres')
cur = conn.cursor(cursor_factory=RealDictCursor)

cur.execute("""
SELECT t.typname, e.enumlabel
FROM pg_type t
JOIN pg_enum e ON t.oid = e.enumtypid
ORDER BY t.typname, e.enumsortorder;
""")
for r in cur.fetchall():
    print(r['typname'], '-->', r['enumlabel'])
