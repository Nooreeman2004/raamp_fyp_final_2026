import asyncio
import websockets
import subprocess
import time
import os
import signal

async def test_ws_live():
    # Start server
    print("Starting server...")
    proc = subprocess.Popen(
        ["python", "main.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd="d:/raamp-fyp-final/raamp-backend"
    )
    
    # Wait for server to start
    time.sleep(10)
    
    uri = "ws://127.0.0.1:8000/api/notifications/ws"
    print(f"Connecting to {uri}...")
    try:
        # Standard handshake
        async with websockets.connect(uri) as websocket:
            print("Connected!")
            await websocket.send("ping")
            response = await websocket.recv()
            print(f"Received: {response}")
    except Exception as e:
        print(f"Connection failed: {e}")
        # Get server output
        out, err = proc.communicate(timeout=1)
        print("Server STDOUT:")
        print(out)
        print("Server STDERR:")
        print(err)
    finally:
        # Kill server
        os.kill(proc.pid, signal.SIGTERM)

if __name__ == "__main__":
    asyncio.run(test_ws_live())
