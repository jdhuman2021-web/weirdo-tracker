# Research Agent v1.0 - PowerShell Version
# Fetches market data from DexScreener API

$ErrorActionPreference = "Continue"

# Configuration
$Tokens = @(
    @{ Symbol = "PUNCH"; Name = "パンチ"; Address = "NV2RYH954cTJ3ckFUpvfqaQXU4ARqqDH3562nFSpump"; Chain = "SOL" },
    @{ Symbol = "Jellybean"; Name = "Jellybean"; Address = "412zDygnwP9DzitnQVgRKUFFTDmrYScFch6P2k39pump"; Chain = "SOL" },
    @{ Symbol = "Devious"; Name = "Devious MF"; Address = "CeoReCwAmt8iqjQoKQGEMqKERDWGxxDUED9zVYg3pump"; Chain = "SOL" },
    @{ Symbol = "HODL"; Name = "HODL"; Address = "Hh3oTaqDCKKfdBgsQEvxp9sUwyNf8x9qmKqE8x9pump"; Chain = "SOL" },
    @{ Symbol = "JUICE"; Name = "JUICE"; Address = "2LzLh5pHg3nDQz6goTLAvDXfDbSBgAR8qem3bdXdpump"; Chain = "SOL" },
    @{ Symbol = "PIZZA"; Name = "Bitcoin Pizza"; Address = "G9ivB7K41a4G8m1k4QdxxN4L5eGKL7Mr12S26B85pump"; Chain = "SOL" },
    @{ Symbol = "BULK"; Name = "bulk"; Address = "F4TJfiMVi7zFGRJj4FVC1Zuj7fdCo6skKa4SnAU4pump"; Chain = "SOL" },
    @{ Symbol = "Momo-chan"; Name = "モモちゃん"; Address = "3zomtMhRRsBpLZeJLS86fgueXE7xAhoN8dnymNh8pump"; Chain = "SOL" },
    @{ Symbol = "MAX"; Name = "maxxing"; Address = "32CdQdBUxbCsLy5AUHWmyidfwhgGUr9N573NBUrDpump"; Chain = "SOL" },
    @{ Symbol = "LOBSTAR"; Name = "Lobstar"; Address = "4TyZGqRLG3VcHTGMcLBoPUmqYitMVojXinAmkL8xpump"; Chain = "SOL" }
)

$DataDir = "..\data"
New-Item -ItemType Directory -Force -Path $DataDir | Out-Null

Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "🧠 Weirdo Tracker - Research Agent v1.0" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""

$Results = @()
$Index = 0

foreach ($Token in $Tokens) {
    $Index++
    Write-Host "[$Index/$($Tokens.Count)] $($Token.Symbol)... " -NoNewline
    
    try {
        $Url = "https://api.dexscreener.com/latest/dex/tokens/$($Token.Address)"
        $Response = Invoke-RestMethod -Uri $Url -TimeoutSec 10 -ErrorAction Stop
        
        if ($Response.pairs -and $Response.pairs.Count -gt 0) {
            # Get pair with highest liquidity
            $Pair = $Response.pairs | Sort-Object { $_.liquidity.usd } -Descending | Select-Object -First 1
            
            $Data = @{
                symbol = $Token.Symbol
                name = $Token.Name
                address = $Token.Address
                chain = $Token.Chain
                price_usd = [float]($Pair.priceUsd -as [decimal])
                price_change_1h = [float]($Pair.priceChange.h1 -as [decimal])
                price_change_24h = [float]($Pair.priceChange.h24 -as [decimal])
                volume_24h = [float]($Pair.volume.h24 -as [decimal])
                liquidity_usd = [float]($Pair.liquidity.usd -as [decimal])
                market_cap = [float](($Pair.fdv -as [decimal]) -or ($Pair.marketCap -as [decimal]))
                timestamp = (Get-Date -Format "o")
                source = "dexscreener"
            }
            
            $Results += $Data
            Write-Host "✓ `$($Data.price_usd.ToString("0.000000"))" -ForegroundColor Green
        } else {
            Write-Host "✗ No pairs" -ForegroundColor Red
        }
    }
    catch {
        Write-Host "✗ Error: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    # Rate limiting
    if ($Index -lt $Tokens.Count) {
        Start-Sleep -Seconds 6
    }
}

# Save results
if ($Results.Count -gt 0) {
    $Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $Filename = "research_$Timestamp.json"
    $Filepath = Join-Path $DataDir $Filename
    
    $Output = @{
        metadata = @{
            timestamp = (Get-Date -Format "o")
            tokens_count = $Results.Count
            source = "research_agent_v1.0"
        }
        data = $Results
    } | ConvertTo-Json -Depth 10
    
    $Output | Out-File -FilePath $Filepath -Encoding UTF8
    
    Write-Host ""
    Write-Host "=" * 60 -ForegroundColor Cyan
    Write-Host "📊 SUMMARY" -ForegroundColor Yellow
    Write-Host "=" * 60 -ForegroundColor Cyan
    Write-Host "Tokens fetched: $($Results.Count)/$($Tokens.Count)"
    Write-Host "Saved to: $Filepath"
    
    # Top gainer/loser
    $Sorted = $Results | Sort-Object price_change_24h -Descending
    Write-Host ""
    Write-Host "🔥 Top Gainer: $($Sorted[0].symbol) (+$($Sorted[0].price_change_24h)%)" -ForegroundColor Green
    Write-Host "❄️ Top Loser: $($Sorted[-1].symbol) ($($Sorted[-1].price_change_24h)%)" -ForegroundColor Red
    
    # High volume
    $HighVol = $Results | Where-Object { $_.volume_24h -gt 100000 }
    Write-Host "💧 High Volume: $($HighVol.Count) tokens" -ForegroundColor Cyan
}
else {
    Write-Host "❌ No data fetched" -ForegroundColor Red
}

Write-Host ""
Write-Host "Done!" -ForegroundColor Green
