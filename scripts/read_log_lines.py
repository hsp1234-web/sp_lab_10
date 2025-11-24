import sys
try:
    with open("poc_debug.log", "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
        print(f"File size: {len(content)} chars")
        print("-" * 20)
        print(content)
        print("-" * 20)
except Exception as e:
    print(f"Error: {e}")
