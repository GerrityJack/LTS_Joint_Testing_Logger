param(
    [Parameter(Mandatory=$true)][string]$ScriptName
)
$procs = Get-CimInstance Win32_Process | Where-Object {
    $_.Name -eq 'python.exe' -and $_.CommandLine -like "*$ScriptName*"
}
if ($procs) {
    exit 1
} else {
    exit 0
}
