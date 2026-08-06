#!/usr/bin/env python3
"""Set JSESSIONID cookie for Jira MCP Server."""

import os
import sys
import urllib.request
import json

def set_cookie(cookie_value: str):
    """Set JSESSIONID cookie on the MCP server."""
    if not cookie_value:
        print("Error: Cookie value is empty")
        return
    
    data = json.dumps({"jsessionid": cookie_value}).encode()
    req = urllib.request.Request(
        "http://localhost:3000/set-cookie",
        data=data,
        headers={"Content-Type": "application/json"}
    )
    
    try:
        resp = urllib.request.urlopen(req, timeout=5)
        result = json.loads(resp.read().decode())
        print(f"Response: {result}")
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code} - {e.read().decode()}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Get cookie from command line or environment
    cookie = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("JSESSIONID", "")
    
    if not cookie:
        print("Usage: python3 set_cookie.py <JSESSIONID>")
        print("Or: export JSESSIONID=<cookie> && python3 set_cookie.py")
        sys.exit(1)
    
    print(f"Setting cookie: {cookie[:20]}...")
    set_cookie(cookie)
