"""
Config Migration Script
Adds 'status': 'active' to all tokens missing it

Usage: python migrate_config_status.py
"""

import json
from pathlib import Path
import sys

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

CONFIG_FILE = Path(__file__).parent / "config" / "tokens.json"

def migrate_config():
    """Add status field to all tokens"""
    
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    tokens = data.get('tokens', [])
    updated = 0
    
    for token in tokens:
        if 'status' not in token:
            token['status'] = 'active'
            updated += 1
    
    # Update version
    data['version'] = '1.3'
    
    # Save back
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"Config Migration Complete")
    print(f"  Updated {updated} tokens with status='active'")
    print(f"  Version: 1.3")

if __name__ == "__main__":
    migrate_config()
