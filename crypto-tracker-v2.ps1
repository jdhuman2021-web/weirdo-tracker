#!/usr/bin/env pwsh
# Enhanced Crypto Portfolio Tracker v2
# Features: Price charts, PnL tracking, Volume spikes, Opportunity scanner, CSV export
# Requires: jq, bat, fzf, ripgrep, PowerShell 7

# Portfolio Configuration
$script:PortfolioFile = "C:\Users\HP\.openclaw\workspace\solana_tracker.json"
$script:HistoryFile = "C:\Users\HP\.openclaw\workspace\portfolio_history.json"
$script:Threshold24h = 50
$script:Threshold1h = 20
$script:NotificationEnabled = $true
$script:SparkChars = '▁▂▃▄▅▆▇█'

# Color definitions
$Colors = @{
    Green = "`e[32m"
    Red = "`e[31m"
    Yellow = "`e[33m"
    Blue = "`e[34m"
    Cyan = "`e[36m"
    Magenta = "`e[35m"
    Reset = "`e[0m"
    Bold = "`e[1m"
}

function Show-PortfolioHeader {
    Clear-Host
    Write-Host "$($Colors.Bold)$($Colors.Cyan)╔══════════════════════════════════════════════════════════════════╗$($Colors.Reset)"
    Write-Host "$($Colors.Bold)$($Colors.Cyan)║     🪙  WEIRDO PORTFOLIO TRACKER v2.0  -  $(Get-Date -Format 'yyyy-MM-dd HH:mm') UTC   ║$($Colors.Reset)"
    Write-Host "$($Colors.Bold)$($Colors.Cyan)╚══════════════════════════════════════════════════════════════════╝$($Colors.Reset)"
    Write-Host ""
}

function Get-TokenData {
    param([string]$Contract)
    
    try {
        $response = curl -s "https://api.dexscreener.com/latest/dex/tokens/$Contract" | jq -r '.pairs[0]'
        return $response | ConvertFrom-Json
    }
    catch {
        Write-Host "$($Colors.Red)Error fetching data for $Contract$($Colors.Reset)"
        return $null
    }
}

function Format-PriceChange {
    param([decimal]$Change)
    
    if ($Change -gt 0) {
        return "$($Colors.Green)+$($Change.ToString('F2'))%$($Colors.Reset)"
    }
    elseif ($Change -lt 0) {
        return "$($Colors.Red)$($Change.ToString('F2'))%$($Colors.Reset)"
    }
    else {
        return "$($Colors.Yellow)0.00%$($Colors.Reset)"
    }
}

# Sparkline generator for price charts
function Get-Sparkline {
    param([array]$Values, [int]$Width = 20)
    
    if ($Values.Count -lt 2) { return "Insufficient data" }
    
    $min = ($Values | Measure-Object -Minimum).Minimum
    $max = ($Values | Measure-Object -Maximum).Maximum
    $range = $max - $min
    
    if ($range -eq 0) { return $script:SparkChars[0] * [math]::Min($Width, $Values.Count) }
    
    $result = ""
    $step = [math]::Max(1, [math]::Floor($Values.Count / $Width))
    
    for ($i = 0; $i -lt $Values.Count; $i += $step) {
        $val = $Values[$i]
        $index = [math]::Floor((($val - $min) / $range) * ($script:SparkChars.Length - 1))
        $result += $script:SparkChars[[math]::Min($index, $script:SparkChars.Length - 1)]
        if ($result.Length -ge $Width) { break }
    }
    
    return $result
}

# Save price history
function Save-PriceHistory {
    param([string]$Symbol, [decimal]$Price)
    
    $history = @{}
    if (Test-Path $script:HistoryFile) {
        $history = Get-Content $script:HistoryFile -Raw | ConvertFrom-Json -AsHashtable
        if (-not $history) { $history = @{} }
    }
    
    if (-not $history[$Symbol]) {
        $history[$Symbol] = @()
    }
    
    $history[$Symbol] += @{
        timestamp = (Get-Date -Format "o")
        price = [double]$Price
    }
    
    # Keep last 100 data points
    if ($history[$Symbol].Count -gt 100) {
        $history[$Symbol] = $history[$Symbol][-100..-1]
    }
    
    $history | ConvertTo-Json -Depth 5 | Out-File $script:HistoryFile
}

# Get price chart
function Get-PriceChart {
    param([string]$Symbol, [int]$Width = 20)
    
    if (-not (Test-Path $script:HistoryFile)) { return "No history" }
    
    try {
        $history = Get-Content $script:HistoryFile -Raw | ConvertFrom-Json -AsHashtable
        if (-not $history -or -not $history[$Symbol] -or $history[$Symbol].Count -lt 2) {
            return "Building history..."
        }
        
        $prices = $history[$Symbol] | Select-Object -Last $Width | ForEach-Object { $_.price }
        $sparkline = Get-Sparkline -Values $prices -Width ($Width - 10)
        
        $firstPrice = $prices[0]
        $lastPrice = $prices[-1]
        $change = (($lastPrice - $firstPrice) / $firstPrice) * 100
        
        $changeStr = if ($change -gt 0) { "+$($change.ToString('F1'))%" } else { "$($change.ToString('F1'))%" }
        $changeColor = if ($change -gt 0) { $Colors.Green } else { $Colors.Red }
        
        return "$sparkline $changeColor$changeStr$($Colors.Reset)"
    }
    catch {
        return "Chart error"
    }
}

function Get-PortfolioTokens {
    if (Test-Path $script:PortfolioFile) {
        $json = Get-Content $script:PortfolioFile -Raw | ConvertFrom-Json
        return $json.tracked_contracts | Where-Object { $_.status -eq "active" }
    }
    return @()
}

# Portfolio Summary with PnL
function Get-PortfolioSummary {
    Show-PortfolioHeader
    
    $tokens = Get-PortfolioTokens
    if ($tokens.Count -eq 0) {
        Write-Host "$($Colors.Yellow)No active tokens found in portfolio$($Colors.Reset)"
        Read-Host "Press Enter"
        return
    }
    
    $totalValue = 0
    $totalInvested = 0
    $tokenData = @()
    
    Write-Host "$($Colors.Yellow)Fetching data for $($tokens.Count) tokens...$($Colors.Reset)"
    
    foreach ($token in $tokens) {
        $data = Get-TokenData -Contract $token.address
        if ($data) {
            Save-PriceHistory -Symbol $data.baseToken.symbol -Price $data.priceUsd
            
            # Simulated holdings (set avgBuyPrice in solana_tracker.json for real data)
            $holding = if ($token.holding) { $token.holding } else { 1000 }
            $avgBuyPrice = if ($token.avgBuyPrice) { $token.avgBuyPrice } else { $data.priceUsd * 0.8 }
            
            $currentValue = $holding * $data.priceUsd
            $investedValue = $holding * $avgBuyPrice
            $pnl = $currentValue - $investedValue
            $pnlPercent = if ($investedValue -gt 0) { ($pnl / $investedValue) * 100 } else { 0 }
            
            $totalValue += $currentValue
            $totalInvested += $investedValue
            
            $tokenData += [PSCustomObject]@{
                Symbol = $data.baseToken.symbol
                Holdings = $holding
                CurrentPrice = [decimal]$data.priceUsd
                CurrentValue = $currentValue
                PnL = $pnl
                PnLPercent = $pnlPercent
                Chart = Get-PriceChart -Symbol $data.baseToken.symbol -Width 15
                Change24h = $data.priceChange.h24
            }
        }
        Start-Sleep -Milliseconds 100
    }
    
    $totalPnL = $totalValue - $totalInvested
    $totalPnLPercent = if ($totalInvested -gt 0) { ($totalPnL / $totalInvested) * 100 } else { 0 }
    
    # Summary Header
    Show-PortfolioHeader
    Write-Host "$($Colors.Bold)$($Colors.Cyan)══════════════════ PORTFOLIO PERFORMANCE ══════════════════$($Colors.Reset)"
    Write-Host ""
    
    # Overall stats box
    $pnlColor = if ($totalPnL -ge 0) { $Colors.Green } else { $Colors.Red }
    $pnlEmoji = if ($totalPnL -ge 0) { "📈" } else { "📉" }
    
    Write-Host "  Invested:     $($Colors.Yellow)`$$($totalInvested.ToString('N2'))$($Colors.Reset)"
    Write-Host "  Value:        $($Colors.Cyan)`$$($totalValue.ToString('N2'))$($Colors.Reset)"
    Write-Host "  PnL:          $pnlColor$pnlEmoji `$$($totalPnL.ToString('N2')) ($($totalPnLPercent.ToString('F2'))%)$($Colors.Reset)"
    Write-Host "  Tokens:       $($Colors.Cyan)$($tokenData.Count) active$($Colors.Reset)"
    Write-Host ""
    Write-Host "$($Colors.Bold)  Token Breakdown:$($Colors.Reset)"
    Write-Host "  ───────────────────────────────────────────────────────────────"
    
    # Sort by PnL
    $sortedTokens = $tokenData | Sort-Object PnL -Descending
    
    foreach ($t in $sortedTokens) {
        $symColor = if ($t.PnL -ge 0) { $Colors.Green } else { $Colors.Red }
        $pnlStr = if ($t.PnL -ge 0) { "+$($t.PnL.ToString('N2'))" } else { "$($t.PnL.ToString('N2'))" }
        
        Write-Host "  $($t.Symbol.PadRight(8)) Value: `$($t.CurrentValue.ToString('N2').PadRight(12)) PnL: $symColor`$$pnlStr$($Colors.Reset) $($t.Chart)"
    }
    
    Write-Host ""
}

# Top Movers
function Show-TopMovers {
    param([int]$Count = 5)
    
    Show-PortfolioHeader
    Write-Host "$($Colors.Bold)Analyzing market movers...$($Colors.Reset)"
    
    $tokens = Get-PortfolioTokens
    $allTokens = @()
    
    foreach ($token in $tokens) {
        $data = Get-TokenData -Contract $token.address
        if ($data) {
            Save-PriceHistory -Symbol $data.baseToken.symbol -Price $data.priceUsd
            $allTokens += [PSCustomObject]@{
                Symbol = $data.baseToken.symbol
                Price = $data.priceUsd
                Change24h = $data.priceChange.h24
                Change1h = $data.priceChange.h1
                Liquidity = $data.liquidity.usd
                Chart = Get-PriceChart -Symbol $data.baseToken.symbol -Width 15
            }
        }
    }
    
    Show-PortfolioHeader
    
    # Gainers
    Write-Host "$($Colors.Bold)$($Colors.Green)╔════════════════════════════════════════════════════════════════╗$($Colors.Reset)"
    Write-Host "$($Colors.Bold)$($Colors.Green)║                    🚀 TOP GAINERS (24h)                        ║$($Colors.Reset)"
    Write-Host "$($Colors.Bold)$($Colors.Green)╚════════════════════════════════════════════════════════════════╝$($Colors.Reset)"
    Write-Host ""
    
    $gainers = $allTokens | Where-Object { $_.Change24h -gt 0 } | Sort-Object Change24h -Descending | Select-Object -First $Count
    if ($gainers) {
        foreach ($t in $gainers) {
            Write-Host "  $($Colors.Green)▲$($Colors.Reset) $($t.Symbol.PadRight(8)) +$($t.Change24h.ToString('F2'))%  Price: `$$($t.Price)  $($t.Chart)"
        }
    } else {
        Write-Host "  $($Colors.Yellow)No gainers in portfolio$($Colors.Reset)"
    }
    
    Write-Host ""
    
    # Losers
    Write-Host "$($Colors.Bold)$($Colors.Red)╔════════════════════════════════════════════════════════════════╗$($Colors.Reset)"
    Write-Host "$($Colors.Bold)$($Colors.Red)║                    📉 TOP LOSERS (24h)                         ║$($Colors.Reset)"
    Write-Host "$($Colors.Bold)$($Colors.Red)╚════════════════════════════════════════════════════════════════╝$($Colors.Reset)"
    Write-Host ""
    
    $losers = $allTokens | Where-Object { $_.Change24h -lt 0 } | Sort-Object Change24h | Select-Object -First $Count
    if ($losers) {
        foreach ($t in $losers) {
            Write-Host "  $($Colors.Red)▼$($Colors.Reset) $($t.Symbol.PadRight(8)) $($t.Change24h.ToString('F2'))%  Price: `$$($t.Price)  $($t.Chart)"
        }
    } else {
        Write-Host "  $($Colors.Green)No losers in portfolio!$($Colors.Reset)"
    }
    
    Write-Host ""
}

# Volume spike detector
function Find-VolumeSpikes {
    param([decimal]$Multiplier = 2.0)
    
    Show-PortfolioHeader
    Write-Host "$($Colors.Bold)Scanning for volume spikes (${Multiplier}x normal)...$($Colors.Reset)"
    Write-Host ""
    
    $tokens = Get-PortfolioTokens
    $spikes = @()
    
    foreach ($token in $tokens) {
        $data = Get-TokenData -Contract $token.address
        if ($data -and $data.volume -and $data.volume.h6 -and $data.volume.h6 -gt 0) {
            $avg6h = $data.volume.h6 / 6
            $currentRate = $data.volume.h24 / 24
            
            if ($avg6h -gt 0 -and $currentRate -gt ($avg6h * $Multiplier)) {
                $spikeMultiplier = $currentRate / $avg6h
                $spikes += [PSCustomObject]@{
                    Symbol = $data.baseToken.symbol
                    Volume24h = $data.volume.h24
                    Spike = $spikeMultiplier
                    Change = $data.priceChange.h24
                }
            }
        }
    }
    
    if ($spikes.Count -eq 0) {
        Write-Host "$($Colors.Yellow)No volume spikes detected above ${Multiplier}x$($Colors.Reset)"
    } else {
        Write-Host "$($Colors.Bold)🚨 VOLUME SPIKES DETECTED:$($Colors.Reset)"
        Write-Host ""
        Write-Host "  Symbol    24h Volume        Spike     Price Change"
        Write-Host "  ────────  ────────────────  ────────  ─────────────"
        
        foreach ($s in $spikes | Sort-Object Spike -Descending) {
            $color = if ($s.Spike -gt 5) { $Colors.Red } elseif ($s.Spike -gt 3) { $Colors.Yellow } else { $Colors.Green }
            $emoji = if ($s.Spike -gt 5) { "🔥" } elseif ($s.Spike -gt 3) { "⚡" } else { "📊" }
            Write-Host "  $($s.Symbol.PadRight(8)) `$($s.Volume24h.ToString('N0').PadRight(15)) $color$emoji $($s.Spike.ToString('F1'))x$($Colors.Reset)     $($s.Change)%"
        }
    }
    Write-Host ""
}

# Export to CSV
function Export-PortfolioCSV {
    $tokens = Get-PortfolioTokens
    $csvData = @()
    
    Write-Host "$($Colors.Yellow)Exporting data...$($Colors.Reset)"
    
    foreach ($token in $tokens) {
        $data = Get-TokenData -Contract $token.address
        if ($data) {
            $csvData += [PSCustomObject]@{
                Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
                Symbol = $data.baseToken.symbol
                Address = $token.address
                Price = $data.priceUsd
                MarketCap = $data.marketCap
                Liquidity = $data.liquidity.usd
                Volume24h = $data.volume.h24
                Change24h = $data.priceChange.h24
                Change1h = $data.priceChange.h1
            }
        }
    }
    
    $filename = "portfolio_data_$(Get-Date -Format 'yyyyMMdd_HHmmss').csv"
    $csvData | Export-Csv -Path $filename -NoTypeInformation
    
    Write-Host "$($Colors.Green)✓ Exported to: $filename$($Colors.Reset)"
    Write-Host "  $($Colors.Cyan)Location: $(Get-Location)\$filename$($Colors.Reset)"
}

# Watch mode
function Watch-Portfolio {
    param([int]$RefreshSeconds = 30)
    
    while ($true) {
        Show-PortfolioHeader
        
        $tokens = Get-PortfolioTokens
        $tokenData = @()
        
        Write-Host "$($Colors.Yellow)Fetching live data...$($Colors.Reset)"
        
        foreach ($contract in $tokens) {
            $data = Get-TokenData -Contract $contract.address
            if ($data) {
                Save-PriceHistory -Symbol $data.baseToken.symbol -Price $data.priceUsd
                $chart = Get-PriceChart -Symbol $data.baseToken.symbol -Width 12
                
                $tokenData += [PSCustomObject]@{
                    Symbol = $data.baseToken.symbol
                    Price = $data.priceUsd
                    Change24h = $data.priceChange.h24
                    Change1h = $data.priceChange.h1
                    Liquidity = $data.liquidity.usd
                    Chart = $chart
                }
            }
        }
        
        # Display table
        Write-Host "$($Colors.Bold)Live Portfolio$($Colors.Reset)"
        Write-Host "───────────────────────────────────────────────────────────────────────"
        Write-Host "Ticker    Price          24h%      1h%       Chart"
        Write-Host "───────────────────────────────────────────────────────────────────────"
        
        foreach ($t in $tokenData) {
            $c24 = Format-PriceChange -Change $t.Change24h
            $c1 = Format-PriceChange -Change $t.Change1h
            Write-Host "$($t.Symbol.PadRight(8)) `$($t.Price.ToString().PadRight(12)) $c24  $c1  $($t.Chart)"
        }
        
        Write-Host ""
        Write-Host "$($Colors.Yellow)Press [Q] to quit | Refreshing in $RefreshSeconds seconds...$($Colors.Reset)"
        
        $waited = 0
        while ($waited -lt $RefreshSeconds) {
            if ($Host.UI.RawUI.KeyAvailable) {
                $key = $Host.UI.RawUI.ReadKey("IncludeKeyDown,NoEcho")
                if ($key.Character -eq 'q' -or $key.Character -eq 'Q') {
                    return
                }
            }
            Start-Sleep -Seconds 1
            $waited++
        }
    }
}

# Search with fzf
function Search-Portfolio {
    $tokens = Get-PortfolioTokens
    $selection = $tokens | ForEach-Object { "$($_.symbol) - $($_.name) [$($_.address)]" } | 
        fzf --height 50% --border --preview "powershell -Command `"`$c = '{}'; Write-Host Token: `$c`"" --preview-window right:50%
    
    if ($selection) {
        $contract = $selection | Select-String -Pattern '\[(.*)\]' | ForEach-Object { $_.Matches.Groups[1].Value }
        $data = Get-TokenData -Contract $contract
        if ($data) {
            $detail = @{
                Symbol = $data.baseToken.symbol
                Name = $data.baseToken.name
                Price = $data.priceUsd
                MarketCap = $data.marketCap
                Liquidity = $data.liquidity.usd
                Volume24h = $data.volume.h24
                Change24h = $data.priceChange.h24
                Change1h = $data.priceChange.h1
                Dex = $data.dexId
            } | ConvertTo-Json -Depth 3
            
            $detail | bat --language=json --style=grid
        }
    }
}

# Simple table view
function Show-PortfolioTable {
    Show-PortfolioHeader
    
    $tokens = Get-PortfolioTokens
    $tokenData = @()
    
    Write-Host "$($Colors.Yellow)Loading portfolio...$($Colors.Reset)"
    
    foreach ($c in $tokens) {
        $data = Get-TokenData -Contract $c.address
        if ($data) {
            Save-PriceHistory -Symbol $data.baseToken.symbol -Price $data.priceUsd
            $tokenData += [PSCustomObject]@{
                Symbol = $data.baseToken.symbol
                Price = $data.priceUsd
                Change24h = $data.priceChange.h24
                Change1h = $data.priceChange.h1
                Liquidity = $data.liquidity.usd
            }
        }
    }
    
    Write-Host ""
    Write-Host "$($Colors.Bold)════════════════════ PORTFOLIO OVERVIEW ════════════════════$($Colors.Reset)"
    Write-Host ""
    Write-Host "Ticker    Price          24h%       1h%        Liquidity"
    Write-Host "──────────────────────────────────────────────────────────────────"
    
    foreach ($t in $tokenData) {
        $c24 = Format-PriceChange -Change $t.Change24h
        $c1 = Format-PriceChange -Change $t.Change1h
        $liq = "`$$(($t.Liquidity/1000).ToString('N0'))K"
        
        Write-Host "$($t.Symbol.PadRight(8)) `$($t.Price.ToString().PadRight(12)) $c24  $c1  $liq"
    }
    
    Write-Host ""
}

# Main menu
function Show-EnhancedMenu {
    Show-PortfolioHeader
    
    Write-Host "$($Colors.Bold)$($Colors.Cyan)📊 MAIN MENU$($Colors.Reset)"
    Write-Host ""
    
    Write-Host "$($Colors.Yellow)Basic Tools:$($Colors.Reset)"
    Write-Host "  [1] Live Portfolio Table"
    Write-Host "  [2] Watch Mode (Auto-refresh)"
    Write-Host "  [3] Search Token (fzf)"
    Write-Host ""
    
    Write-Host "$($Colors.Yellow)Analytics:$($Colors.Reset)"
    Write-Host "  [4] Portfolio Summary (PnL)"
    Write-Host "  [5] Top Movers (Gainers/Losers)"
    Write-Host "  [6] Volume Spike Detector"
    Write-Host ""
    
    Write-Host "$($Colors.Yellow)Data Export:$($Colors.Reset)"
    Write-Host "  [7] Export to CSV"
    Write-Host "  [8] View Price History"
    Write-Host ""
    
    Write-Host "  [Q] Quit"
    Write-Host ""
    
    $choice = Read-Host "Select option"
    
    switch ($choice) {
        "1" { Show-PortfolioTable; Read-Host "Press Enter"; Show-EnhancedMenu }
        "2" { Watch-Portfolio; Show-EnhancedMenu }
        "3" { Search-Portfolio; Read-Host "Press Enter"; Show-EnhancedMenu }
        "4" { Get-PortfolioSummary; Read-Host "Press Enter"; Show-EnhancedMenu }
        "5" { Show-TopMovers; Read-Host "Press Enter"; Show-EnhancedMenu }
        "6" { Find-VolumeSpikes; Read-Host "Press Enter"; Show-EnhancedMenu }
        "7" { Export-PortfolioCSV; Read-Host "Press Enter"; Show-EnhancedMenu }
        "8" {
            Show-PortfolioHeader
            if (Test-Path $script:HistoryFile) {
                Write-Host "$($Colors.Bold)Price History File:$($Colors.Reset) $script:HistoryFile"
                Write-Host ""
                Get-Content $script:HistoryFile | bat --language=json --style=numbers
            } else {
                Write-Host "$($Colors.Yellow)No history yet. Run options 1-5 first to build data.$($Colors.Reset)"
            }
            Read-Host "Press Enter"
            Show-EnhancedMenu
        }
        "q" { exit }
        "Q" { exit }
        default { Show-EnhancedMenu }
    }
}

# Run
Show-EnhancedMenu
