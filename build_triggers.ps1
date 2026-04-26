# Triggers/ 폴더의 파일들을 바이트 단위로 이어붙여
# KargasIV_Triggers_Mission1Only.txt 를 생성한다 (인코딩 변환 없음).
$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot
$out = "KargasIV_Triggers_Mission1Only.txt"
$parts = Get-ChildItem -Path "Triggers" -Filter "*.txt" | Sort-Object Name
$outPath = Join-Path $PSScriptRoot $out
$fs = [System.IO.File]::Create($outPath)
try {
    foreach ($p in $parts) {
        $bytes = [System.IO.File]::ReadAllBytes($p.FullName)
        $fs.Write($bytes, 0, $bytes.Length)
    }
} finally {
    $fs.Close()
}
Write-Host "built: $out from $($parts.Count) parts"
