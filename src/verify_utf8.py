from pathlib import Path

file_path = Path(r"c:\SP_lab_Projects\sp_lab_v9_1.1\data\taifex_extracted\1998_fut.csv")

try:
    print("Attempting to read with utf-8...")
    content = file_path.read_text(encoding='utf-8')
    print("Successfully read with utf-8. First 100 chars:")
    print(content[:100])
except Exception as e:
    print(f"Failed with utf-8: {e}")
