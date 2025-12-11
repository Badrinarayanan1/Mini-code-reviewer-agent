import asyncio
import websockets
import json
import os
import sys

# Use utf-8 for stdin/stdout to handle emojis on Windows
sys.stdin.reconfigure(encoding='utf-8')
sys.stdout.reconfigure(encoding='utf-8')

INPUT_FILE = "input_code.py"

async def manual_check():
    uri = "ws://127.0.0.1:8000/ws/code-review"
    
    # Ask for threshold once
    try:
        threshold_str = input("Enter quality threshold (default 0.8): ").strip()
        threshold = float(threshold_str) if threshold_str else 0.8
    except ValueError:
        print("Invalid input, defaulting to 0.8")
        threshold = 0.8
    print(f"Using threshold: {threshold}")

    print(f"Connecting to {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print(f"\nConnected! \nModify '{INPUT_FILE}' and press Enter here to check it.\n(Type 'exit' to quit)")
            
            # Ensure input file exists
            if not os.path.exists(INPUT_FILE):
                with open(INPUT_FILE, "w", encoding="utf-8") as f:
                    f.write("def my_function(x):\n    print('Hello')\n    return x\n")
                print(f"Created '{INPUT_FILE}' with sample code.")

            while True:
                user_input = await asyncio.get_event_loop().run_in_executor(None, input, "\nPress Enter to check 'input_code.py' > ")
                
                if user_input.lower() in ('exit', 'quit'):
                    break
                
                # Read the code from the file
                try:
                    with open(INPUT_FILE, "r", encoding="utf-8") as f:
                        code_content = f.read()
                except Exception as e:
                    print(f"Error reading file: {e}")
                    continue

                if not code_content.strip():
                    print("File is empty!")
                    continue

                print("Sending code for review...")
                await websocket.send(json.dumps({"code": code_content, "threshold": threshold}))
                
                response_json = await websocket.recv()
                data = json.loads(response_json)
                
                print("-" * 40)
                print(f"Quality Score: {data.get('quality_score', 0)}")
                print(f"Accepted: {data.get('accepted', False)}")
                print(f"Execution Status (Node): {data.get('node', 'N/A')}")

                functions = data.get("functions", [])
                if functions:
                    print(f"\nExtracted Functions: {', '.join(functions)}")
                
                complexity = data.get("complexity", {})
                if complexity:
                    print(f"\nComplexity Data:")
                    for fn, score in complexity.items():
                        print(f" - {fn}: {score} statements")

                issues = data.get("issues", [])
                if issues:
                    print(f"\nIssues Found ({len(issues)}):")
                    for issue in issues:
                        print(f" - Line {issue.get('line')}: {issue.get('message')}")
                else:
                    print("\nNo issues found.")
                    
                suggestions = data.get("suggestions", [])
                if suggestions:
                    print(f"\nSuggestions:")
                    for sugg in suggestions:
                        print(f" - {sugg}")
                
                print("-" * 40)

                if data.get("accepted"):
                    print("\n" + "="*40)
                    print("Code ACCEPTED! Workflow complete.")
                    print("="*40 + "\n")
                    break

    except ConnectionRefusedError:
        print("Could not connect. Is the server running? (started with uvicorn app.main:app --reload)")
    except websockets.exceptions.ConnectionClosedError:
        print("Connection closed by server.")

if __name__ == "__main__":
    try:
        asyncio.run(manual_check())
    except KeyboardInterrupt:
        print("\nExiting...")
