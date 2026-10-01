"""
Tickertape OAuth 2.1 PKCE Authentication & Auto-Refresh Manager
Provides automated token refresh so monthly and daily cycles never fail due to expired JWTs.
"""

import os
import sys
import json
import time
import base64
import hashlib
import urllib.parse
import urllib.request
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler

def load_env():
    candidates = [
        os.path.join(os.path.dirname(__file__), "..", ".env"),
        os.path.join(os.getcwd(), ".env")
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            k, v = k.strip(), v.strip().strip("'\"")
                            if k and k not in os.environ:
                                os.environ[k] = v
                break
            except Exception:
                pass

load_env()

PORT = 8080
REDIRECT_URI = f"http://localhost:{PORT}/callback"
AUTH_SERVER = "https://auth.api.tickertape.in"
MCP_ENDPOINT = "https://mcp.tickertape.in/mcp"
CONFIG_FILE = os.environ.get("MCP_CONFIG_FILE", os.path.join(os.path.expanduser("~"), ".gemini", "config", "mcp_config.json"))
TOKEN_FILE = os.environ.get("TICKERTAPE_TOKEN_FILE", os.path.join(os.path.expanduser("~"), ".gemini", "config", "tickertape_token.json"))
LOCAL_TOKEN_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "tickertape_token.json"))
ENV_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))

def register_public_oauth_client():
    url = f"{AUTH_SERVER}/oauth/register"
    payload = {
        "client_name": "Antigravity Assistant US Quant Bot",
        "redirect_uris": [REDIRECT_URI],
        "grant_types": ["authorization_code", "refresh_token"],
        "response_types": ["code"],
        "token_endpoint_auth_method": "none"
    }
    if not url.startswith("https://"):
        raise ValueError("Insecure registration URL scheme")
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": "Antigravity/1.0"}
    )
    with urllib.request.urlopen(req) as resp:  # nosec B310
        data = json.loads(resp.read().decode("utf-8"))
        return data["client_id"]

def generate_pkce():
    code_verifier = base64.urlsafe_b64encode(os.urandom(40)).decode("utf-8").rstrip("=")
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode("utf-8")).digest()
    ).decode("utf-8").rstrip("=")
    return code_verifier, code_challenge

auth_code = None

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/callback":
            params = urllib.parse.parse_qs(parsed.query)
            if "code" in params:
                auth_code = params["code"][0]
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                html = """
                <html>
                <body style="font-family:sans-serif;text-align:center;padding:50px;">
                  <h2 style="color:#10b981;">✓ Tickertape Authorization Successful</h2>
                  <p>Antigravity US Quant Bot is now connected. You can close this window.</p>
                </body>
                </html>
                """
                self.wfile.write(html.encode("utf-8"))
            else:
                self.send_response(400)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

def exchange_code_for_token(client_id, code, code_verifier):
    token_url = f"{AUTH_SERVER}/oauth/token"
    if not token_url.startswith("https://"):
        raise ValueError("Insecure token URL scheme")
    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": client_id,
        "code_verifier": code_verifier
    }
    encoded = urllib.parse.urlencode(payload).encode("utf-8")
    req = urllib.request.Request(
        token_url,
        data=encoded,
        headers={"Content-Type": "application/x-www-form-urlencoded", "User-Agent": "Antigravity/1.0"}
    )
    with urllib.request.urlopen(req) as resp:  # nosec B310
        return json.loads(resp.read().decode("utf-8"))

def save_token_atomic(token_data):
    """Atomically writes token data to prevent 0-byte file corruption if interrupted."""
    for tf in [TOKEN_FILE, LOCAL_TOKEN_FILE]:
        tmp_path = tf + ".tmp"
        try:
            os.makedirs(os.path.dirname(tf), exist_ok=True)
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(token_data, f, indent=2)
            os.replace(tmp_path, tf)
        except Exception as e:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
    
    # Also update .env if present
    acc = token_data.get("access_token")
    if acc and os.path.exists(ENV_FILE):
        try:
            with open(ENV_FILE, "r", encoding="utf-8") as f:
                lines = f.readlines()
            found = False
            for i, line in enumerate(lines):
                if line.startswith("TICKERTAPE_TOKEN="):
                    lines[i] = f"TICKERTAPE_TOKEN={acc}\n"
                    found = True
                    break
            if not found:
                lines.append(f"\nTICKERTAPE_TOKEN={acc}\n")
            with open(ENV_FILE, "w", encoding="utf-8") as f:
                f.writelines(lines)
        except Exception:
            pass

def refresh_access_token(client_id, refresh_token, max_retries=3):
    token_url = f"{AUTH_SERVER}/oauth/token"
    if not token_url.startswith("https://"):
        raise ValueError("Insecure token URL scheme")
    payload = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": client_id
    }
    encoded = urllib.parse.urlencode(payload).encode("utf-8")
    req = urllib.request.Request(
        token_url,
        data=encoded,
        headers={"Content-Type": "application/x-www-form-urlencoded", "User-Agent": "Antigravity/1.0"}
    )
    for attempt in range(1, max_retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=12) as resp:  # nosec B310
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore") if hasattr(e, "read") else ""
            if e.code in [400, 401]:
                return {"error": "invalid_grant", "details": err_body}
            if attempt == max_retries:
                raise
        except Exception as e:
            if attempt == max_retries:
                raise
            time.sleep(attempt * 1.5)
    return {"error": "refresh_timeout"}

def update_mcp_config(access_token):
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            if "mcpServers" not in cfg:
                cfg["mcpServers"] = {}
            if "tickertape" not in cfg["mcpServers"]:
                cfg["mcpServers"]["tickertape"] = {"type": "http", "url": MCP_ENDPOINT}
            if "headers" not in cfg["mcpServers"]["tickertape"]:
                cfg["mcpServers"]["tickertape"]["headers"] = {}
            cfg["mcpServers"]["tickertape"]["headers"]["Authorization"] = f"Bearer {access_token}"
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=2)
        except Exception as e:
            print(f"[!] Warning: Could not update {CONFIG_FILE}: {e}")

def get_valid_token(force_login=False):
    """Returns a valid access token, auto-refreshing if expired."""
    global auth_code
    token_data = None
    if not force_login:
        for tf in [LOCAL_TOKEN_FILE, TOKEN_FILE]:
            if os.path.exists(tf):
                try:
                    with open(tf, "r", encoding="utf-8") as f:
                        token_data = json.load(f)
                        if token_data and "access_token" in token_data:
                            break
                except Exception:
                    token_data = None

        now = time.time()
        if token_data:
            access_token = token_data.get("access_token")
            expires_at = token_data.get("expires_at", 0)
            client_id = token_data.get("client_id")
            refresh_token = token_data.get("refresh_token")

            # If token is valid for at least 5 more minutes and was issued via OAuth client, use it
            if access_token and client_id and expires_at > (now + 300):
                return access_token

            # If expired but we have refresh_token and client_id, auto-refresh!
            if client_id and refresh_token:
                try:
                    new_tokens = refresh_access_token(client_id, refresh_token)
                    new_access = new_tokens.get("access_token")
                    if new_access:
                        token_data["access_token"] = new_access
                        if "refresh_token" in new_tokens:
                            token_data["refresh_token"] = new_tokens["refresh_token"]
                        token_data["expires_at"] = now + new_tokens.get("expires_in", 3600)
                        save_token_atomic(token_data)
                        update_mcp_config(new_access)
                        return new_access
                except Exception as e:
                    print(f"[!] Token refresh failed: {e}. Re-authenticating...")

    # Otherwise perform interactive login
    if os.environ.get("HEADLESS"):
        # If in headless/cron, fall back to whatever access token is available in mcp_config.json
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    h = cfg.get("mcpServers", {}).get("tickertape", {}).get("headers", {}).get("Authorization", "")
                    if h.startswith("Bearer "):
                        return h.split("Bearer ")[1].strip()
            except Exception:
                pass
        raise RuntimeError("Tickertape refresh token expired and running in HEADLESS environment.")

    print("\n--- TICKERTAPE OAUTH LOGIN REQUIRED ---", flush=True)
    client_id = register_public_oauth_client()
    verifier, challenge = generate_pkce()
    state = base64.urlsafe_b64encode(os.urandom(16)).decode("utf-8").rstrip("=")
    
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "scope": "market_data portfolio trade",
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "state": state
    }
    url = f"{AUTH_SERVER}/oauth/authorize?" + urllib.parse.urlencode(params)
    print("Opening browser for 1-click Tickertape approval...", flush=True)
    print(f"\nAUTH_URL: {url}\n", flush=True)
    try:
        webbrowser.open(url)
    except Exception:
        pass

    auth_code = None
    print(f"Listening on http://localhost:{PORT}/callback for authorization callback (timeout: 5 minutes)...", flush=True)
    print("Please approve access in your browser.", flush=True)
    server = HTTPServer(("127.0.0.1", PORT), OAuthCallbackHandler)
    server.timeout = 300
    while auth_code is None:
        server.handle_request()
    server.server_close()

    new_toks = exchange_code_for_token(client_id, auth_code, verifier)
    new_toks["client_id"] = client_id
    new_toks["expires_at"] = time.time() + new_toks.get("expires_in", 3600)
    
    save_token_atomic(new_toks)
    update_mcp_config(new_toks["access_token"])
    print("[SUCCESS] Tickertape authenticated and token saved with auto-refresh capability.")
    return new_toks["access_token"]

if __name__ == "__main__":
    force = "--check" not in sys.argv
    tok = get_valid_token(force_login=force)
    print("Active Token (first 25 chars):", tok[:25] + "...")
