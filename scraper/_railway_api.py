"""
Use Railway API token to restart services and check project state.
Token from ~/.railway/config.json
"""
import urllib.request
import json

ACCESS_TOKEN = "Fi9kA_Yt2VeDwq-MrxSyHcWGeigtSh9FcVVTVc0bwwe"
REFRESH_TOKEN = "ZwsQeu7eDCsp97rnPnxY_9eRZbN2Aar1xWkQjUCLSAy"
PROJECT_ID = "a29714ed-e5d9-4163-a0f8-c86927914039"
ENVIRONMENT_ID = "14e178d6-f129-4e31-a9a4-9ace9a14fb9c"

def railway_gql(query, variables=None, token=None):
    token = token or ACCESS_TOKEN
    data = json.dumps({"query": query, "variables": variables or {}}).encode()
    req = urllib.request.Request(
        "https://backboard.railway.com/graphql/v2",
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
            "User-Agent": "railway-cli/4.0.0",
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return {"error": e.code, "body": e.read().decode()[:500]}
    except Exception as e:
        return {"error": str(e)}

# 1. Check if accessToken is valid
print("Checking accessToken validity...")
me_query = "{ me { id email } }"
result = railway_gql(me_query)
print(f"  Result: {result}")

if "errors" in result or "error" in result:
    print("\nAccess token invalid, trying refresh token as auth...")
    # Try refreshToken as the bearer
    result2 = railway_gql(me_query, token=REFRESH_TOKEN)
    print(f"  Refresh token result: {result2}")
    
    if "errors" not in result2 and "error" not in result2:
        ACCESS_TOKEN = REFRESH_TOKEN
        print("Using refresh token as auth token")
    else:
        print("\nBoth tokens invalid.")
        
        # Try to refresh the access token
        print("Attempting token refresh via OAuth endpoint...")
        refresh_data = json.dumps({
            "query": """
            mutation refreshToken($refreshToken: String!) {
                refreshToken(refreshToken: $refreshToken) {
                    token
                    refreshToken
                }
            }
            """,
            "variables": {"refreshToken": REFRESH_TOKEN}
        }).encode()
        refresh_req = urllib.request.Request(
            "https://backboard.railway.com/graphql/v2",
            data=refresh_data,
            headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(refresh_req, timeout=15) as r:
                refresh_result = json.loads(r.read())
            print(f"  Refresh result: {refresh_result}")
        except Exception as e:
            print(f"  Refresh failed: {e}")
else:
    print("\nToken is VALID!")
    user = result.get("data", {}).get("me", {})
    print(f"  Logged in as: {user}")
    
    # 2. Get services in the project
    print("\nFetching project services...")
    services_query = """
    query getProject($projectId: String!) {
        project(id: $projectId) {
            name
            services {
                edges {
                    node {
                        id
                        name
                    }
                }
            }
        }
    }
    """
    services_result = railway_gql(services_query, {"projectId": PROJECT_ID})
    print(f"  Services: {json.dumps(services_result, indent=2)[:1000]}")
    
    # 3. Look for deployments and try to restart
    print("\nLooking for deployments to restart...")
    deploy_query = """
    query getDeployments($projectId: String!, $environmentId: String!) {
        deployments(
            input: {
                projectId: $projectId,
                environmentId: $environmentId
            }
            first: 10
        ) {
            edges {
                node {
                    id
                    status
                    serviceId
                    service { name }
                    createdAt
                }
            }
        }
    }
    """
    deploy_result = railway_gql(deploy_query, {
        "projectId": PROJECT_ID,
        "environmentId": ENVIRONMENT_ID
    })
    print(f"  Deployments: {json.dumps(deploy_result, indent=2)[:2000]}")
