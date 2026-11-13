"""Minimal Chrome DevTools Protocol driver (test harness only; the game itself ships no script)."""
import asyncio
import base64
import json
import os
import pathlib
import shutil
import subprocess
import tempfile
import time
import urllib.request

import websockets

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"


class Browser:
    async def start(self, headless=True, width=1280, height=800):
        self.dir = tempfile.mkdtemp(prefix="cdp-")
        args = [
            CHROME,
            f"--user-data-dir={self.dir}",
            "--remote-debugging-port=0",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-extensions",
            "--allow-file-access-from-files",
            f"--window-size={width},{height}",
            "about:blank",
        ]
        if headless:
            args.insert(1, "--headless=new")
        self.proc = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        port_file = pathlib.Path(self.dir, "DevToolsActivePort")
        deadline = time.time() + 20
        while not port_file.exists():
            if time.time() > deadline:
                raise RuntimeError("chrome did not start")
            await asyncio.sleep(0.1)
        await asyncio.sleep(0.2)
        port = int(port_file.read_text().split()[0])
        targets = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{port}/json").read())
        page = next(t for t in targets if t["type"] == "page")
        self.ws = await websockets.connect(page["webSocketDebuggerUrl"], max_size=2**28)
        self.seq = 0
        self.pending = {}
        self.listeners = []
        self.reader = asyncio.create_task(self._read())
        await self.send("Page.enable")
        await self.send("Runtime.enable")
        await self.send("Performance.enable")
        return self

    async def _read(self):
        async for raw in self.ws:
            msg = json.loads(raw)
            if "id" in msg:
                fut = self.pending.pop(msg["id"], None)
                if fut and not fut.done():
                    if "error" in msg:
                        fut.set_exception(RuntimeError(f"{msg['error']}"))
                    else:
                        fut.set_result(msg.get("result", {}))
            else:
                if msg.get("method") == "Runtime.consoleAPICalled":
                    args = msg["params"]["args"]
                    print("console:", *[a.get("value", a.get("description")) for a in args])
                if msg.get("method") == "Runtime.exceptionThrown":
                    print("exception:", msg["params"]["exceptionDetails"].get("text"))
                for q in list(self.listeners):
                    q.put_nowait(msg)

    async def send(self, method, params=None):
        self.seq += 1
        fut = asyncio.get_running_loop().create_future()
        self.pending[self.seq] = fut
        await self.ws.send(json.dumps({"id": self.seq, "method": method, "params": params or {}}))
        return await fut

    async def eval(self, expr):
        res = await self.send(
            "Runtime.evaluate",
            {"expression": expr, "returnByValue": True, "awaitPromise": True},
        )
        if "exceptionDetails" in res:
            raise RuntimeError(res["exceptionDetails"])
        return res["result"].get("value")

    async def goto(self, url, settle=0.5, timeout=30):
        q = asyncio.Queue()
        self.listeners.append(q)
        await self.send("Page.navigate", {"url": url})
        while True:
            msg = await asyncio.wait_for(q.get(), timeout)
            if msg.get("method") == "Page.loadEventFired":
                break
        self.listeners.remove(q)
        await asyncio.sleep(settle)

    async def viewport(self, width, height, scale=1):
        await self.send(
            "Emulation.setDeviceMetricsOverride",
            {"width": width, "height": height, "deviceScaleFactor": scale, "mobile": False},
        )

    async def mouse(self, kind, x, y, button="none", buttons=0):
        await self.send(
            "Input.dispatchMouseEvent",
            {"type": kind, "x": x, "y": y, "button": button, "buttons": buttons, "clickCount": 1 if kind != "mouseMoved" else 0},
        )

    async def screenshot(self, path):
        res = await self.send("Page.captureScreenshot", {"format": "png"})
        pathlib.Path(path).write_bytes(base64.b64decode(res["data"]))

    async def metrics(self):
        res = await self.send("Performance.getMetrics")
        return {m["name"]: m["value"] for m in res["metrics"]}

    async def close(self):
        self.reader.cancel()
        await self.ws.close()
        self.proc.terminate()
        try:
            self.proc.wait(5)
        except subprocess.TimeoutExpired:
            self.proc.kill()
        shutil.rmtree(self.dir, ignore_errors=True)


def file_url(path):
    return pathlib.Path(path).resolve().as_uri()
