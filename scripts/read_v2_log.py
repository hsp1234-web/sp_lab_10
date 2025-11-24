import sys
try:
    with open("v2_debug.log", "r", encoding="utf-8", errors="replace") as f:
        print(f.read())
except Exception as e:
    print(f"Error: {e}")
