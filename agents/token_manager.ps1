# Token Manager - PowerShell Version
# Add/Remove tokens from config/tokens.json

$ConfigFile = "..\config\tokens.json"

function Load-Config {
    if (Test-Path $ConfigFile) {
        return Get-Content $ConfigFile | ConvertFrom-Json
    } else {
        New-Item -ItemType Directory -Force -Path "..\config" | Out-Null
        return @{ tokens = @(); whales = @() }
    }
}

function Save-Config($config) {
    $config | ConvertTo-Json -Depth 10 | Out-File $ConfigFile -Encoding UTF8
    Write-Host "💾 Saved to $ConfigFile" -ForegroundColor Green
}

function Add-Token {
    Write-Host ""
    Write-Host "=" * 50 -ForegroundColor Cyan
    Write-Host "➕ Add New Token" -ForegroundColor Green
    Write-Host "=" * 50 -ForegroundColor Cyan
    
    $symbol = Read-Host "Symbol (e.g., PUNCH)"
    if ([string]::IsNullOrWhiteSpace($symbol)) {
        Write-Host "❌ Symbol required" -ForegroundColor Red
        return
    }
    
    $config = Load-Config
    
    # Check if exists
    if ($config.tokens | Where-Object { $_.symbol -eq $symbol.ToUpper() }) {
        Write-Host "⚠️  $symbol already exists" -ForegroundColor Yellow
        return
    }
    
    $name = Read-Host "Name (e.g., パンチ)"
    if ([string]::IsNullOrWhiteSpace($name)) { $name = $symbol }
    
    $address = Read-Host "Contract Address"
    if ([string]::IsNullOrWhiteSpace($address)) {
        Write-Host "❌ Address required" -ForegroundColor Red
        return
    }
    
    $chain = Read-Host "Chain (SOL/ETH/BASE) [SOL]"
    if ([string]::IsNullOrWhiteSpace($chain)) { $chain = "SOL" }
    
    $source = Read-Host "Source (e.g., Rick Telegram)"
    if ([string]::IsNullOrWhiteSpace($source)) { $source = "manual" }
    
    $notes = Read-Host "Notes (optional)"
    
    $newToken = @{
        symbol = $symbol.ToUpper()
        name = $name
        address = $address
        chain = $chain.ToUpper()
        added_date = (Get-Date -Format "yyyy-MM-dd")
        source = $source
        notes = $notes
    }
    
    $config.tokens += $newToken
    Save-Config $config
    
    Write-Host ""
    Write-Host "✅ Added $symbol to watchlist!" -ForegroundColor Green
    Write-Host "   Address: $($address.Substring(0,20))..."
    Write-Host "   Chain: $chain"
    Write-Host ""
    Write-Host "🔄 Run Research Agent to fetch data for this token" -ForegroundColor Cyan
}

function List-Tokens {
    $config = Load-Config
    $tokens = $config.tokens
    
    Write-Host ""
    Write-Host "=" * 50 -ForegroundColor Cyan
    Write-Host "📋 Configured Tokens ($($tokens.Count))" -ForegroundColor Yellow
    Write-Host "=" * 50 -ForegroundColor Cyan
    
    $i = 1
    foreach ($token in $tokens) {
        Write-Host ""
        Write-Host "$i. $($token.symbol) - $($token.name)" -ForegroundColor White
        Write-Host "   Address: $($token.address.Substring(0,30))..." -ForegroundColor Gray
        Write-Host "   Chain: $($token.chain) | Added: $($token.added_date)" -ForegroundColor Gray
        if ($token.notes) {
            Write-Host "   Notes: $($token.notes)" -ForegroundColor DarkGray
        }
        $i++
    }
}

function Remove-Token {
    $config = Load-Config
    
    if ($config.tokens.Count -eq 0) {
        Write-Host "⚠️  No tokens to remove" -ForegroundColor Yellow
        return
    }
    
    List-Tokens
    
    Write-Host ""
    $symbol = Read-Host "Enter symbol to remove"
    
    $originalCount = $config.tokens.Count
    $config.tokens = $config.tokens | Where-Object { $_.symbol -ne $symbol.ToUpper() }
    
    if ($config.tokens.Count -lt $originalCount) {
        Save-Config $config
        Write-Host "✅ Removed $symbol" -ForegroundColor Green
    } else {
        Write-Host "❌ $symbol not found" -ForegroundColor Red
    }
}

# Main Menu
Write-Host ""
Write-Host "=" * 50 -ForegroundColor Cyan
Write-Host "🧠 Weirdo Tracker - Token Manager" -ForegroundColor Green
Write-Host "=" * 50 -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Add new token"
Write-Host "2. List all tokens"
Write-Host "3. Remove token"
Write-Host "4. Exit"
Write-Host ""

$choice = Read-Host "Select"

switch ($choice) {
    "1" { Add-Token }
    "2" { List-Tokens }
    "3" { Remove-Token }
    default { Write-Host "Goodbye!" -ForegroundColor Gray }
}
