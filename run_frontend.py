import sys
import os
import subprocess
import webbrowser
import time
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()
FRONTEND_DIR = BASE_DIR / "frontend"
INDEX_HTML = FRONTEND_DIR / "index.html"
SLIDES_HTML = FRONTEND_DIR / "slides.html"
MOCK_SERVER = BASE_DIR / "mock_system" / "be2_mock_server.py"

def print_banner():
    print("=" * 72)
    print("  AEGIS-OS :: FE1 (FRONTEND LEAD) MISSION CONTROL SUITE")
    print("=" * 72)

def main():
    print_banner()
    print(f"[*] Base Directory: {BASE_DIR}")
    print(f"[+] Verified index.html: {INDEX_HTML.exists()}")
    print(f"[+] Verified slides.html: {SLIDES_HTML.exists()}")
    print(f"[+] Verified BE2 mock server: {MOCK_SERVER.exists()}")
    print("=" * 72)

    choice = "1"
    if len(sys.argv) > 1:
        choice = sys.argv[1]
    else:
        print("Launch Options:")
        print("  1. Launch Mission Control HUD (frontend/index.html)")
        print("  2. Launch Executive Pitch Deck (frontend/slides.html)")
        print("  3. Launch Both HUD + Background BE2 Mock Telemetry Server")
        print("  4. Run Automated Backend Verification Pipeline")
        print("  5. Exit")
        try:
            choice = input("\nEnter choice [1-5] (default: 1): ").strip() or "1"
        except (EOFError, KeyboardInterrupt):
            choice = "1"

    if choice == "1":
        print("[*] Opening Mission Control HUD in default browser...")
        webbrowser.open(INDEX_HTML.as_uri())
    elif choice == "2":
        print("[*] Opening Executive Pitch Deck in default browser...")
        webbrowser.open(SLIDES_HTML.as_uri())
    elif choice == "3":
        print("[*] Starting BE2 Mock Telemetry Server on http://localhost:8000...")
        subprocess.Popen([sys.executable, str(MOCK_SERVER), "8000"], creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0)
        time.sleep(1)
        print("[*] Opening Mission Control HUD connected to localhost:8000...")
        webbrowser.open(f"{INDEX_HTML.as_uri()}?host=localhost:8000")
    elif choice == "4":
        print("[*] Running live system runner pipeline...")
        subprocess.run([sys.executable, str(BASE_DIR / "live_system_runner.py")])
    else:
        print("Exiting.")

if __name__ == "__main__":
    main()
