"""
Zerodha Kite Connect v3 Authentication & Session Manager
Automates the OAuth 2.0 flow for Zerodha Kite Connect.
Catches the login callback on http://127.0.0.1:8000/ to extract request_token,
generates the daily access_token, and saves it to persistent memory.
"""

import os
import sys
import json
import time
import webbrowser
from urllib.parse import urlparse, parse_qs
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

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

class ReusableHTTPServer(HTTPServer):
    allow_reuse_address = True

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
            <head>
                <title>Zerodha Kite Auth Success</title>
                <script>
                    setTimeout(() => {
                        try { window.close(); } catch(e) {}
                    }, 1500);
                </script>
            </head>
            <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; text-align: center; padding: 50px 20px; background: #0f172a; color: #f8fafc;">
                <div style="max-width: 480px; margin: 40px auto; background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 32px; box-shadow: 0 10px 25px rgba(0,0,0,0.5);">
                    <h1 style="color: #10b981; margin-top: 0;">&#10004; Authentication Successful!</h1>
                    <p style="font-size: 16px; color: #cbd5e1;">Zerodha Kite Connect session is now active.</p>
                    <p style="font-size: 14px; color: #94a3b8; margin-top: 20px;">You can close this tab and return to your agent terminal.</p>
                </div>
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

def open_url_in_browser(url: str):
    """Reliably opens a URL in Google Chrome or default browser on Windows / cross-platform."""
    import subprocess
    if sys.platform == "win32":
        # 1. Native Windows Explorer shell (guarantees interactive desktop browser launch)
        try:
            subprocess.Popen(f'explorer.exe "{url}"', shell=True)
            return
        except Exception:
            pass

        # 2. Try launching Chrome executable directly without cmd.exe
        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")
        ]
        for cp in chrome_paths:
            if os.path.exists(cp):
                try:
                    subprocess.Popen([cp, url], shell=False)
                    return
                except Exception:
                    pass

        # 3. Try Windows cmd start with caret-escaped ampersands
        try:
            escaped = url.replace("&", "^&")
            subprocess.Popen(f'cmd.exe /c start "" "{escaped}"', shell=True)
            return
        except Exception:
            pass

    try:
        webbrowser.open(url)
    except Exception:
        pass

def seamless_authenticate(timeout_seconds: int = 60, open_browser: bool = True):
    """
    Seamless background authentication for Zerodha Kite Connect v3:
    1. Spins up local callback server on http://127.0.0.1:8000/
    2. Opens default browser to Kite login URL (where user already has an active Kite session)
    3. Kite automatically redirects to local callback with request_token
    4. Automatically exchanges request_token for access_token, saves to .kite_token.json, and returns token.
    Returns access_token on success, or None on timeout/failure.
    """
    try:
        api_key, api_secret, redirect_url = load_credentials()
    except Exception as e:
        print(f"  [!] Kite credentials missing: {e}", flush=True)
        return None

    kite = KiteConnect(api_key=api_key)
    login_url = kite.login_url()

    parsed = urlparse(redirect_url)
    port = parsed.port or 8000
    host = parsed.hostname or "127.0.0.1"

    CallbackHandler.request_token = None

    server = None
    try:
        server = ReusableHTTPServer((host, port), CallbackHandler)
        server.timeout = 1.0  # 1 second poll tick
    except Exception as e:
        print(f"  [!] Could not start local callback server on {host}:{port}: {e}", flush=True)
        return None

    if open_browser and not os.environ.get("HEADLESS"):
        print(f"  * Launching browser with Zerodha Kite authorization URL...", flush=True)
        print(f"    -> {login_url}", flush=True)
        open_url_in_browser(login_url)

    print(f"  * Listening on http://{host}:{port}/ for callback (waiting up to {timeout_seconds}s)...", flush=True)
    print(f"    -> If prompted in your browser tab, please click 'Authorize'...", flush=True)
    start_time = time.time()
    try:
        while CallbackHandler.request_token is None:
            if time.time() - start_time > timeout_seconds:
                print(f"  [!] Seamless browser authorization timed out after {timeout_seconds}s.", flush=True)
                break
            server.handle_request()
    finally:
        if server:
            server.server_close()

    req_token = CallbackHandler.request_token
    if not req_token:
        return None

    print(f"  [+] Captured request_token seamlessly: {req_token[:6]}...{req_token[-4:]}", flush=True)
    try:
        session = kite.generate_session(req_token, api_secret=api_secret)
        access_token = session.get("access_token")
        user_name = session.get("user_name", "Zerodha User")
        user_id = session.get("user_id", "")
        print(f"  [SUCCESS] Authenticated as: {user_name} ({user_id})", flush=True)
        save_token(session)
        kite.set_access_token(access_token)
        margins = kite.margins(segment="equity")
        cash = margins.get("available", {}).get("cash", 0.0)
        print(f"  * Verified Available Cash in Zerodha: Rs {cash:,.2f} INR", flush=True)
        return access_token
    except Exception as e:
        print(f"  [!] Failed to exchange request_token: {e}", flush=True)
        return None

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

    # First attempt seamless browser authorization
    tok = seamless_authenticate(timeout_seconds=30, open_browser=True)
    if tok:
        return tok

    # If seamless failed, fallback to interactive prompt if in interactive tty
    if sys.stdin.isatty():
        print("\n  -> If browser redirect failed, paste the full redirected URL or request_token below:")
        try:
            user_input = input("Enter request_token or full redirect URL: ").strip()
            if user_input:
                return authenticate(direct_token=user_input)
        except Exception:
            pass

    print("[ERROR] Failed to obtain request_token.")
    sys.exit(1)

if __name__ == "__main__":
    authenticate()
