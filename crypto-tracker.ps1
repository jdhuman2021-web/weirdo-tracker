#!/usr/bin/env pwsh
# Enhanced Crypto Portfolio Tracker
# Requires: jq, bat, fzf, ripgrep (all installed)

# Portfolio Configuration
$script:PortfolioFile = "C:\Users\HP\.openclaw\workspace\solana_tracker.json"
$script:Threshold24h = 50  # Alert if >50% change
$script:Threshold1h = 20   # Alert if >20% change
$script:HistoryFile = "C:\Users\HP\.openclaw\workspace\portfolio_history.json"
$script:NotificationEnabled = $true

# Sparkline characters for charts
$script:SparkChars = '▁▂▃▄▅▆▇█'

# Color definitions
$Colors = @{
    Green = "`e[32m"
    Red = "`e[31m"
    Yellow = "`e[33m"
    Blue = "`e[34m"
    Reset = "`e[0m"
    Bold = "`e[1m"
}

function Show-PortfolioHeader {
    Clear-Host
    Write-Host "$($Colors.Bold)$($Colors.Blue)═══════════════════════════════════════════════════════════════$($Colors.Reset)"
    Write-Host "$($Colors.Bold)$($Colors.Blue)  🪙  WEIRDO PORTFOLIO TRACKER  -  $(Get-Date -Format 'yyyy-MM-dd HH:mm UTC')$($Colors.Reset)"
    Write-Host "$($Colors.Bold)$($Colors.Blue)═══════════════════════════════════════════════════════════════$($Colors.Reset)"
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
        return "$($Colors.Green)+$Change%$($Colors.Reset)"
    }
    elseif ($Change -lt 0) {
        return "$($Colors.Red)$Change%$($Colors.Reset)"
    }
    else {
        return "$($Colors.Yellow)0%$($Colors.Reset)"
    }
}

function Get-AlertStatus {
    param([decimal]$Change24h, [decimal]$Change1h)
    
    $alerts = @()
    
    if ([math]::Abs($Change24h) -gt $script:Threshold24h) {
        $alerts += "$($Colors.Red)🚨 24h ALERT$($Colors.Reset)"
    }
    if ([math]::Abs($Change1h) -gt $script:Threshold1h) {
        $alerts += "$($Colors.Yellow)⚠️ 1h ALERT$($Colors.Reset)"
    }
    
    if ($alerts.Count -eq 0) {
        return "$($Colors.Green)✓ Normal$($Colors.Reset)"
    }
    
    return $alerts -join " | "
}

function Show-PortfolioTable {
    param([array]$Tokens)
    
    Write-Host "$($Colors.Bold)Ticker    Price          24h Change    1h Change     Liquidity      Status$($Colors.Reset)"
    Write-Host "─────────────────────────────────────────────────────────────────────────"
    
    foreach ($token in $Tokens) {
        $symbol = $token.Symbol.PadRight(9)
        $price = "$($token.PriceUsd)".PadRight(14)
        $change24h = Format-PriceChange -Change $token.PriceChange24h
        $change1h = Format-PriceChange -Change $token.PriceChange1h
        $liquidity = "`$$(($token.LiquidityUsd / 1000).ToString('N0'))K".PadRight(14)
        $status = Get-AlertStatus -Change24h $token.PriceChange24h -Change1h $token.PriceChange1h
        
        Write-Host "$symbol $price $change24h     $change1h     $liquidity $status"
    }
    
    Write-Host ""
}

function Show-TokenDetail {
    param([string]$Contract)
    
    $data = Get-TokenData -Contract $Contract
    if (-not $data) { return }
    
    $detail = @{
        symbol = $data.baseToken.symbol
        name = $data.baseToken.name
        price = $data.priceUsd
        marketCap = $data.marketCap
        liquidity = $data.liquidity.usd
        volume24h = $data.volume.h24
        change24h = $data.priceChange.h24
        change1h = $data.priceChange.h1
        dexId = $data.dexId
        pairCreatedAt = $data.pairCreatedAt
    } | ConvertTo-Json -Depth 3
    
    # Use bat for pretty output
    $detail | bat --language=json --style=numbers,grid
}

function Get-PortfolioTokens {
    if (Test-Path $script:PortfolioFile) {
        $json = Get-Content $script:PortfolioFile -Raw | ConvertFrom-Json
        return $json.tracked_contracts | Where-Object { $_.status -eq "active" }
    }
    return @()
}

function Watch-Portfolio {
    param([int]$RefreshSeconds = 60)
    
    while ($true) {
        Show-PortfolioHeader
        
        $tokens = Get-PortfolioTokens
        $tokenData = @()
        
        foreach ($contract in $tokens) {
            $data = Get-TokenData -Contract $contract.address
            if ($data) {
                $tokenData += [PSCustomObject]@{
                    Symbol = $data.baseToken.symbol
                    Contract = $contract.address
                    PriceUsd = $data.priceUsd
                    LiquidityUsd = $data.liquidity.usd
                    PriceChange24h = $data.priceChange.h24
                    PriceChange1h = $data.priceChange.h1
                }
            }
        }
        
        Show-PortfolioTable -Tokens $tokenData
        
        Write-Host "$($Colors.Yellow)Press [Q] to quit | Refreshing in $RefreshSeconds seconds...$($Colors.Reset)"
        
        # Wait with key detection
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

function Search-Portfolio {
    $tokens = Get-PortfolioTokens
    $selection = $tokens | ForEach-Object { "$($_.symbol) - $($_.name) [$($_.address)]" } | 
        fzf --preview "powershell -Command { `$c = echo {} | Select-String -Pattern '\[(.*)\]' | % { `$_.Matches.Groups[1].Value }; Get-Content '$script:PortfolioFile' | jq `.tracked_contracts[] | select(.address == '`$c')` }"
    
    if ($selection) {
        $contract = $selection | Select-String -Pattern '\[(.*)\]' | % { $_.Matches.Groups[1].Value }
        Show-TokenDetail -Contract $contract
    }
}

# Wallet Tracking Configuration
$script:WalletTrackerFile = "C:\Users\HP\.openclaw\workspace\wallet_tracker.json"

# ANSI Sparkline function
function Get-Sparkline {
    param([array]$Values)
    
    if ($Values.Count -eq 0) { return "" }
    
    $min = ($Values | Measure-Object -Minimum).Minimum
    $max = ($Values | Measure-Object -Maximum).Maximum
    $range = $max - $min
    
    if ($range -eq 0) { return $script:SparkChars[0] * $Values.Count }
    
    $result = ""
    foreach ($val in $Values) {
        $index = [math]::Floor((($val - $min) / $range) * ($script:SparkChars.Length - 1))
        $result += $script:SparkChars[$index]
    }
    return $result
}

# Save price history for charting
function Save-PriceHistory {
    param([string]$Symbol, [decimal]$Price)
    
    $history = @{}
    if (Test-Path $script:HistoryFile) {
        $history = Get-Content $script:HistoryFile -Raw | ConvertFrom-Json
    }
    
    if (-not $history.$Symbol) {
        $history.$Symbol = @()
    }
    
    $history.$Symbol += @{
        timestamp = (Get-Date -Format "o")
        price = $Price
    }
    
    # Keep last 50 data points
    if ($history.$Symbol.Count -gt 50) {
        $history.$Symbol = $history.$Symbol[-50..-1]
    }
    
    $history | ConvertTo-Json -Depth 5 | Out-File $script:HistoryFile
}

# Get price chart for a token
function Get-PriceChart {
    param([string]$Symbol, [int]$Width = 30)
    
    if (-not (Test-Path $script:HistoryFile)) { return "No history" }
    
    $history = Get-Content $script:HistoryFile -Raw | ConvertFrom-Json
    if (-not $history.$Symbol -or $history.$Symbol.Count -lt 2) { 
        return "Insufficient history" 
    }
    
    $prices = $history.$Symbol | Select-Object -Last $Width | ForEach-Object { $_.price }
    $sparkline = Get-Sparkline -Values $prices
    
    $firstPrice = $prices[0]
    $lastPrice = $prices[-1]
    $change = (($lastPrice - $firstPrice) / $firstPrice) * 100
    
    $changeColor = if ($change -gt 0) { $Colors.Green } else { $Colors.Red }
    return "$sparkline $($changeColor)$($change.ToString('F2'))%$($Colors.Reset)"
}

# Compare token performance
function Compare-Tokens {
    param([string[]]$Contracts)
    
    Show-PortfolioHeader
    Write-Host "$($Colors.Bold)Token Comparison (24h Performance):$($Colors.Reset)"
    Write-Host ""
    
    $comparison = @()
    foreach ($contract in $Contracts) {
        $data = Get-TokenData -Contract $contract
        if ($data) {
            $comparison += [PSCustomObject]@{
                Symbol = $data.baseToken.symbol
                Price = $data.priceUsd
                Change24h = $data.priceChange.h24
                Change1h = $data.priceChange.h1
                Volume = $data.volume.h24
                Liquidity = $data.liquidity.usd
                Chart = Get-PriceChart -Symbol $data.baseToken.symbol -Width 20
            }
        }
    }
    
    # Sort by 24h performance
    $comparison = $comparison | Sort-Object Change24h -Descending
    
    Write-Host "Rank  Symbol    Price          24h%      1h%       Chart"
    Write-Host "────  ────────  ─────────────  ───────── ───────── ──────────────────────────"
    
    $rank = 1
    foreach ($token in $comparison) {
        $rankStr = "$rank".PadRight(4)
        $symbol = $token.Symbol.PadRight(9)
        $price = "$($token.Price)".PadRight(14)
        $c24 = "$($token.Change24h)%".PadRight(9)
        $c1 = "$($token.Change1h)%".PadRight(9)
        
        Write-Host "$rankStr $symbol $price $c24 $c1 $($token.Chart)"
        $rank++
    }
    
    Write-Host ""
}

# Portfolio summary with PnL calculation
function Get-PortfolioSummary {
    Show-PortfolioHeader
    
    $tokens = Get-PortfolioTokens
    $totalValue = 0
    $totalInvested = 0
    $tokenPerformance = @()
    
    foreach ($token in $tokens) {
        $data = Get-TokenData -Contract $token.address
        if ($data) {
            # Simulate holdings (you'd need to add this to solana_tracker.json)
            $holding = if ($token.holding) { $token.holding } else { 1000 } # Default for demo
            $investedPrice = if ($token.avgBuyPrice) { $token.avgBuyPrice } else { $data.priceUsd * 0.8 } # Estimate
            
            $currentValue = $holding * $data.priceUsd
            $investedValue = $holding * $investedPrice
            $pnl = $currentValue - $investedValue
            $pnlPercent = ($pnl / $investedValue) * 100
            
            $totalValue += $currentValue
            $totalInvested += $investedValue
            
            $tokenPerformance += [PSCustomObject]@{
                Symbol = $data.baseToken.symbol
                Holdings = $holding
                AvgBuy = $investedPrice
                CurrentPrice = $data.priceUsd
                Value = $currentValue
                Invested = $investedValue
                PnL = $pnl
                PnLPercent = $pnlPercent
                Chart = Get-PriceChart -Symbol $data.baseToken.symbol -Width 15
            }
            
            Save-PriceHistory -Symbol $data.baseToken.symbol -Price $data.priceUsd
        }
    }
    
    $totalPnL = $totalValue - $totalInvested
    $totalPnLPercent = if ($totalInvested -gt 0) { ($totalPnL / $totalInvested) * 100 } else { 0 }
    
    # Summary header
    Write-Host "$($Colors.Bold)═══════════════════════════════════════════════════════════════════$($Colors.Reset)"
    Write-Host "$($Colors.Bold)                   PORTFOLIO PERFORMANCE SUMMARY$($Colors.Reset)"
    Write-Host "$($Colors.Bold)═══════════════════════════════════════════════════════════════════$($Colors.Reset)"
    Write-Host ""
    
    # Overall stats
    $pnlColor = if ($totalPnL -gt 0) { $Colors.Green } else { $Colors.Red }
    Write-Host "Total Invested:  `$($totalInvested.ToString('N2'))"
    Write-Host "Current Value:   `$($totalValue.ToString('N2'))"
    Write-Host "Total PnL:       $pnlColor`$$($totalPnL.ToString('N2')) ($($totalPnLPercent.ToString('F2'))%)$($Colors.Reset)"
    Write-Host ""
    Write-Host "$($Colors.Bold)Token Breakdown:$($Colors.Reset)"
    Write-Host "─────────────────────────────────────────────────────────────────────"
    
    foreach ($t in $tokenPerformance | Sort-Object PnL -Descending) {
        $pnlStr = if ($t.PnL -gt 0) { "+$($t.PnL.ToString('N2'))" } else { "$($t.PnL.ToString('N2'))" }
        $pnlPctStr = if ($t.PnLPercent -gt 0) { "+$($t.PnLPercent.ToString('F1'))%" } else { "$($t.PnLPercent.ToString('F1'))%" }
        $color = if ($t.PnL -gt 0) { $Colors.Green } else { $Colors.Red }
        
        Write-Host "$($t.Symbol.PadRight(8)) Value: `$($t.Value.ToString('N2').PadRight(12)) PnL: $color`$$pnlStr ($pnlPctStr)$($Colors.Reset) $($t.Chart)"
    }
    
    Write-Host ""
}

# Top gainers/losers
function Show-TopMovers {
    param([int]$Count = 5, [string]$Timeframe = "24h")
    
    Show-PortfolioHeader
    Write-Host "$($Colors.Bold)Top $Count Movers ($Timeframe):$($Colors.Reset)"
    Write-Host ""
    
    $tokens = Get-PortfolioTokens
    $allTokens = @()
    
    foreach ($token in $tokens) {
        $data = Get-TokenData -Contract $token.address
        if ($data) {
            $change = if ($Timeframe -eq "1h") { $data.priceChange.h1 } else { $data.priceChange.h24 }
            $allTokens += [PSCustomObject]@{
                Symbol = $data.baseToken.symbol
                Price = $data.priceUsd
                Change = $change
                Liquidity = $data.liquidity.usd
            }
        }
    }
    
    # Gainers
    Write-Host "$($Colors.Green)🚀 Top Gainers:$($Colors.Reset)"
    $gainers = $allTokens | Where-Object { $_.Change -gt 0 } | Sort-Object Change -Descending | Select-Object -First $Count
    foreach ($t in $gainers) {
        Write-Host "  $($t.Symbol.PadRight(8)) +$($t.Change.ToString('F2'))%  @ `$($t.Price)  [Liq: `$($($t.Liquidity/1000).ToString('N0'))K]"
    }
    Write-Host ""
    
    # Losers
    Write-Host "$($Colors.Red)📉 Top Losers:$($Colors.Reset)"
    $losers = $allTokens | Where-Object { $_.Change -lt 0 } | Sort-Object Change | Select-Object -First $Count
    foreach ($t in $losers) {
        Write-Host "  $($t.Symbol.PadRight(8)) $($t.Change.ToString('F2'))%  @ `$($t.Price)  [Liq: `$($($t.Liquidity/1000).ToString('N0'))K]"
    }
    Write-Host ""
}

# Volume spike detector
function Find-VolumeSpikes {
    param([decimal]$Multiplier = 2)
    
    Show-PortfolioHeader
    Write-Host "$($Colors.Bold)Volume Spike Detection (>${Multiplier}x average):$($Colors.Reset)"
    Write-Host ""
    
    $tokens = Get-PortfolioTokens
    $spikes = @()
    
    foreach ($token in $tokens) {
        $data = Get-TokenData -Contract $token.address
        if ($data -and $data.volume -and $data.volume.h6) {
            $avgVolume = $data.volume.h6 / 6  # Average per hour over 6h
            $currentVolume = $data.volume.h24 / 24  # Current hourly rate
            
            if ($currentVolume -gt ($avgVolume * $Multiplier)) {
                $spikes += [PSCustomObject]@{
                    Symbol = $data.baseToken.symbol
                    Volume24h = $data.volume.h24
                    Volume6h = $data.volume.h6
                    Multiplier = ($currentVolume / $avgVolume).ToString('F1')
                    PriceChange = $data.priceChange.h24
                }
            }
        }
    }
    
    if ($spikes.Count -eq 0) {
        Write-Host "$($Colors.Yellow)No volume spikes detected$($Colors.Reset)"
    } else {
        Write-Host "Symbol    24h Volume      6h Avg        Multiplier    Price Change"
        Write-Host "────────  ──────────────  ────────────  ────────────  ────────────"
        foreach ($s in $spikes) {
            $multiplierColor = if ([decimal]$s.Multiplier -gt 3) { $Colors.Red } elseif ([decimal]$s.Multiplier -gt 2) { $Colors.Yellow } else { $Colors.Green }
            Write-Host "$($s.Symbol.PadRight(8)) `$($s.Volume24h.ToString('N0').PadRight(14)) `$($s.Volume6h.ToString('N0').PadRight(12)) $multiplierColor`$($s.Multiplier)x$($Colors.Reset)     $($s.PriceChange)%"
        }
    }
    Write-Host ""
}

# Market scanner (find new opportunities)
function Find-NewOpportunities {
    param([decimal]$MinVolume = 50000, [decimal]$MaxMarketCap = 500000)
    
    Show-PortfolioHeader
    Write-Host "$($Colors.Bold)Scanner: New Opportunities$($Colors.Reset)"
    Write-Host "Criteria: Vol >`$$MinVolume, MC <`$$MaxMarketCap"
    Write-Host ""
    
    # This would scan DexScreener's top pairs endpoint
    # For demo, we'll check current portfolio tokens
    $tokens = Get-PortfolioTokens
    $opportunities = @()
    
    foreach ($token in $tokens) {
        $data = Get-TokenData -Contract $token.address
        if ($data -and $data.volume.h24 -gt $MinVolume -and $data.marketCap -lt $MaxMarketCap) {
            $score = ($data.volume.h24 / 1000) * [math]::Abs($data.priceChange.h24) / 100
            $opportunities += [PSCustomObject]@{
                Symbol = $data.baseToken.symbol
                MarketCap = $data.marketCap
                Volume24h = $data.volume.h24
                Change24h = $data.priceChange.h24
                Liquidity = $data.liquidity.usd
                Score = $score
                Age = if ($data.pairCreatedAt) { 
                    ([DateTime]::Now - [DateTime]::FromFileTimeUtc($data.pairCreatedAt)).Days 
                } else { "Unknown" }
            }
        }
    }
    
    $opportunities = $opportunities | Sort-Object Score -Descending
    
    Write-Host "Rank  Symbol    MCAP           Volume    24h%      Liq       Age   Score"
    Write-Host "────  ────────  ─────────────  ────────  ────────  ────────  ────  ─────"
    
    $rank = 1
    foreach ($opp in $opportunities | Select-Object -First 10) {
        Write-Host "$($rank.ToString().PadRight(4)) $($opp.Symbol.PadRight(8)) `$($opp.MarketCap.ToString('N0').PadRight(14)) `$($opp.Volume24h.ToString('N0').PadRight(8)) $($opp.Change24h.ToString('F1').PadRight(8)) `$($opp.Liquidity.ToString('N0').PadRight(8)) $($opp.Age.ToString().PadRight(4)) $($opp.Score.ToString('F0'))"
        $rank++
    }
    Write-Host ""
}

# Export to CSV for Excel analysis
function Export-PortfolioCSV {
    $tokens = Get-PortfolioTokens
    $csvData = @()
    
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
                Dex = $data.dexId
            }
        }
    }
    
    $filename = "portfolio_data_$(Get-Date -Format 'yyyyMMdd_HHmmss').csv"
    $csvData | Export-Csv -Path $filename -NoTypeInformation
    Write-Host "$($Colors.Green)✓ Exported to $filename$($Colors.Reset)"
}

# Notification system (Windows Toast)
function Send-PortfolioAlert {
    param([string]$Title, [string]$Message, [string]$Severity = "info")
    
    if (-not $script:NotificationEnabled) { return }
    
    try {
        # Requires BurntToast module (optional enhancement)
        Import-Module BurntToast -ErrorAction SilentlyContinue
        if (Get-Module BurntToast) {
            $icon = switch ($Severity) {
                "error" { "❌" }
                "warning" { "⚠️" }
                "success" { "✅" }
                default { "ℹ️" }
            }
            New-BurntToastNotification -Text "$icon $Title", $Message
        }
    }
    catch {
        # Fallback to console notification
        Write-Host "$($Colors.Yellow)[$Title] $Message$($Colors.Reset)"
    }
}

# Back to Main Menu
function Show-EnhancedMenu {
    Show-PortfolioHeader
    
    Write-Host "$($Colors.Bold)═══════════════════════════════════════════════════════════════$($Colors.Reset)"
    Write-Host "$($Colors.Bold)  📊 ENHANCED PORTFOLIO TRACKER$($Colors.Reset)"
    Write-Host "$($Colors.Bold)═══════════════════════════════════════════════════════════════$($Colors.Reset)"
    Write-Host ""
    
    Write-Host "$($Colors.Bold)Basic:$($Colors.Reset)"
    Write-Host "  [1]  Live Portfolio Table"
    Write-Host "  [2]  Watch Mode (Auto-refresh)"
    Write-Host "  [3]  Search Token Details"
    Write-Host "  [4]  Export to JSON"
    Write-Host "  [5]  Check Alerts Only"
    Write-Host ""
    
    Write-Host "$($Colors.Bold)Analytics:$($Colors.Reset)"
    Write-Host "  [6]  Portfolio Summary (PnL)"
    Write-Host "  [7]  Token Comparison"
    Write-Host "  [8]  Top Movers (Gainers/Losers)"
    Write-Host "  [9]  Price Charts (Sparklines)"
    Write-Host "  [10] Volume Spike Detector"
    Write-Host "  [11] Opportunity Scanner"
    Write-Host ""
    
    Write-Host "$($Colors.Bold)Data:$($Colors.Reset)"
    Write-Host "  [12] Export to CSV (Excel)"
    Write-Host "  [13] View Price History"
    Write-Host ""
    
    Write-Host "  [Q]  Quit"
    Write-Host ""
    
    $choice = Read-Host "Select option"
    
    switch ($choice) {
        "1" { 
            Show-PortfolioHeader
            $tokens = Get-PortfolioTokens
            $tokenData = @()
            foreach ($c in $tokens) {
                $data = Get-TokenData -Contract $c.address
                if ($data) {
                    $tokenData += [PSCustomObject]@{
                        Symbol = $data.baseToken.symbol
                        PriceUsd = $data.priceUsd
                        LiquidityUsd = $data.liquidity.usd
                        PriceChange24h = $data.priceChange.h24
                        PriceChange1h = $data.priceChange.h1
                    }
                    Save-PriceHistory -Symbol $data.baseToken.symbol -Price $data.priceUsd
                }
            }
            Show-PortfolioTable -Tokens $tokenData
            Read-Host "Press Enter to continue"
            Show-EnhancedMenu
        }
        "2" { Watch-Portfolio }
        "3" { Search-Portfolio; Show-EnhancedMenu }
        "4" { 
            $tokens = Get-PortfolioTokens
            $output = @{tokens = @(); timestamp = (Get-Date -Format "o")}
            foreach ($c in $tokens) {
                $data = Get-TokenData -Contract $c.address
                if ($data) { $output.tokens += $data }
            }
            $output | ConvertTo-Json -Depth 5 | Out-File "portfolio_export_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
            Write-Host "$($Colors.Green)✓ Exported to JSON$($Colors.Reset)"
            Start-Sleep -Seconds 2
            Show-EnhancedMenu
        }
        "5" {
            Show-PortfolioHeader
            Write-Host "$($Colors.Bold)Active Alerts:$($Colors.Reset)"
            $tokens = Get-PortfolioTokens
            foreach ($c in $tokens) {
                $data = Get-TokenData -Contract $c.address
                if ($data -and ([math]::Abs($data.priceChange.h24) -gt $script:Threshold24h -or [math]::Abs($data.priceChange.h1) -gt $script:Threshold1h)) {
                    Write-Host "$($Colors.Red)$($data.baseToken.symbol): $($data.priceChange.h24)% (24h), $($data.priceChange.h1)% (1h)$($Colors.Reset)"
                }
            }
            Read-Host "Press Enter to continue"
            Show-EnhancedMenu
        }
        "6" { Get-PortfolioSummary; Read-Host "Press Enter to continue"; Show-EnhancedMenu }
        "7" { 
            $tokens = Get-PortfolioTokens
            $contracts = $tokens | ForEach-Object { $_.address }
            Compare-Tokens -Contracts $contracts
            Read-Host "Press Enter to continue"
            Show-EnhancedMenu
        }
        "8" { Show-TopMovers; Read-Host "Press Enter to continue"; Show-EnhancedMenu }
        "9" {
            Show-PortfolioHeader
            Write-Host "$($Colors.Bold)Price Charts (Last 30 data points):$($Colors.Reset)"
            Write-Host ""
            $tokens = Get-PortfolioTokens
            foreach ($t in $tokens) {
                $data = Get-TokenData -Contract $t.address
                if ($data) {
                    Save-PriceHistory -Symbol $data.baseToken.symbol -Price $data.priceUsd
                    $chart = Get-PriceChart -Symbol $data.baseToken.symbol -Width 30
                    Write-Host "$($data.baseToken.symbol.PadRight(8)) $chart"
                }
            }
            Read-Host "Press Enter to continue"
            Show-EnhancedMenu
        }
        "10" { Find-VolumeSpikes; Read-Host "Press Enter to continue"; Show-EnhancedMenu }
        "11" { Find-NewOpportunities; Read-Host "Press Enter to continue"; Show-EnhancedMenu }
        "12" { Export-PortfolioCSV; Read-Host "Press Enter to continue"; Show-EnhancedMenu }
        "13" {
            Show-PortfolioHeader
            if (Test-Path $script:HistoryFile) {
                Get-Content $script:HistoryFile | bat --language=json
            } else {
                Write-Host "$($Colors.Yellow)No price history available. Run option 1 or 9 first.$($Colors.Reset)"
            }
            Read-Host "Press Enter to continue"
            Show-EnhancedMenu
        }
        "q" { exit }
        "Q" { exit }
        default { Show-EnhancedMenu }
    }
}

# Override the original menu
function Show-MainMenu {
    Show-EnhancedMenu
}
