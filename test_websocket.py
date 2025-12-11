import asyncio
import websockets
import json

async def test_workflow():
    uri = "ws://127.0.0.1:8000/ws/code-review"
    async with websockets.connect(uri) as websocket:
        print("Connected to WebSocket")

        # 1. Send bad code
        bad_code = """
def bad(x):
    unused = 1
    a = 1
    b = 2
    c = 3
    d = 4
    e = 5
    f = 6
    g = 7
    h = 8
    i = 9
    return x
"""
        print(f"\nSending BAD code:\n{bad_code}")
        await websocket.send(json.dumps({"code": bad_code, "threshold": 0.8}))
        
        response = await websocket.recv()
        data = json.loads(response)
        print("\nServer Response 1:")
        print(f"Score: {data['quality_score']}")
        print(f"Accepted: {data['accepted']}")
        print(f"Message: {data['message']}")
        print(f"Suggestions: {data['suggestions']}")

        # 2. Simulate user fixing code
        good_code = """
def good(x):
    return x * 2
"""
        print(f"\nSending GOOD code:\n{good_code}")
        await websocket.send(json.dumps({"code": good_code, "threshold": 0.8}))
        
        response = await websocket.recv()
        data = json.loads(response)
        print("\nServer Response 2:")
        print(f"Score: {data['quality_score']}")
        print(f"Accepted: {data['accepted']}")
        print(f"Message: {data['message']}")

if __name__ == "__main__":
    asyncio.run(test_workflow())
