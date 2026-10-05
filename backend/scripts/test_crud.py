import urllib.request
import json

base_url = "http://127.0.0.1:8000/api/incidents"

# 1. CREATE
print("--- 1. Testing CREATE Incident ---")
create_payload = json.dumps({
    "title": "Waterlogging at Hindmata Junction",
    "description": "Severe rainwater flooding obstructing traffic movement at Hindmata Dadar",
    "category": "Stormwater Drainage",
    "priority_level": "critical",
    "priority_score": 92.0,
    "status": "open",
    "latitude": 19.0178,
    "longitude": 72.8478,
    "address": "Hindmata Flyover Underpass, Dadar East, Mumbai",
    "ward_id": "Ward 14 (Dadar)",
    "safety_risk": True,
    "estimated_affected_population": 500
}).encode("utf-8")

req = urllib.request.Request(base_url, data=create_payload, headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode("utf-8"))
    created_id = data["id"]
    print("CREATED SUCCESS: status =", resp.status, "ID =", created_id, "Number =", data.get("incident_number"))

# 2. READ
print("\n--- 2. Testing READ Incident ---")
req = urllib.request.Request(f"{base_url}/{created_id}", headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode("utf-8"))
    print("READ SUCCESS: Title =", data.get("title"), "Status =", data.get("status"), "Priority =", data.get("priority_level"))

# 3. UPDATE
print("\n--- 3. Testing UPDATE Incident ---")
update_payload = json.dumps({
    "title": "Waterlogging at Hindmata Junction - Pumps Deployed",
    "status": "in_progress",
    "priority_score": 85.0,
    "description": "High-capacity dewatering pumps operational on-site."
}).encode("utf-8")

req = urllib.request.Request(f"{base_url}/{created_id}", data=update_payload, headers={"Content-Type": "application/json"}, method="PUT")
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode("utf-8"))
    print("UPDATE SUCCESS: New Status =", data.get("status"), "Updated Title =", data.get("title"))

# 4. DELETE
print("\n--- 4. Testing DELETE Incident ---")
req = urllib.request.Request(f"{base_url}/{created_id}", headers={"Content-Type": "application/json"}, method="DELETE")
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode("utf-8"))
    print("DELETE SUCCESS: message =", data.get("message"))

print("\nALL CRUD TESTS PASSED SUCCESSFULLY!")
