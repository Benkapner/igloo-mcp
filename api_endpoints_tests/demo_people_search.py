#!/usr/bin/env python3
"""
Demo: People Search API Endpoints for Igloo

This script demonstrates the 3 API endpoints used by the people_search tool.
It calls each endpoint directly and shows the request and response.

Usage: run this command:
    uv run python demo_people_search.py "<some employee name>" 

The 3 API Endpoints Used:
    1. GET /.api/api.svc/search/members?q={query}     - Search for people by name
    2. GET /.api/api.svc/users/{id}/viewprofile       - Get detailed profile info
    3. GET /.api/api.svc/users/{id}/view              - Get user's name by ID (for manager lookup)
"""

import asyncio
import sys
import os
from dotenv import load_dotenv
import httpx

load_dotenv()

# Configuration from environment
COMMUNITY = os.getenv("IGLOO_MCP_COMMUNITY", "https://source.redhat.com")
APP_ID = os.getenv("IGLOO_MCP_APP_ID")
APP_PASS = os.getenv("IGLOO_MCP_APP_PASS")
USERNAME = os.getenv("IGLOO_MCP_USERNAME")
PASSWORD = os.getenv("IGLOO_MCP_PASSWORD")
PROXY = os.getenv("IGLOO_MCP_PROXY")


# =============================================================================
# AUTHENTICATION
# =============================================================================
# Before calling any API, we need to authenticate and get a session key.
# The session key is stored as a cookie named "iglooAuth".

async def authenticate(client: httpx.AsyncClient) -> bool:
    """Authenticate with Igloo API and set session cookie."""
    print("\n" + "=" * 60)
    print("STEP 0: AUTHENTICATION")
    print("=" * 60)
    print(f"Endpoint: POST /.api/api.svc/session/create")
    
    response = await client.post(
        f"{COMMUNITY}/.api/api.svc/session/create",
        params={
            "appId": APP_ID,
            "appPass": APP_PASS,
            "apiversion": 1,
            "community": COMMUNITY,
            "username": USERNAME,
            "password": PASSWORD,
        },
        headers={"Accept": "application/json"},
    )
    
    print(f"Response Status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"ERROR: HTTP {response.status_code}")
        return False
    
    data = response.json()
    session_key = data.get("response", {}).get("sessionKey")
    
    if session_key:
        client.cookies.set("iglooAuth", session_key)
        print(f"Result: SUCCESS - Got session key")
        return True
    
    print(f"ERROR: No session key in response")
    return False


# =============================================================================
# ENDPOINT 1: Search Members
# =============================================================================
# This endpoint searches for people by name (or partial name).
# It returns basic info: name, email, username, user_id.
#
# Request:  GET /.api/api.svc/search/members?q={query}
# Response: { "response": { "value": { "hit": [ { "id", "name", "email", "namespace" } ] } } }

async def search_members(client: httpx.AsyncClient, query: str) -> list[dict]:
    """
    ENDPOINT 1: Search for people by name.
    
    Request:  GET /.api/api.svc/search/members?q={query}
    Response: List of matching people with id, name, email, namespace (username)
    """
    print("\n" + "=" * 60)
    print("ENDPOINT 1: SEARCH MEMBERS")
    print("=" * 60)
    print(f"Request:  GET /.api/api.svc/search/members?q={query}")
    
    response = await client.get(
        f"{COMMUNITY}/.api/api.svc/search/members",
        params={"q": query},
        headers={"Accept": "application/json"},
    )
    
    print(f"Response Status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"ERROR: HTTP {response.status_code}")
        return []
    
    data = response.json()
    hits = data.get("response", {}).get("value", {}).get("hit", [])
    
    print(f"Result: Found {len(hits)} person(s)")
    
    # Transform API response to clean format
    results = []
    for hit in hits:
        name_info = hit.get("name", {})
        person = {
            "user_id": hit.get("id", ""),
            "full_name": name_info.get("fullName", "Unknown"),
            "first_name": name_info.get("firstName", ""),
            "last_name": name_info.get("lastName", ""),
            "email": hit.get("email", ""),
            "username": hit.get("namespace", ""),
            "profile_url": f"{COMMUNITY}/.profile/{hit.get('namespace', '')}",
        }
        results.append(person)
        
        # Show what we extracted from this hit
        print(f"\n  Person {len(results)}:")
        print(f"    user_id:   {person['user_id']}")
        print(f"    full_name: {person['full_name']}")
        print(f"    email:     {person['email']}")
        print(f"    username:  {person['username']}")
    
    return results


# =============================================================================
# ENDPOINT 2: Get User Profile
# =============================================================================
# This endpoint returns detailed profile info for a user.
# It includes: job title, department, manager, office, phone, start date, etc.
#
# Request:  GET /.api/api.svc/users/{user_id}/viewprofile
# Response: { "response": { "items": [ { "Name": "title", "Value": "Engineer" }, ... ] } }

async def get_user_profile(client: httpx.AsyncClient, user_id: str) -> dict:
    """
    ENDPOINT 2: Get detailed profile for a user.
    
    Request:  GET /.api/api.svc/users/{user_id}/viewprofile
    Response: List of profile fields (title, department, office, phone, etc.)
    """
    print("\n" + "=" * 60)
    print("ENDPOINT 2: GET USER PROFILE")
    print("=" * 60)
    print(f"Request:  GET /.api/api.svc/users/{user_id}/viewprofile")
    
    response = await client.get(
        f"{COMMUNITY}/.api/api.svc/users/{user_id}/viewprofile",
        headers={"Accept": "application/json"},
    )
    
    print(f"Response Status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"ERROR: HTTP {response.status_code}")
        return {}
    
    data = response.json()
    items = data.get("response", {}).get("items", [])
    
    print(f"Result: Got {len(items)} profile fields")
    
    # Map API field names to clean names
    field_mapping = {
        "title": "job_title",
        "department": "department",
        "i_report_to": "manager_id",
        "i_report_to_email": "manager_email",
        "office_location": "office",
        "desk_number": "desk",
        "busphone": "work_phone",
        "extension": "extension",
        "cellphone": "mobile",
        "work_start_date": "start_date",
    }
    
    # Skip these fields becuase we dont care about them
    skip_fields = {"bluejeans", "timezone"}
    
    profile = {}
    manager_id = None
    
    for item in items:
        field_name = item.get("Name", "")
        field_value = item.get("Value", "")
        
        if field_name in skip_fields:
            continue
        
        if not field_value or field_value in ["null", "https://bluejeans.com/null"]:
            continue
        
        # Capture manager ID for endpoint 3
        if field_name == "i_report_to":
            manager_id = field_value
            continue
        
        # Map to clean name
        clean_name = field_mapping.get(field_name, field_name)
        
        # Clean up date format
        if "date" in field_name and " " in str(field_value):
            field_value = str(field_value).split(" ")[0]
        
        profile[clean_name] = field_value
        print(f"  {clean_name}: {field_value}")
    
    # Store manager_id for endpoint 3
    if manager_id:
        profile["_manager_id"] = manager_id
        print(f"  manager_id: {manager_id} (will look up name in Endpoint 3)")
    
    return profile


# =============================================================================
# ENDPOINT 3: Get User Name by ID
# =============================================================================
# This endpoint returns a user's name given their ID.
# We use it to look up the manager's name from their ID.
#
# Request:  GET /.api/api.svc/users/{user_id}/view
# Response: { "response": { "name": { "fullName": "John Smith" } } }

async def get_user_name(client: httpx.AsyncClient, user_id: str) -> str | None:
    """
    ENDPOINT 3: Get user's name by their ID.
    
    Request:  GET /.api/api.svc/users/{user_id}/view
    Response: User info including name
    
    We use this to look up the manager's name from their ID.
    """
    print("\n" + "=" * 60)
    print("ENDPOINT 3: GET USER NAME BY ID")
    print("=" * 60)
    print(f"Request:  GET /.api/api.svc/users/{user_id}/view")
    print(f"Purpose:  Looking up manager's name")
    
    try:
        response = await client.get(
            f"{COMMUNITY}/.api/api.svc/users/{user_id}/view",
            headers={"Accept": "application/json"},
        )
        
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            name_info = data.get("response", {}).get("name", {})
            full_name = name_info.get("fullName")
            print(f"Result: {full_name}")
            return full_name
        else:
            print(f"ERROR: HTTP {response.status_code}")
            return None
    except Exception as e:
        print(f"ERROR: {e}")
        return None


# =============================================================================
# MAIN - Run all 3 endpoints
# =============================================================================

async def main():
    if len(sys.argv) < 2:
        print("\nUsage: uv run python demo_people_search.py \"NAME\"")
        print("\nExamples:")
        print("  uv run python demo_people_search.py \"John Smith\"")
        print("  uv run python demo_people_search.py \"Jane\"")
        print("\nThis script demonstrates the 3 API endpoints used by people_search:")
        print("  1. /.api/api.svc/search/members       - Search for people")
        print("  2. /.api/api.svc/users/{id}/viewprofile - Get profile details")
        print("  3. /.api/api.svc/users/{id}/view      - Get name by ID")
        sys.exit(1)
    
    query = sys.argv[1]
    
    print("\n" + "=" * 60)
    print("DEMO: PEOPLE SEARCH API ENDPOINTS")
    print("=" * 60)
    print(f"Query: \"{query}\"")
    print(f"Community: {COMMUNITY}")
    
    async with httpx.AsyncClient(proxy=PROXY, verify=True) as client:
        
        # Step 0: Authenticate
        if not await authenticate(client):
            print("\nERROR: Authentication failed. Check your .env configuration.")
            print("Required environment variables:")
            print("  IGLOO_MCP_COMMUNITY, IGLOO_MCP_APP_ID, IGLOO_MCP_APP_PASS")
            print("  IGLOO_MCP_USERNAME, IGLOO_MCP_PASSWORD")
            sys.exit(1)
        
        # Endpoint 1: Search for people
        results = await search_members(client, query)
        
        if not results:
            print("\nNo people found matching the query.")
            sys.exit(0)
        
        # Endpoint 2: Get profile for first result
        first_person = results[0]
        profile = await get_user_profile(client, first_person["user_id"])
        
        # Endpoint 3: Look up manager's name (if we have manager_id)
        manager_name = None
        if profile.get("_manager_id"):
            manager_name = await get_user_name(client, profile["_manager_id"])
            if manager_name:
                profile["manager_name"] = manager_name
        
        # Final summary
        print("\n" + "=" * 60)
        print("FINAL RESULT")
        print("=" * 60)
        print(f"\nPerson: {first_person['full_name']}")
        print(f"Email:  {first_person['email']}")
        print(f"Profile URL: {first_person['profile_url']}")
        
        if profile:
            print("\nProfile Details:")
            for key, value in profile.items():
                if not key.startswith("_"):  # Skip internal fields
                    print(f"  {key}: {value}")
        
        print("\n" + "=" * 60)
        print("DEMO COMPLETE")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
