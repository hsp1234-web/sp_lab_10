import os

def print_file(path):
    print(f"--- Reading {path} ---")
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                print(f.read())
        except Exception as e:
            print(f"Error reading utf-8: {e}")
            try:
                with open(path, 'r', encoding='utf-16') as f:
                    print(f.read())
            except Exception as e2:
                print(f"Error reading utf-16: {e2}")
    else:
        print("File not found.")

print_file("debug_v27.log")
print_file("output_log.txt")
