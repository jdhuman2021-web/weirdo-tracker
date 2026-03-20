# Batch add tokens to config/tokens.json
# This script adds 18 new tokens (LOBSTAR already exists)

$tokensFile = "$PSScriptRoot\..\config\tokens.json"

# Token data to add
$newTokens = @(
    @{ address = "EJzqpRPxgZZVoVVuCXuQBNXp7mQzeH6FENMfuLRbpump"; name = "Artemis Moon Mission"; symbol = "Artemis II" },
    @{ address = "AtdqW9HYpx6bzuXAyuVRz6a3UiTHLoNTRJDN8buXHem7"; name = "INU"; symbol = "INU" },
    @{ address = "CmgJ1PobhUqB7MEa8qDkiG2TUpMTskWj8d9JeZWSpump"; name = "rainbowfish"; symbol = "FISH" },
    @{ address = "AbeDBXvqGnmcvX8NtQg5qgREFTw7HynkCc4u97xcpump"; name = "Blindfold Finance"; symbol = "BLIND" },
    @{ address = "BANKJmvhT8tiJRsBSS1n2HryMBPvT5Ze4HU95DUAmeta"; name = "Avici"; symbol = "AVICI" },
    @{ address = "DP4omjjY94NRJrECHBZyUQSpGrjtukoDyUbqb9Zzpump"; name = "Regret"; symbol = "Regret" },
    @{ address = "Cm6fNnMk7NfzStP9CZpsQA2v3jjzbcYGAxdJySmHpump"; name = "Buttcoin"; symbol = "Buttcoin" },
    @{ address = "GB8KtQfMChhYrCYtd5PoAB42kAdkHnuyAincSSmFpump"; name = "Pigeon Doctor"; symbol = "PIGEON" },
    @{ address = "JB2wezZLdzWfnaCfHxLg193RS3Rh51ThiXxEDWQDpump"; name = "LABUBU"; symbol = "LABUBU" },
    @{ address = "2pjcq9k2X5oSArNKiVeQ2ENB63eJt8pwCabciGQGpump"; name = "Optimistic Minion"; symbol = "Optimistic" },
    @{ address = "J8PSdNP3QewKq2Z1JJJFDMaqF7KcaiJhR7gbr5KZpump"; name = "Tung Tung Tung Sahur"; symbol = "TripleT" },
    @{ address = "A8C3xuqscfmyLrte3VmTqrAq8kgMASius9AFNANwpump"; name = "FWOG"; symbol = "FWOG" },
    @{ address = "5z3EqYQo9HiCEs3R84RCDMu2n7anpDMxRhdK8PSWmrRC"; name = "PONKE"; symbol = "PONKE" },
    @{ address = "5UUH9RTDiSpq6HKS6bp4NdU9PNJpXRXuiw6ShBTBhgH2"; name = "TROLL"; symbol = "TROLL" },
    @{ address = "DQnkBM4eYYMnVE8Qy2K3BB7uts1fh2EwBVktEz6jpump"; name = "DOWGE"; symbol = "DJI6930" },
    @{ address = "9QSjVAg5rDfBZPhvKwZcB63St3r6bqohP3Adurkjpump"; name = "Rosie"; symbol = "Rosie" },
    @{ address = "AVF9F4C4j8b1Kh4BmNHqybDaHgnZpJ7W7yLvL7hUpump"; name = "Lobstar"; symbol = "Lobstar" },
    @{ address = "Gbu7JAKhTVtGyRryg8cYPiKNhonXpUqbrZuCDjfUpump"; name = "snowball"; symbol = "snowball" }
)

# Read existing tokens file
$jsonContent = Get-Content $tokensFile -Raw | ConvertFrom-Json

# Get existing addresses for duplicate checking
$existingAddresses = $jsonContent.tokens | ForEach-Object { $_.address }

$addedCount = 0
$skippedCount = 0

foreach ($token in $newTokens) {
    if ($existingAddresses -contains $token.address) {
        Write-Host "Skipping duplicate: $($token.symbol) ($($token.address))" -ForegroundColor Yellow
        $skippedCount++
        continue
    }
    
    $newToken = @{
        symbol = $token.symbol
        name = $token.name
        address = $token.address
        chain = "SOL"
        added_date = (Get-Date -Format "yyyy-MM-dd")
        source = "batch_added"
    }
    
    $jsonContent.tokens += $newToken
    Write-Host "Added: $($token.symbol) - $($token.name)" -ForegroundColor Green
    $addedCount++
}

# Update last_updated timestamp
$jsonContent.last_updated = (Get-Date -Format "yyyy-MM-ddTHH:mm:ss")

# Save back to file
$jsonContent | ConvertTo-Json -Depth 10 | Set-Content $tokensFile

Write-Host "`nBatch complete!" -ForegroundColor Cyan
Write-Host "Added: $addedCount tokens" -ForegroundColor Green
Write-Host "Skipped (duplicates): $skippedCount tokens" -ForegroundColor Yellow
Write-Host "Total tokens in database: $($jsonContent.tokens.Count)" -ForegroundColor Cyan
