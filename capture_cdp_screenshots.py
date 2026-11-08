"""CDP-based screenshot capture using Chrome headless remote debugging port and Python websockets."""
import asyncio
import json
import base64
import subprocess
import time
from pathlib import Path
import requests
import websockets

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
ARTIFACTS_DIR = Path(r"C:\Users\Rudra Panchal\.gemini\antigravity\brain\0d6d988e-63e9-4cc1-9101-b3a62cca0d13")
SCRATCH_DIR = Path(r"C:\Users\Rudra Panchal\.gemini\antigravity\scratch\bharattrip-refund-ops")

async def send_cmd(ws, method, params=None, msg_id=1):
    payload = {"id": msg_id, "method": method, "params": params or {}}
    await ws.send(json.dumps(payload))
    while True:
        resp = await ws.recv()
        data = json.loads(resp)
        if data.get("id") == msg_id:
            return data.get("result", {})

async def capture_views():
    print("1. Starting uvicorn on port 8008...")
    server = subprocess.Popen(
        ["python", "-m", "uvicorn", "api:app", "--host", "127.0.0.1", "--port", "8008"],
        cwd=str(SCRATCH_DIR),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    print("2. Prewarming cache...")
    for _ in range(30):
        try:
            r = requests.get("http://127.0.0.1:8008/api/summary", timeout=1)
            if r.status_code == 200:
                print("Server ready! Summary gap B count:", r.json().get("gap_b_count"))
                break
        except Exception:
            time.sleep(0.3)
    else:
        print("Server failed to prewarm.")
        server.terminate()
        return

    user_data = SCRATCH_DIR / ".chrome_tmp_profile"
    user_data.mkdir(exist_ok=True)

    print("3. Starting Chrome with remote debugging...")
    chrome_proc = subprocess.Popen([
        CHROME_PATH,
        "--headless=new",
        f"--user-data-dir={user_data}",
        "--remote-debugging-port=9222",
        "--hide-scrollbars",
        "--disable-gpu",
        "about:blank",
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    time.sleep(2)

    try:
        tabs = requests.get("http://127.0.0.1:9222/json", timeout=2).json()
        ws_url = tabs[0]["webSocketDebuggerUrl"]
        print("4. Connected to Chrome CDP:", ws_url)

        async with websockets.connect(ws_url, max_size=25*1024*1024) as ws:
            await send_cmd(ws, "Page.enable", {}, 1)

            tasks = [
                ("desktop_hero.png", 1440, 950, "http://127.0.0.1:8008/#hero"),
                ("desktop_leaks.png", 1440, 950, "http://127.0.0.1:8008/#leaks"),
                ("desktop_escalations.png", 1440, 950, "http://127.0.0.1:8008/#escalations"),
                ("desktop_queue.png", 1440, 950, "http://127.0.0.1:8008/#queue"),
                ("desktop_intake.png", 1440, 950, "http://127.0.0.1:8008/#intake"),
                ("mobile_hero.png", 375, 812, "http://127.0.0.1:8008/#hero"),
                ("mobile_leaks.png", 375, 812, "http://127.0.0.1:8008/#leaks"),
                ("mobile_queue.png", 375, 812, "http://127.0.0.1:8008/#queue"),
                ("mobile_intake.png", 375, 812, "http://127.0.0.1:8008/#intake"),
            ]

            msg_id = 10
            for filename, width, height, url in tasks:
                msg_id += 1
                await send_cmd(ws, "Emulation.setDeviceMetricsOverride", {
                    "width": width,
                    "height": height,
                    "deviceScaleFactor": 1,
                    "mobile": width < 600,
                }, msg_id)

                msg_id += 1
                await send_cmd(ws, "Page.navigate", {"url": url}, msg_id)
                # Wait 2.5s for React render and Recharts animations
                await asyncio.sleep(2.5)

                msg_id += 1
                res = await send_cmd(ws, "Page.captureScreenshot", {"format": "png"}, msg_id)
                img_data = base64.b64decode(res["data"])
                out_path = ARTIFACTS_DIR / filename
                out_path.write_bytes(img_data)
                print(f"Captured {filename}: {len(img_data)} bytes")

    finally:
        chrome_proc.terminate()
        server.terminate()
        print("Done.")

if __name__ == "__main__":
    asyncio.run(capture_views())
