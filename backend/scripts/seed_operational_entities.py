import psycopg2
import uuid
from psycopg2.extras import RealDictCursor

conn = psycopg2.connect("postgresql://postgres.hfgfqzpjkndwmukmjvjg:89046911338088@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres")
cur = conn.cursor(cursor_factory=RealDictCursor)

print("Adjusting foreign keys for user_profiles and seeding operational field workers...")

# Drop user_profiles_id_fkey if exists
cur.execute("ALTER TABLE user_profiles DROP CONSTRAINT IF EXISTS user_profiles_id_fkey;")
conn.commit()
print("Dropped user_profiles_id_fkey constraint")

# 1. Municipality
cur.execute("SELECT id FROM municipalities WHERE code = 'BMC' LIMIT 1")
row = cur.fetchone()
if not row:
    muni_id = str(uuid.uuid4())
    cur.execute("""
        INSERT INTO municipalities (id, name, code, state, district, config)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (muni_id, "Brihanmumbai Municipal Corporation", "BMC", "Maharashtra", "Mumbai", '{}'))
else:
    muni_id = str(row["id"])

# 2. Departments
departments_data = [
    ("roads", "Roads & Traffic Infrastructure", "Pothole repair, road surfacing, asphalt layering, curb repairs"),
    ("sanitation", "Solid Waste Management & Sanitation", "Garbage collection, overflowing bins, street sweeping, dump clearance"),
    ("water", "Water Supply & Sewage Operations", "Pipeline bursts, water leakage, sewer blockages, low pressure"),
    ("drainage", "Stormwater & Flood Drainage", "Drain cleaning, monsoon waterlogging, culvert desilting"),
    ("electrical", "Street Lighting & Electrical Works", "Faulty streetlights, open junction boxes, power cuts on streets"),
    ("health", "Public Health & Vector Control", "Fumigation, stagnant water, pest control, sanitation inspections"),
    ("general", "Civil Infrastructure & General Works", "Footpaths, public parks, wall repairs, municipal property maintenance"),
]

dept_ids = {}
for code, name, desc in departments_data:
    cur.execute("SELECT id FROM departments WHERE code = %s LIMIT 1", (code,))
    drow = cur.fetchone()
    if not drow:
        d_id = str(uuid.uuid4())
        cur.execute("""
            INSERT INTO departments (id, municipality_id, name, code, description)
            VALUES (%s, %s, %s, %s, %s)
        """, (d_id, muni_id, name, code, desc))
        dept_ids[code] = d_id
    else:
        dept_ids[code] = str(drow["id"])

# 3. Core Skills
skills_data = [
    ("roads", ["Asphalt Paving", "Pothole Filling", "Road Compaction", "Heavy Equipment Operation"]),
    ("sanitation", ["Waste Disposal", "Compactor Truck Driving", "Segregation", "Street Sweeping"]),
    ("water", ["Plumbing & Pipe Repair", "Valve Operation", "Sewer Jetting", "Leak Detection"]),
    ("drainage", ["Drain Cleaning", "Desilting", "Storm Drain Unblocking", "Pump Operation"]),
    ("electrical", ["High-Voltage Maintenance", "Streetlight Wiring", "Transformer Repair", "Safety Inspection"]),
    ("health", ["Vector Spraying", "Fogging Operation", "Sanitary Inspection", "Water Testing"]),
    ("general", ["Masonry", "Civil Maintenance", "Carpentry", "General Repairs"]),
]

skill_ids = {}
for dept_code, sk_list in skills_data:
    dept_id = dept_ids.get(dept_code)
    for sname in sk_list:
        cur.execute("SELECT id FROM skills WHERE name = %s LIMIT 1", (sname,))
        srow = cur.fetchone()
        if not srow:
            sk_id = str(uuid.uuid4())
            cur.execute("""
                INSERT INTO skills (id, name, description, department_id)
                VALUES (%s, %s, %s, %s)
            """, (sk_id, sname, f"Specialized skill for {dept_code}", dept_id))
            skill_ids[sname] = sk_id
        else:
            skill_ids[sname] = str(srow["id"])

# 4. Field Workers with User Profiles
workers_data = [
    ("Rajesh Shinde", "9820111222", "roads", "RW-101", 19.0600, 72.8300, ["Pothole Filling", "Asphalt Paving"]),
    ("Suresh Jadhav", "9820111223", "roads", "RW-102", 19.0750, 72.8750, ["Road Compaction", "Heavy Equipment Operation"]),
    ("Anil Kamble", "9820111224", "sanitation", "SW-201", 19.0550, 72.8400, ["Waste Disposal", "Compactor Truck Driving"]),
    ("Manoj Gaikwad", "9820111225", "sanitation", "SW-202", 19.0800, 72.8600, ["Segregation", "Street Sweeping"]),
    ("Vijay More", "9820111226", "water", "WW-301", 19.0700, 72.8500, ["Plumbing & Pipe Repair", "Leak Detection"]),
    ("Prakash Pawar", "9820111227", "water", "WW-302", 19.0650, 72.8800, ["Valve Operation", "Sewer Jetting"]),
    ("Dinesh Patil", "9820111228", "drainage", "DW-401", 19.0620, 72.8350, ["Drain Cleaning", "Storm Drain Unblocking"]),
    ("Sunil Kadam", "9820111229", "electrical", "EW-501", 19.0720, 72.8680, ["Streetlight Wiring", "Safety Inspection"]),
    ("Santosh Sawant", "9820111230", "health", "HW-601", 19.0580, 72.8450, ["Vector Spraying", "Fogging Operation"]),
    ("Ganesh Surve", "9820111231", "general", "GW-701", 19.0640, 72.8550, ["Masonry", "Civil Maintenance"]),
]

for name, phone, dept_code, emp_code, lat, lon, w_skills in workers_data:
    dept_id = dept_ids.get(dept_code)
    cur.execute("SELECT id FROM workers WHERE employee_code = %s LIMIT 1", (emp_code,))
    wrow = cur.fetchone()
    if not wrow:
        user_id = str(uuid.uuid4())
        worker_id = str(uuid.uuid4())
        
        # User profile
        cur.execute("""
            INSERT INTO user_profiles (id, role, full_name, phone, municipality_id, department_id, is_active)
            VALUES (%s, 'worker', %s, %s, %s, %s, true)
        """, (user_id, name, phone, muni_id, dept_id))
        
        # Worker record with GPS location
        cur.execute("""
            INSERT INTO workers (id, user_id, department_id, employee_code, status, current_location, max_concurrent_tasks)
            VALUES (%s, %s, %s, %s, 'available', ST_SetSRID(ST_MakePoint(%s, %s), 4326), 5)
        """, (worker_id, user_id, dept_id, emp_code, lon, lat))
        
        # Worker skills
        for sk_name in w_skills:
            if sk_name in skill_ids:
                cur.execute("""
                    INSERT INTO worker_skills (worker_id, skill_id, proficiency_level)
                    VALUES (%s, %s, 5)
                    ON CONFLICT DO NOTHING
                """, (worker_id, skill_ids[sk_name]))
                
        print(f"Created Field Worker: {name} ({emp_code}) in {dept_code}")

conn.commit()
conn.close()
print("Operational municipal setup complete!")
