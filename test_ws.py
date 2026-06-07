import asyncio
import websockets
import sys

async def test_ws():
    # We need a valid session_id. Let's just use a dummy one.
    uri = "ws://localhost:8000/api/v1/ws/terminal/dummy-session-123"
    async with websockets.connect(uri) as websocket:
        print("Connected.")
        
        # Start a listener task
        async def listen():
            while True:
                msg = await websocket.recv()
                print("Received:", msg)
                
        asyncio.create_task(listen())
        
        await websocket.send("ls\r")
        print("Sent ls")
        await asyncio.sleep(2)
        
        await websocket.send("echo hello\r")
        print("Sent echo hello")
        await asyncio.sleep(2)

asyncio.run(test_ws())
