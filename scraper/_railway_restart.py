import requests, json

TOKEN = "Fi9kA_Yt2VeDwq-MrxSyHcWGeigtSh9FcVVTVc0bwwe"
PROJECT_ID = "a29714ed-e5d9-4163-a0f8-c86927914039"
ENV_ID = "14e178d6-f129-4e31-a9a4-9ace9a14fb9c"
API = "https://backboard.railway.app/graphql/v2"
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

# 1. List all services
r = requests.post(API, json={"query": f"""
  query {{
    project(id: "{PROJECT_ID}") {{
      services {{
        edges {{
          node {{ id name }}
        }}
      }}
    }}
  }}
"""}, headers=HEADERS, timeout=15)

data = r.json()
print("Services:", json.dumps(data, indent=2))

# Find postgres service
services = data.get("data", {}).get("project", {}).get("services", {}).get("edges", [])
pg_service = next((s["node"] for s in services if "postgres" in s["node"]["name"].lower() or "pg" in s["node"]["name"].lower() or "database" in s["node"]["name"].lower()), None)

if pg_service:
    print(f"\nFound DB service: {pg_service['name']} ({pg_service['id']})")
    # Restart it
    r2 = requests.post(API, json={"query": f"""
      mutation {{
        serviceInstanceRedeploy(environmentId: "{ENV_ID}", serviceId: "{pg_service['id']}")
      }}
    """}, headers=HEADERS, timeout=15)
    print("Restart response:", r2.json())
else:
    print("\nNo postgres service found — printing all:")
    for s in services:
        print(" ", s["node"]["name"], s["node"]["id"])
