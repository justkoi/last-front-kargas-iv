$ErrorActionPreference = "Stop"

$scmdraft = "E:\SCMDraft_clean\ScmDraft 2.exe"
$map = "E:\KargasIV_Work\KargasIV_legacy_str.scx"

if (-not (Test-Path -LiteralPath $scmdraft)) {
    throw "SCMDraft clean executable not found: $scmdraft"
}

if (-not (Test-Path -LiteralPath $map)) {
    throw "Map not found: $map"
}

Start-Process -FilePath $scmdraft -ArgumentList "`"$map`"" -WorkingDirectory (Split-Path -Parent $scmdraft) -WindowStyle Normal
