$repos = @(
    'auton','e2ee-messenger','frontier-bastion','harmony-medspa','home-hub',
    'JumpQuest','lancewfisher-v2','market-dashboard','master-trade-bot',
    'master-trading-system','noco-app-demos','one-three-net','polymarket-sniper',
    'polymarketbtc15massistant','profit-desk','project-hub','solana-bot',
    'tax-prep-system','trading-profit-engine'
)

foreach ($r in $repos) {
    $p = "D:\ProjectsHome\$r"
    if (Test-Path "$p\.git") {
        $status = git -C $p status --porcelain 2>$null
        if ($status) {
            Write-Host "   [!!] $r  has uncommitted changes"
        } else {
            Write-Host "   [OK] $r"
        }
    } else {
        Write-Host "   [--] $r  (no git repo)"
    }
}
