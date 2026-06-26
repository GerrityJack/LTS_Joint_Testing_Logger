param(
    [string]$ComputerName = "localhost",
    [int]$Port = 9000
)
# A generic TCP connect check can be fooled by some other, unrelated process
# already squatting on the port. This hits QuestDB's own HTTP API and checks
# for a response shape that's actually QuestDB, not just "something answered."
try {
    $uri = "http://$($ComputerName):$Port/exec?query=SELECT+1"
    $response = Invoke-WebRequest -Uri $uri -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200 -and $response.Content -match '"columns"') {
        exit 0
    } else {
        exit 1
    }
} catch {
    exit 1
}
