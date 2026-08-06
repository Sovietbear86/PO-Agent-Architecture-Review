#!/usr/bin/env python3
"""Set Jira PLATFORM_SESSION cookie for MCP server."""
import json
import urllib.request
import urllib.error

# Ваш PLATFORM_SESSION cookie (скопируйте из браузера)
# Откройте DevTools -> Application -> Cookies -> PLATFORM_SESSION
PLATFORM_SESSION = '''YOUR_COOKIE_HERE'''

def set_cookie():
    """Set Jira PLATFORM_SESSION cookie."""
    url = 'http://localhost:3000/set-cookie'
    data = json.dumps({'platform_session': PLATFORM_SESSION}).encode()
    
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        result = json.loads(resp.read().decode())
        print(f"Success: {result}")
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.reason}")
        print(f"Response: {e.read().decode()[:300]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    set_cookie()
