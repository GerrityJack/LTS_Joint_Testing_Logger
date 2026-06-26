param(
    [string]$ComputerName = "localhost",
    [int]$Port = 3000
)
# Same reasoning as check_questdb.ps1 -- verify it's actually Grafana
# answering, not just any process on the port. Grafana's /api/health
# endpoint returns JSON containing a "database" field when it's really up.
try {
    $uri = "http://$($ComputerName):$Port/api/health"
    $response = Invoke-WebRequest -Uri $uri -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200 -and $response.Content -match '"database"') {
        exit 0
    } else {
        exit 1
    }
} catch {
    exit 1
}
