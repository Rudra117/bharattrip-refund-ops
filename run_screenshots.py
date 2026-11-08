import subprocess
import time
import requests
from pathlib import Path

SCRATCH_DIR = Path(r"C:\Users\Rudra Panchal\.gemini\antigravity\scratch\bharattrip-refund-ops")
FRONTEND_DIR = SCRATCH_DIR / "frontend"

def main():
    print("Starting uvicorn server on port 8008...")
    server = subprocess.Popen(
        ["python", "-m", "uvicorn", "api:app", "--host", "127.0.0.1", "--port", "8008"],
        cwd=str(SCRATCH_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    try:
        for _ in range(40):
            if server.poll() is not None:
                out, err = server.communicate()
                print("Server exited early with code:", server.returncode)
                print("STDOUT:", out)
                print("STDERR:", err)
                return
            try:
                r = requests.get("http://127.0.0.1:8008/api/summary", timeout=1)
                if r.status_code == 200:
                    print("Server ready! Gap B count:", r.json().get("gap_b_count"))
                    break
            except Exception:
                time.sleep(0.5)
        else:
            print("Failed to start server within timeout")
            return

        print("Running take_screenshots.mjs...")
        res = subprocess.run(
            ["node", "take_screenshots.mjs"],
            cwd=str(FRONTEND_DIR),
            capture_output=True,
            text=True,
            timeout=60,
        )
        print("STDOUT:", res.stdout)
        print("STDERR:", res.stderr)
        if res.returncode != 0:
            print("Failed with returncode", res.returncode)

    finally:
        server.terminate()
        print("Server terminated.")

if __name__ == "__main__":
    main()
