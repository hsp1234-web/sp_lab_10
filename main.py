import sys
import os

# Add the project root to the python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.main import main

if __name__ == "__main__":
    # Ensure output directories exist
    output_dir = os.path.join(os.path.dirname(__file__), 'output')
    for subdir in ['results', 'logs', 'archive']:
        os.makedirs(os.path.join(output_dir, subdir), exist_ok=True)
    
    main()
