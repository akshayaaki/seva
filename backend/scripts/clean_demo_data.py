import psycopg2
from psycopg2.extras import RealDictCursor

conn = psycopg2.connect("postgresql://postgres.hfgfqzpjkndwmukmjvjg:89046911338088@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres")
cur = conn.cursor(cursor_factory=RealDictCursor)

print("Removing test/demo data in correct relational sequence...")

cur.execute("DELETE FROM assignments WHERE true;")
cur.execute("DELETE FROM tasks WHERE true;")
cur.execute("DELETE FROM incident_complaints WHERE true;")
cur.execute("DELETE FROM complaint_messages WHERE true;")
cur.execute("DELETE FROM complaint_evidence WHERE true;")
cur.execute("DELETE FROM citizen_confirmations WHERE true;")
cur.execute("UPDATE complaints SET master_incident_id = NULL WHERE true;")
cur.execute("DELETE FROM complaints WHERE true;")
cur.execute("DELETE FROM master_incidents WHERE true;")
cur.execute("DELETE FROM locations WHERE true;")
cur.execute("DELETE FROM audit_logs WHERE true;")
cur.execute("DELETE FROM notifications WHERE true;")

conn.commit()
conn.close()
print("All demo and test tasks, incidents, and complaints successfully removed!")
