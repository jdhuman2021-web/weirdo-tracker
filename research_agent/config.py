# Research Agent Configuration
# Token list and whale wallets for Weirdo Tracker

TOKENS = [
    {"symbol": "PUNCH", "name": "パンチ", "address": "NV2RYH954cTJ3ckFUpvfqaQXU4ARqqDH3562nFSpump", "chain": "SOL"},
    {"symbol": "Jellybean", "name": "Jellybean", "address": "412zDygnwP9DzitnQVgRKUFFTDmrYScFch6P2k39pump", "chain": "SOL"},
    {"symbol": "Devious", "name": "Devious MF", "address": "CeoReCwAmt8iqjQoKQGEMqKERDWGxxDUED9zVYg3pump", "chain": "SOL"},
    {"symbol": "HODL", "name": "HODL", "address": "Hh3oTaqDCKKfdBgsQEvxp9sUwyNf8x9qmKqE8x9pump", "chain": "SOL"},
    {"symbol": "JUICE", "name": "JUICE", "address": "2LzLh5pHg3nDQz6goTLAvDXfDbSBgAR8qem3bdXdpump", "chain": "SOL"},
    {"symbol": "PIZZA", "name": "Bitcoin Pizza", "address": "G9ivB7K41a4G8m1k4QdxxN4L5eGKL7Mr12S26B85pump", "chain": "SOL"},
    {"symbol": "BULK", "name": "bulk", "address": "F4TJfiMVi7zFGRJj4FVC1Zuj7fdCo6skKa4SnAU4pump", "chain": "SOL"},
    {"symbol": "Momo-chan", "name": "モモちゃん", "address": "3zomtMhRRsBpLZeJLS86fgueXE7xAhoN8dnymNh8pump", "chain": "SOL"},
    {"symbol": "MAX", "name": "maxxing", "address": "32CdQdBUxbCsLy5AUHWmyidfwhgGUr9N573NBUrDpump", "chain": "SOL"},
    {"symbol": "GOYIM", "name": "Goyim", "address": "EJzqpRPxgZZVoVVuCXuQBNXp7mQzeH6FENMfuLRbpump", "chain": "SOL"},
    {"symbol": "INU", "name": "INU", "address": "CmgJ1PobhUqB7MEa8qDkiG2TUpMTskWj8d9JeZWSpump", "chain": "SOL"},
    {"symbol": "FISH", "name": "rainbowfish", "address": "AbeDBXvqGnmcvX8NtQg5qgREFTw7HynkCc4u97xcpump", "chain": "SOL"},
    {"symbol": "AVICI", "name": "Avici", "address": "DP4omjjY94NRJrECHBZyUQSpGrjtukoDyUbqb9Zzpump", "chain": "SOL"},
    {"symbol": "BUTT", "name": "Buttcoin", "address": "GB8KtQfMChhYrCYtd5PoAB42kAdkHnuyAincSSmFpump", "chain": "SOL"},
    {"symbol": "PIGEON", "name": "Pigeon Doctor", "address": "JB2wezZLdzWfnaCfHxLg193RS3Rh51ThiXxEDWQDpump", "chain": "SOL"},
    {"symbol": "LABUBU", "name": "LABUBU", "address": "2pjcq9k2X5oSArNKiVeQ2ENB63eJt8pwCabciGQGpump", "chain": "SOL"},
    {"symbol": "OPTIMISTIC", "name": "Optimistic Minion", "address": "J8PSdNP3QewKq2Z1JJJFDMaqF7KcaiJhR7gbr5KZpump", "chain": "SOL"},
    {"symbol": "LOBSTAR", "name": "Lobstar", "address": "4TyZGqRLG3VcHTGMcLBoPUmqYitMVojXinAmkL8xpump", "chain": "SOL"},
    {"symbol": "TESTICLE", "name": "testicle", "address": "Gbu7JAKhTVtGyRryg8cYPiKNhonXpUqbrZuCDjfUpump", "chain": "SOL"},
    {"symbol": "SNOWBALL", "name": "snowball", "address": "AbeDBXvqGnmcvX8NtQg5qgREFTw7HynkCc4u97xcpump", "chain": "SOL"},
]

WHALE_WALLETS = [
    {"address": "BtDaZUqHr2mKH5EYQCztuerHBuBEfQNYdquTDtEZp2Ym", "name": "SPECIAL1", "priority": "high"},
    {"address": "AfwNi3FBb1zFpBxMerawpq5fTf7vdGfSRQnfmkU8YT8h", "name": "Fish insider", "priority": "high"},
    {"address": "ApRnQN2HkbCn7W2WWiT2FEKvuKJp9LugRyAE1a9Hdz1", "name": "Winrate", "priority": "high"},
    {"address": "Be24Gbf5KisDk1LcWWZsBn8dvB816By7YzYF5zWZnRR6", "name": "Chairman", "priority": "high"},
    {"address": "ALY8eYje7CnGGBEcgQ8AWR5SctCoL867RznVh2zgKUto", "name": "Fish Decent", "priority": "medium"},
    {"address": "BBp4M7AQXDsPwKbNMrd8eXvBSDVGT8sdNhoP6kd8PWBo", "name": "Gold guy", "priority": "medium"},
    {"address": "GM7Hrz2bDq33ezMtL6KGidSWZXMWgZ6qBuugkb5H8NvN", "name": "beaver", "priority": "medium"},
    {"address": "89HbgWduLwoxcofWpmn1EiF9wEdpgkNDEyPjzZ72mkDi", "name": "AI cook", "priority": "medium"},
    {"address": "FEGu1issUaiWS7NhSNLwDYRudBSSUHaBenHF14qStv4W", "name": "Crypto Stacks", "priority": "medium"},
    {"address": "7JAi6spGX1FFnUNAhkAjJEPWb4iS6BYHVK16RP9fKBZF", "name": "Retrace Ape", "priority": "medium"},
]

# API Endpoints
DEXSCREENER_API = "https://api.dexscreener.com/latest/dex"
BIRDEYE_API = "https://public-api.birdeye.so"

# Rate limiting (requests per minute)
RATE_LIMIT = 10

# Output directory
DATA_DIR = "data"
