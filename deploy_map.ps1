$ErrorActionPreference = "Stop"

$sourceItem = Get-ChildItem -LiteralPath $PSScriptRoot -Filter "LastFront_KargasIV.scx" -File -Recurse |
    Where-Object { $_.FullName -notmatch "\\backup\\" } |
    Sort-Object FullName |
    Select-Object -First 1
$destinationDir = "C:\Users\justk\Documents\StarCraft\Maps"
$destination = Join-Path $destinationDir "LastFront_KargasIV.scx"

if ($null -eq $sourceItem) {
    Write-Host "[failed] Source map file was not found."
    exit 1
}

Write-Host "[copy] $($sourceItem.FullName)"
Write-Host "[to]   $destination"
Write-Host ""

if (!(Test-Path -LiteralPath $destinationDir)) {
    Write-Host "[info] Destination folder does not exist. Creating it."
    New-Item -ItemType Directory -Path $destinationDir | Out-Null
}

Copy-Item -LiteralPath $sourceItem.FullName -Destination $destination -Force

Write-Host ""
Write-Host "[done] Map copied to StarCraft Maps folder."
