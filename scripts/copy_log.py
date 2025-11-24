import shutil
import os

try:
    src = "poc_debug.log"
    dst = "poc_debug_copy.txt"
    shutil.copy(src, dst)
    print(f"Copied {src} to {dst}")
    print(f"Source size: {os.path.getsize(src)}")
    print(f"Dest size: {os.path.getsize(dst)}")
    
    with open(dst, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
        print(f"Content length: {len(content)}")
        if len(content) > 0:
            print("First 100 chars:")
            print(content[:100])
except Exception as e:
    print(f"Error: {e}")
