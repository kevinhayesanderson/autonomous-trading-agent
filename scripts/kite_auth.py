"""
Zerodha Kite Connect v3 Authentication & Session Manager
Automates the OAuth 2.0 flow for Zerodha Kite Connect.
Catches the login callback on http://127.0.0.1:8000/ to extract request_token,
generates the daily access_token, and saves it to persistent memory.
"""

import os
import sys
import json
import webbrowser
from urllib.parse import urlparse, parse_qs
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

from kiteconnect import KiteConnect

TOKEN_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".kite_token.json"))
GLOBAL_TOKEN_FILE = os.path.expanduser("~/.kite_token.json")

def load_credentials():
    api_key = os.environ.get("KITE_API_KEY")
    api_secret = os.environ.get("KITE_API_SECRET")
    redirect_url = os.environ.get("KITE_REDIRECT_URL", "http://127.0.0.1:8000/")

    if not api_key or not api_secret:
        env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k, v = k.strip(), v.strip().strip("'\"")
                        if k == "KITE_API_KEY" and not api_key:
                            api_key = v
                        elif k == "KITE_API_SECRET" and not api_secret:
                            api_secret = v
                        elif k == "KITE_REDIRECT_URL":
                            redirect_url = v

    if not api_key or not api_secret:
        raise ValueError("Missing KITE_API_KEY or KITE_API_SECRET in environment or .env file.")

    return api_key, api_secret, redirect_url

class CallbackHandler(BaseHTTPRequestHandler):
    request_token = None

    def do_GET(self):
        query = urlparse(self.path).query
        params = parse_qs(query)
        if "request_token" in params:
            CallbackHandler.request_token = params["request_token"][0]
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            html = """
            <!DOCTYPE html>
            <html>
            <head><title>Zerodha Kite Auth Success</title></head>
            <body style="font-family: -apple-system, sans-serif; text-align: center; padding: 50px; background: #0f172a; color: #f8fafc;">
                <h1 style="color: #10b981;">&#10004; Zerodha Authentication Successful!</h1>
                <p style="font-size: 18px;">Access token is being generated. You can close this browser tab.</p>
            </body>
            </html>
            """
            self.wfile.write(html.encode("utf-8"))
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"No request_token found in callback.")

    def log_message(self, format, *args):
        pass

def save_token(session_data: dict):
    clean_data = {}
    for k, v in session_data.items():
        if hasattr(v, "isoformat"):
            clean_data[k] = v.isoformat()
        else:
            clean_data[k] = v
    clean_data["created_at"] = datetime.now().isoformat()
    for path in [TOKEN_FILE, GLOBAL_TOKEN_FILE]:
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(clean_data, f, indent=2, default=str)
            print(f"  * Session token saved to: {path}")
        except Exception as e:
            print(f"  [!] Note: could not write to {path}: {e}")

def authenticate(direct_token: str = None):
    api_key, api_secret, redirect_url = load_credentials()
    kite = KiteConnect(api_key=api_key)
    login_url = kite.login_url()

    # Check sys.argv for direct token
    if not direct_token:
        for i, arg in enumerate(sys.argv):
            if arg in ["--token", "-t"] and i + 1 < len(sys.argv):
                direct_token = sys.argv[i + 1]
            elif arg.startswith("--token="):
                direct_token = arg.split("=", 1)[1]
            elif arg in ["--url", "-u"] and i + 1 < len(sys.argv):
                direct_token = sys.argv[i + 1]
            elif arg.startswith("--url="):
                direct_token = arg.split("=", 1)[1]
            elif "request_token=" in arg:
                direct_token = arg

    if direct_token:
        if "request_token=" in direct_token:
            query = urlparse(direct_token).query or direct_token.split("?", 1)[-1]
            params = parse_qs(query)
            CallbackHandler.request_token = params.get("request_token", [direct_token])[0]
        else:
            CallbackHandler.request_token = direct_token.strip()

    if CallbackHandler.request_token:
        req_token = CallbackHandler.request_token
        print("=" * 80)
        print(" [ZERODHA KITE CONNECT v3 DIRECT TOKEN EXCHANGE]")
        print("=" * 80)
        print(f"  * Using provided request_token: {req_token[:6]}...{req_token[-4:]}")
        try:
            session = kite.generate_session(req_token, api_secret=api_secret)
            access_token = session.get("access_token")
            user_name = session.get("user_name", "Zerodha User")
            user_id = session.get("user_id", "")
            print("\n" + "=" * 80)
            print(f" [SUCCESS] Authenticated as: {user_name} ({user_id})")
            print(f" Access Token: {access_token[:6]}...{access_token[-4:]}")
            print("=" * 80)
            save_token(session)
            kite.set_access_token(access_token)
            margins = kite.margins(segment="equity")
            cash = margins.get("available", {}).get("cash", 0.0)
            print(f"  * Verified Available Cash in Zerodha: Rs {cash:,.2f} INR")
            return access_token
        except Exception as e:
            print(f"[ERROR] Failed to exchange request_token for access_token: {e}")
            sys.exit(1)

    parsed = urlparse(redirect_url)
    port = parsed.port or 8000
    host = parsed.hostname or "127.0.0.1"

    print("=" * 80)
    print(" [ZERODHA KITE CONNECT v3 AUTHENTICATION]")
    print("=" * 80)
    print(f"  * API Key:         {api_key[:4]}...{api_key[-4:]}")
    print(f"  * Callback URL:    {redirect_url}")
    print(f"  * Login URL:       {login_url}")
    print("\nOpening browser to authorize with Zerodha Kite...")

    try:
        webbrowser.open(login_url)
    except Exception as e:
        print(f"  [!] Could not open browser automatically: {e}")
        print(f"  -> Please open this URL manually: {login_url}")

    server = None
    try:
        server = HTTPServer((host, port), CallbackHandler)
        server.timeout = 120  # 2 minute timeout
        print(f"Waiting for Zerodha callback on http://{host}:{port}/ ...")
        while CallbackHandler.request_token is None:
            server.handle_request()
    except Exception as e:
        print(f"  [!] Local server notice: {e}")
        print("  -> If browser redirect failed, paste the full redirected URL or request_token below:")
        user_input = input("Enter request_token or full redirect URL: ").strip()
        if "request_token=" in user_input:
            query = urlparse(user_input).query
            params = parse_qs(query)
            CallbackHandler.request_token = params.get("request_token", [None])[0]
        else:
            CallbackHandler.request_token = user_input
    finally:
        if server:
            server.server_close()

    req_token = CallbackHandler.request_token
    if not req_token:
        print("[ERROR] Failed to obtain request_token.")
        sys.exit(1)

    print(f"\n[+] Obtained request_token: {req_token[:6]}...{req_token[-4:]}")
    print("Generating persistent access token session...")

    try:
        session = kite.generate_session(req_token, api_secret=api_secret)
        access_token = session.get("access_token")
        user_name = session.get("user_name", "Zerodha User")
        user_id = session.get("user_id", "")
        
        print("\n" + "=" * 80)
        print(f" [SUCCESS] Authenticated as: {user_name} ({user_id})")
        print(f" Access Token: {access_token[:6]}...{access_token[-4:]}")
        print("=" * 80)

        save_token(session)

        # Test margins
        kite.set_access_token(access_token)
        margins = kite.margins(segment="equity")
        cash = margins.get("available", {}).get("cash", 0.0)
        print(f"  * Verified Available Cash in Zerodha: Rs {cash:,.2f} INR")

        return access_token
    except Exception as e:
        print(f"[ERROR] Failed to exchange request_token for access_token: {e}")
        sys.exit(1)

if __name__ == "__main__":
    authenticate()
