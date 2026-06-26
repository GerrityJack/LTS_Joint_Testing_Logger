param(
    [Parameter(Mandatory=$true)][int]$Port,
    [string]$ComputerName = "localhost"
)
try {
    $client = New-Object System.Net.Sockets.TcpClient
    $client.Connect($ComputerName, $Port)
    $client.Close()
    exit 0
} catch {
    exit 1
}
