import psycopg2
from psycopg2.extras import RealDictCursor

conn = psycopg2.connect("postgresql://postgres.hfgfqzpjkndwmukmjvjg:89046911338088@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres")
cur = conn.cursor(cursor_factory=RealDictCursor)

cur.execute("""
SELECT conname, pg_get_constraintdef(oid) as def 
FROM pg_constraint 
WHERE conrelid = 'user_profiles'::regclass
""")
for r in cur.fetchall():
    print(r['conname'], "-->", r['def'])
