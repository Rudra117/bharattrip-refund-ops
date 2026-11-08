import subprocess
import time
import socket
import sys
from pathlib import Path

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
ARTIFACTS_DIR = Path(r"C:\Users\Rudra Panchal\.gemini\antigravity\brain\0d6d988e-63e9-4cc1-9101-b3a62cca0d13")
SCRATCH_DIR = Path(r"C:\Users\Rudra Panchal\.gemini\antigravity\scratch\bharattrip-refund-ops")

def is_port_open(port=8000):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(('127.0.0.1', port)) == 0

def capture():
    print("Starting uvicorn server...")
    server = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "api:app", "--port", "8000"],
        cwd=str(SCRATCH_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
        for _ in range(30):
            if is_port_open(8000):
                print("Server is listening on port 8000!")
                break
            time.sleep(0.5)
        else:
            print("Server failed to start in time.")
            return

        time.sleep(2)

        screenshots = [
            ("desktop_hero.png", 1440, 950, "http://127.0.0.1:8000/#hero"),
            ("desktop_leaks.png", 1440, 950, "http://127.0.0.1:8000/#leaks"),
            ("desktop_escalations.png", 1440, 950, "http://127.0.0.1:8000/#escalations"),
            ("desktop_queue.png", 1440, 950, "http://127.0.0.1:8000/#queue"),
            ("desktop_intake.png", 1440, 950, "http://127.0.0.1:8000/#intake"),
            ("mobile_hero.png", 375, 812, "http://127.0.0.1:8000/#hero"),
            ("mobile_leaks.png", 375, 812, "http://127.0.0.1:8000/#leaks"),
            ("mobile_queue.png", 375, 812, "http://127.0.0.1:8000/#queue"),
            ("mobile_intake.png", 375, 812, "http://127.0.0.1:8000/#intake"),
        ]

        for filename, width, height, url in screenshots:
            out_path = ARTIFACTS_DIR / filename
            cmd = [
                CHROME_PATH,
                "--headless=new",
                "--disable-gpu",
                "--hide-scrollbars",
                "--virtual-time-budget=4000",
                f"--window-size={width},{height}",
                f"--screenshot={out_path}",
                url,
            ]
            subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            print(f"Captured {filename}: {out_path.exists()} ({out_path.stat().st_size if out_path.exists() else 0} bytes)")

    finally:
        print("Stopping uvicorn server...")
        server.terminate()
        try:
            server.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server.kill()

if __name__ == "__main__":
    capture()
