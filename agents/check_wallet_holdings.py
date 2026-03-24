#!/usr/bin/env python3
"""
Check wallet_database against tracked tokens using public Solana RPC.
One-time scan to find which smart money wallets hold our tokens.
"""

import json
import time
import urllib.request
import urllib.error
from datetime import datetime

# Config
SOLANA_RPC = "https://api.mainnet-beta.solana.com"
TIMEOUT = 10  # seconds per request
DELAY = 0.1   # delay between requests to avoid rate limits

def make_rpc_call(method, params, max_retries=3):
    """Make a JSON-RPC call to Solana RPC"""
    payload = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params
    }).encode('utf-8')
    
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0'
    }
    
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(
                SOLANA_RPC, 
                data=payload, 
                headers=headers,
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
                result = json.loads(response.read().decode('utf-8'))
                if 'error' in result:
                    if 'rate limit' in str(result['error']).lower():
                        time.sleep(2)
                        continue
                    return None, result.get('error')
                return result.get('result'), None
        except urllib.error.HTTPError as e:
            if e.code == 429:  # Rate limited
                time.sleep(5)
                continue
            return None, str(e)
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(1)
                continue
            return None, str(e)
    
    return None, "Max retries exceeded"

def get_token_balance(wallet_address, token_address):
    """Get token balance for a specific wallet and token"""
    # Using getTokenAccountsByOwner with mint filter
    result, error = make_rpc_call("getTokenAccountsByOwner", [
        wallet_address,
        {"mint": token_address},
        {"encoding": "jsonParsed"}
    ])
    
    if error:
        return None, error
    
    if not result or not result.get('value'):
        return 0, None
    
    # Parse the balance
    try:
        account = result['value'][0]
        balance = account['account']['data']['parsed']['info']['tokenAmount']['uiAmount']
        return balance, None
    except (KeyError, IndexError):
        return None, "Failed to parse balance"

def check_wallet_tokens(wallet_address, token_addresses):
    """Check a wallet's holdings across all our tokens"""
    holdings = []
    
    # Get all token accounts for this wallet
    result, error = make_rpc_call("getTokenAccountsByOwner", [
        wallet_address,
        {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"},
        {"encoding": "jsonParsed"}
    ])
    
    if error:
        return None, error
    
    if not result or not result.get('value'):
        return {}, None
    
    # Build a lookup of token -> balance
    wallet_holdings = {}
    for account in result['value']:
        try:
            mint = account['account']['data']['parsed']['info']['mint']
            balance = account['account']['data']['parsed']['info']['tokenAmount']['uiAmount']
            if balance and balance > 0:
                wallet_holdings[mint] = balance
        except (KeyError, IndexError):
            continue
    
    # Check against our tokens
    for token_addr in token_addresses:
        if token_addr in wallet_holdings:
            holdings.append({
                "token": token_addr,
                "balance": wallet_holdings[token_addr]
            })
    
    return holdings, None

def main():
    print("[START] Wallet Holdings Check")
    print(f"   Time: {datetime.now().isoformat()}")
    print("=" * 60)
    
    # Load wallet database
    with open('config/wallet_database.json', 'r') as f:
        wallet_db = json.load(f)
    
    # Load tokens
    with open('config/tokens.json', 'r') as f:
        tokens_config = json.load(f)
    
    wallets = wallet_db['wallets']
    tokens = tokens_config.get('tokens', [])
    
    # Build token address lookup
    token_addresses = []
    token_map = {}  # address -> {name, symbol}
    for token in tokens:
        addr = token.get('address', '')
        if addr:
            token_addresses.append(addr)
            token_map[addr] = {
                'name': token.get('name', 'Unknown'),
                'symbol': token.get('symbol', '???')
            }
    
    print(f"📊 Checking {len(wallets)} wallets against {len(token_addresses)} tokens")
    print("=" * 60)
    
    # Track results
    matches = []
    errors = 0
    checked = 0
    
    start_time = time.time()
    
    for i, wallet in enumerate(wallets):
        wallet_addr = wallet['address']
        wallet_label = wallet.get('label', wallet_addr[:16] + '...')
        wallet_type = wallet.get('type', 'unknown')
        wallet_tier = wallet.get('tier', 'other')
        
        # Check all tokens for this wallet
        holdings, error = check_wallet_tokens(wallet_addr, token_addresses)
        
        if error:
            errors += 1
            if errors <= 5:  # Print first few errors
                print(f"  ⚠️  {wallet_label}: {error}")
        elif holdings:
            # Found matches!
            for holding in holdings:
                token_info = token_map.get(holding['token'], {'name': 'Unknown', 'symbol': '???'})
                match = {
                    'wallet_address': wallet_addr,
                    'wallet_label': wallet_label,
                    'wallet_type': wallet_type,
                    'wallet_tier': wallet_tier,
                    'token_address': holding['token'],
                    'token_name': token_info['name'],
                    'token_symbol': token_info['symbol'],
                    'balance': holding['balance']
                }
                matches.append(match)
                print(f"  [MATCH] {wallet_label} ({wallet_type}) holds {holding['balance']:,.2f} {token_info['symbol']}")
        
        checked += 1
        if checked % 20 == 0:
            elapsed = time.time() - start_time
            print(f"  ... checked {checked}/{len(wallets)} wallets ({elapsed:.1f}s elapsed)")
        
        time.sleep(DELAY)  # Be nice to the RPC
    
    # Summary
    print("=" * 60)
    print(f"✅ Scan complete!")
    print(f"   Wallets checked: {checked}")
    print(f"   Errors: {errors}")
    print(f"   Matches found: {len(matches)}")
    print(f"   Time elapsed: {time.time() - start_time:.1f}s")
    
    # Save results
    results = {
        'scan_time': datetime.now().isoformat(),
        'wallets_checked': checked,
        'tokens_checked': len(token_addresses),
        'errors': errors,
        'matches': matches
    }
    
    with open('data/wallet_holdings_scan.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"   Results saved to: data/wallet_holdings_scan.json")
    
    if matches:
        print("\n📋 SUMMARY - Smart Money in Your Tokens:")
        print("-" * 60)
        
        # Group by token
        by_token = {}
        for m in matches:
            sym = m['token_symbol']
            if sym not in by_token:
                by_token[sym] = []
            by_token[sym].append(m)
        
        for sym, holdings in sorted(by_token.items(), key=lambda x: -len(x[1])):
            print(f"\n  {sym}:")
            for h in holdings:
                print(f"    - {h['wallet_label']} ({h['wallet_type']}, {h['wallet_tier']}): {h['balance']:,.2f}")
    else:
        print("\n❌ No matches found - none of the smart money wallets hold your tracked tokens.")

if __name__ == "__main__":
    main()
