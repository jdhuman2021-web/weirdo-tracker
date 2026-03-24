import json
import time
import urllib.request
import urllib.error
from datetime import datetime

SOLANA_RPC = "https://api.mainnet-beta.solana.com"
TIMEOUT = 10
DELAY = 0.1

def make_rpc_call(method, params, max_retries=3):
    payload = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params
    }).encode("utf-8")
    
    headers = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
    
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(SOLANA_RPC, data=payload, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
                result = json.loads(response.read().decode("utf-8"))
                if "error" in result:
                    if "rate limit" in str(result["error"]).lower():
                        time.sleep(2)
                        continue
                    return None, result.get("error")
                return result.get("result"), None
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(5)
                continue
            return None, str(e)
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(1)
                continue
            return None, str(e)
    return None, "Max retries exceeded"

def check_wallet_tokens(wallet_address, token_addresses):
    result, error = make_rpc_call("getTokenAccountsByOwner", [
        wallet_address,
        {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"},
        {"encoding": "jsonParsed"}
    ])
    
    if error:
        return None, error
    
    if not result or not result.get("value"):
        return {}, None
    
    wallet_holdings = {}
    for account in result["value"]:
        try:
            mint = account["account"]["data"]["parsed"]["info"]["mint"]
            balance = account["account"]["data"]["parsed"]["info"]["tokenAmount"]["uiAmount"]
            if balance and balance > 0:
                wallet_holdings[mint] = balance
        except (KeyError, IndexError):
            continue
    
    holdings = []
    for token_addr in token_addresses:
        if token_addr in wallet_holdings:
            holdings.append({"token": token_addr, "balance": wallet_holdings[token_addr]})
    
    return holdings, None

# Load configs
with open("config/wallet_database.json", "r", encoding="utf-8") as f:
    wallet_db = json.load(f)

with open("config/tokens.json", "r", encoding="utf-8") as f:
    tokens_config = json.load(f)

wallets = wallet_db["wallets"]
tokens = tokens_config.get("tokens", [])

token_addresses = []
token_map = {}
for token in tokens:
    addr = token.get("address", "")
    if addr:
        token_addresses.append(addr)
        token_map[addr] = {"name": token.get("name", "Unknown"), "symbol": token.get("symbol", "???")}

print(f"Checking {len(wallets)} wallets against {len(token_addresses)} tokens...")

matches = []
errors = 0
checked = 0
start_time = time.time()

for i, wallet in enumerate(wallets):
    wallet_addr = wallet["address"]
    wallet_label = wallet.get("label", wallet_addr[:16] + "...")
    wallet_type = wallet.get("type", "unknown")
    wallet_tier = wallet.get("tier", "other")
    
    holdings, error = check_wallet_tokens(wallet_addr, token_addresses)
    
    if error:
        errors += 1
        if errors <= 3:
            print(f"  Error for {wallet_label}: {error}")
    elif holdings:
        for holding in holdings:
            token_info = token_map.get(holding["token"], {"name": "Unknown", "symbol": "??"})
            matches.append({
                "wallet_address": wallet_addr,
                "wallet_label": wallet_label,
                "wallet_type": wallet_type,
                "wallet_tier": wallet_tier,
                "token_address": holding["token"],
                "token_name": token_info["name"],
                "token_symbol": token_info["symbol"],
                "balance": holding["balance"]
            })
            balance_str = str(holding["balance"])
            print(f"  [MATCH] {wallet_label} holds {balance_str} {token_info['symbol']}")
    
    checked += 1
    if checked % 10 == 0:
        elapsed = time.time() - start_time
        print(f"  ... checked {checked}/{len(wallets)} ({elapsed:.1f}s)")
    
    time.sleep(DELAY)

print(f"Scan complete! Checked: {checked}, Errors: {errors}, Matches: {len(matches)}")

results = {"scan_time": datetime.now().isoformat(), "wallets_checked": checked, "tokens_checked": len(token_addresses), "errors": errors, "matches": matches}

with open("data/wallet_holdings_scan.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

print("Results saved to data/wallet_holdings_scan.json")

if matches:
    print("\nMatches found:")
    for m in matches:
        print(f"  {m['wallet_label']} ({m['wallet_type']}) -> {m['token_symbol']}: {m['balance']}")
else:
    print("\nNo matches - none of the smart money wallets hold your tracked tokens.")
