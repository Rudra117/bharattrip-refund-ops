import subprocess
import time
from pathlib import Path
import requests

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
ARTIFACTS_DIR = Path(r"C:\Users\Rudra Panchal\.gemini\antigravity\brain\0d6d988e-63e9-4cc1-9101-b3a62cca0d13")
SCRATCH_DIR = Path(r"C:\Users\Rudra Panchal\.gemini\antigravity\scratch\bharattrip-refund-ops")

def run():
    print("Starting server on port 8008...")
    server = subprocess.Popen(
        ["python", "-m", "uvicorn", "api:app", "--host", "127.0.0.1", "--port", "8008"],
        cwd=str(SCRATCH_DIR),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        for _ in range(30):
            try:
                r = requests.get("http://127.0.0.1:8008/api/summary", timeout=1)
                if r.status_code == 200:
                    print("API cache ready:", r.json().get("gap_b_count"))
                    break
            except Exception:
                time.sleep(0.3)
        else:
            print("Failed to start server")
            return

        targets = [
            ("screenshot_desktop_hero.png", 1440, 950, "http://127.0.0.1:8008/#hero"),
            ("screenshot_desktop_leaks.png", 1440, 950, "http://127.0.0.1:8008/#leaks"),
            ("screenshot_desktop_escalations.png", 1440, 950, "http://127.0.0.1:8008/#escalations"),
            ("screenshot_desktop_queue.png", 1440, 950, "http://127.0.0.1:8008/#queue"),
            ("screenshot_desktop_intake.png", 1440, 950, "http://127.0.0.1:8008/#intake"),
            ("screenshot_mobile_hero.png", 375, 812, "http://127.0.0.1:8008/#hero"),
            ("screenshot_mobile_leaks.png", 375, 812, "http://127.0.0.1:8008/#leaks"),
            ("screenshot_mobile_escalations.png", 375, 812, "http://127.0.0.1:8008/#escalations"),
            ("screenshot_mobile_queue.png", 375, 812, "http://127.0.0.1:8008/#queue"),
            ("screenshot_mobile_intake.png", 375, 812, "http://127.0.0.1:8008/#intake"),
        ]

        for filename, width, height, url in targets:
            out_file = ARTIFACTS_DIR / filename
            cmd = [
                CHROME_PATH,
                "--headless=new",
                "--hide-scrollbars",
                "--virtual-time-budget=4000",
                f"--window-size={width},{height}",
                f"--screenshot={out_file}",
                url,
            ]
            subprocess.run(cmd, capture_output=True, timeout=20)
            sz = out_file.stat().st_size if out_file.exists() else 0
            print(f"Captured {filename}: {sz} bytes")

    finally:
        server.terminate()
        print("Server stopped.")

if __name__ == "__main__":
    run()
