$ErrorActionPreference = "Stop"

$scmdraftDir = "E:\SCMDraft_alpha_20200624"
$archiveDir = Join-Path $scmdraftDir ("backupDB_archived_" + (Get-Date -Format "yyyyMMdd_HHmmss"))

$running = Get-Process -Name "ScmDraft 2" -ErrorAction SilentlyContinue
if ($running) {
    throw "Close SCMDraft first. Running process id(s): $($running.Id -join ', ')"
}

$dbFiles = Get-ChildItem -LiteralPath $scmdraftDir -Filter "backupDB*.scmdDB" -File
if (-not $dbFiles) {
    Write-Host "No backupDB files found."
    exit 0
}

New-Item -ItemType Directory -Force -Path $archiveDir | Out-Null

foreach ($file in $dbFiles) {
    Move-Item -LiteralPath $file.FullName -Destination (Join-Path $archiveDir $file.Name)
}

Write-Host "Moved $($dbFiles.Count) backup database file(s) to:"
Write-Host $archiveDir
Write-Host "SCMDraft will create a fresh backup database on next launch."
