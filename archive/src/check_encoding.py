from pathlib import Path

file_path = Path(r"c:\SP_lab_Projects\sp_lab_v9_1.1\data\taifex_extracted\1998_fut.csv")

try:
    # Try reading with cp950
    print("Attempting to read with cp950...")
    content = file_path.read_text(encoding='cp950')
    print("Successfully read with cp950. First 200 chars:")
    print(content[:200])
except Exception as e:
    print(f"Failed with cp950: {e}")

try:
    # Try reading with utf-8 to see if it fails as expected
    print("\nAttempting to read with utf-8...")
    content = file_path.read_text(encoding='utf-8')
    print("Successfully read with utf-8. First 200 chars:")
    print(content[:200])
except Exception as e:
    print(f"Failed with utf-8: {e}")
