# Build the normal trigger bundle, then append test triggers selected for builds.
# Output is the same import file used by SCMDraft.
$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

$out = "KargasIV_Triggers_Mission1Only.txt"
$outPath = Join-Path $PSScriptRoot $out

$triggerParts = Get-ChildItem -Path "Triggers" -Filter "*.txt"
$testParts = @()
if (Test-Path -Path "TestTriggersForBuild") {
    $testParts = Get-ChildItem -Path "TestTriggersForBuild" -Filter "*.txt"
}

$parts = @($triggerParts) + @($testParts) | Sort-Object Name, DirectoryName
$fs = [System.IO.File]::Create($outPath)
try {
    foreach ($p in $parts) {
        $bytes = [System.IO.File]::ReadAllBytes($p.FullName)
        $fs.Write($bytes, 0, $bytes.Length)
    }
} finally {
    $fs.Close()
}

$builtText = [System.IO.File]::ReadAllText($outPath)
Set-Clipboard -Value $builtText

Write-Host "built: $out from $($triggerParts.Count) trigger parts + $($testParts.Count) test parts"
Write-Host "copied to clipboard: $out"
