#!/usr/bin/env python3
"""
Extract contract data from Rick Burp Bot scan messages.
Supports text and forwarded message formats.
"""

import re
import json
import sys
from datetime import datetime

def extract_contract_data(text):
    """Extract all contract data from a scan message."""
    
    data = {
        "address": None,
        "symbol": None,
        "name": None,
        "price_usd": 0,
        "market_cap": 0,
        "fdv": 0,
        "liquidity": 0,
        "volume_24h": 0,
        "age_days": 0,
        "holders": 0,
        "fresh_wallets_1d": 0,
        "fresh_wallets_7d": 0,
        "price_change_1h": 0,
        "source": "Rick scan"
    }
    
    # Extract contract address (44-50 chars ending in 'pump')
    contract_match = re.search(r'([A-Za-z0-9]{40,50}pump)', text)
    if contract_match:
        data["address"] = contract_match.group(1)
    
    # Extract symbol ($SYMBOL)
    symbol_match = re.search(r'\$([A-Z]+)', text)
    if symbol_match:
        data["symbol"] = symbol_match.group(1)
    
    # Extract name from [💊] link
    name_match = re.search(r'\[💊\]\s*\[[^\]]+\]\s*\[([^\]]+)\]', text)
    if name_match:
        data["name"] = name_match.group(1)
    
    # Extract price
    price_match = re.search(r'USD:\s*([0-9.]+)', text)
    if price_match:
        data["price_usd"] = float(price_match.group(1))
    
    # Extract market cap from FDV line
    mcap_match = re.search(r'FDV:\s*([0-9.KM]+)', text)
    if mcap_match:
        data["market_cap"] = parse_number(mcap_match.group(1))
    
    # Extract FDV peak
    fdv_match = re.search(r'⇨\s*([0-9.KM]+)', text)
    if fdv_match:
        data["fdv"] = parse_number(fdv_match.group(1))
    
    # Extract liquidity
    liq_match = re.search(r'Liq:\s*([0-9.KM]+)', text)
    if liq_match:
        data["liquidity"] = parse_number(liq_match.group(1))
    
    # Extract volume
    vol_match = re.search(r'Vol:\s*([0-9.KM]+)', text)
    if vol_match:
        data["volume_24h"] = parse_number(vol_match.group(1))
    
    # Extract age
    age_match = re.search(r'Age:\s*(\d+)d', text)
    if age_match:
        data["age_days"] = int(age_match.group(1))
    
    # Extract holders
    holders_match = re.search(r'Total:\s*([0-9.KM]+)', text)
    if holders_match:
        data["holders"] = parse_number(holders_match.group(1))
    
    # Extract fresh wallets
    fresh_1d_match = re.search(r'Fresh 1D:\s*(\d+)%', text)
    if fresh_1d_match:
        data["fresh_wallets_1d"] = int(fresh_1d_match.group(1))
    
    fresh_7d_match = re.search(r'Fresh 7D:\s*(\d+)%', text)
    if fresh_7d_match:
        data["fresh_wallets_7d"] = int(fresh_7d_match.group(1))
    
    # Extract 1H price change
    change_match = re.search(r'1H:.*⋅\s*([+-]?[0-9.]+)%', text)
    if change_match:
        data["price_change_1h"] = float(change_match.group(1))
    
    return data

def parse_number(num_str):
    """Parse numbers with K/M suffixes."""
    num_str = num_str.upper().replace(',', '')
    if num_str.endswith('K'):
        return int(float(num_str[:-1]) * 1000)
    elif num_str.endswith('M'):
        return int(float(num_str[:-1]) * 1000000)
    else:
        return int(float(num_str))

def main():
    if len(sys.argv) < 2:
        print("Usage: extract_contract.py '<scan_message>'")
        sys.exit(1)
    
    text = sys.argv[1]
    data = extract_contract_data(text)
    
    if data["address"]:
        print(json.dumps(data, indent=2))
    else:
        print(json.dumps({"error": "No contract address found"}), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()