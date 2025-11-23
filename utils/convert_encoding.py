import sys
import os

def convert_to_utf8(filename):
    try:
        # Try reading as UTF-16 (common for PowerShell output)
        with open(filename, 'r', encoding='utf-16') as f:
            content = f.read()
    except UnicodeError:
        try:
            # Fallback to default encoding (likely CP950 or CP1252 on TW Windows)
            with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading {filename}: {e}")
            return

    # Write back as standard UTF-8
    new_filename = filename.replace('.txt', '_utf8.txt')
    with open(new_filename, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Successfully converted {filename} to {new_filename}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        convert_to_utf8(sys.argv[1])
    else:
        print("Usage: python convert_encoding.py <filename>")
