param(
    [string]$Source = "E:\KargasIV_Work\KargasIV.scx",
    [string]$Output = "E:\KargasIV_Work\KargasIV_compacted.scx"
)

$ErrorActionPreference = "Stop"

$workDir = "E:\SCX_test"
$repairScript = "C:\Users\justk\.codex\skills\repair-starcraft-map\scripts\repair_scx.py"
$lockedCopy = Join-Path $workDir "KargasIV_savecopy.scx"

New-Item -ItemType Directory -Force -Path $workDir | Out-Null

$in = [System.IO.File]::Open(
    $Source,
    [System.IO.FileMode]::Open,
    [System.IO.FileAccess]::Read,
    [System.IO.FileShare]::ReadWrite -bor [System.IO.FileShare]::Delete
)

try {
    $out = [System.IO.File]::Open(
        $lockedCopy,
        [System.IO.FileMode]::Create,
        [System.IO.FileAccess]::Write,
        [System.IO.FileShare]::None
    )
    try {
        $in.CopyTo($out)
    }
    finally {
        $out.Dispose()
    }
}
finally {
    $in.Dispose()
}

python $repairScript $lockedCopy --out $Output --work-dir $workDir
Get-Item -LiteralPath $Output | Select-Object FullName,Length,LastWriteTime | Format-List
