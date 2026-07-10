param(
    [string]$Source = "",
    [string]$DestinationDir = "$env:USERPROFILE\Documents\StarCraft\Maps",
    [string]$DestinationName = "KargasIV_R.scx",
    [string]$WorkDir = "E:\SCX_WORK",
    [switch]$WhatIf
)

$ErrorActionPreference = "Stop"

Set-Location -LiteralPath $PSScriptRoot

$pythonCandidates = @(
    "C:\Users\justk\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe",
    "python"
)
$repairTool = "C:\Users\justk\.codex\skills\repair-starcraft-map\scripts\repair_scx.py"
$protectTool = Join-Path $PSScriptRoot "protect_scx.py"
$stringRecoveryTool = Join-Path $PSScriptRoot "recover_map_strings_cp949.py"
$triggerTextPath = Join-Path $PSScriptRoot "KargasIV_Triggers_Mission1Only.txt"
$briefingTextPath = Join-Path $PSScriptRoot "KargasIV_Briefing.txt"
$forceNamesPath = Join-Path $PSScriptRoot "ForceNames.md"

function Resolve-Python {
    foreach ($candidate in $pythonCandidates) {
        if (Test-Path -LiteralPath $candidate) {
            return $candidate
        }

        $command = Get-Command $candidate -ErrorAction SilentlyContinue
        if ($null -ne $command) {
            return $candidate
        }
    }

    throw "Python was not found."
}

function Resolve-SourceMap([string]$RequestedSource) {
    if (-not [string]::IsNullOrWhiteSpace($RequestedSource)) {
        $sourcePath = if ([System.IO.Path]::IsPathRooted($RequestedSource)) {
            $RequestedSource
        }
        else {
            Join-Path $PSScriptRoot $RequestedSource
        }

        if (-not (Test-Path -LiteralPath $sourcePath)) {
            throw "Source map not found: $sourcePath"
        }

        return Get-Item -LiteralPath $sourcePath
    }

    $preferredSource = Join-Path $PSScriptRoot "최후의 전선 카르가스 IV\KargasIV.scx"
    if (Test-Path -LiteralPath $preferredSource) {
        return Get-Item -LiteralPath $preferredSource
    }

    $sourceMap = Get-ChildItem -Path (Join-Path $PSScriptRoot "*\KargasIV.scx") -File |
        Where-Object { $_.BaseName -notmatch "(_clean|_protected)(_|$)" } |
        Sort-Object FullName |
        Select-Object -First 1

    if ($null -eq $sourceMap) {
        Write-Host "[failed] Source map file was not found."
        Write-Host "[root]   $PSScriptRoot"
        Write-Host "[pattern] *\KargasIV.scx"
        exit 1
    }

    return $sourceMap
}

function Assert-BuildTools {
    if (-not (Test-Path -LiteralPath $repairTool)) {
        throw "Repair tool not found: $repairTool"
    }

    if (-not (Test-Path -LiteralPath $protectTool)) {
        throw "Protect tool not found: $protectTool"
    }

    if (-not (Test-Path -LiteralPath $stringRecoveryTool)) {
        throw "String recovery tool not found: $stringRecoveryTool"
    }

    if (-not (Test-Path -LiteralPath $triggerTextPath)) {
        throw "Trigger text not found. Run build_triggers.ps1 first: $triggerTextPath"
    }

    if (-not (Test-Path -LiteralPath $briefingTextPath)) {
        throw "Briefing text not found: $briefingTextPath"
    }

    if (-not (Test-Path -LiteralPath $forceNamesPath)) {
        throw "Force names file not found: $forceNamesPath"
    }
}

function Get-IncludedTestTriggerParts {
    $testTriggerDir = Join-Path $PSScriptRoot "TestTriggersForBuild"
    if (-not (Test-Path -LiteralPath $testTriggerDir)) {
        return @()
    }

    if (-not (Test-Path -LiteralPath $triggerTextPath)) {
        return @()
    }

    $builtTriggers = [System.IO.File]::ReadAllText($triggerTextPath)
    $testTriggerParts = @(Get-ChildItem -LiteralPath $testTriggerDir -Filter "*.txt" -File)

    return @($testTriggerParts | Where-Object {
        $testText = [System.IO.File]::ReadAllText($_.FullName)
        -not [string]::IsNullOrWhiteSpace($testText) -and
            $builtTriggers.IndexOf($testText, [System.StringComparison]::Ordinal) -ge 0
    })
}

function Get-TestTriggerPartCount {
    $testTriggerDir = Join-Path $PSScriptRoot "TestTriggersForBuild"
    if (-not (Test-Path -LiteralPath $testTriggerDir)) {
        return 0
    }

    return @(Get-ChildItem -LiteralPath $testTriggerDir -Filter "*.txt" -File).Count
}

function Add-TestSuffixToMapName([string]$MapName) {
    $extension = [System.IO.Path]::GetExtension($MapName)
    $baseName = [System.IO.Path]::GetFileNameWithoutExtension($MapName)

    if ($baseName.EndsWith("_T", [System.StringComparison]::OrdinalIgnoreCase)) {
        return $MapName
    }

    return "$baseName`_T$extension"
}

function Invoke-Repair([string]$Python, [string]$SourceMap, [string]$CleanOut) {
    Write-Host "[clean]  $SourceMap"
    Write-Host "[clean]  -> $CleanOut"
    & $Python $repairTool $SourceMap --out $CleanOut --work-dir $WorkDir
    if ($LASTEXITCODE -ne 0) {
        throw "Clean map build failed."
    }
}

function Invoke-StringRecovery([string]$Python, [string]$MapPath) {
    $recoveredOut = Join-Path $WorkDir "kargas_strings_cp949_recovered.scx"
    Write-Host "[strings] Recover UTF-8 trigger and briefing strings to CP949"
    Write-Host "[strings] $MapPath"
    Write-Host "[strings] -> $recoveredOut"
    & $Python $stringRecoveryTool $MapPath --out $recoveredOut --work-dir $WorkDir --trigger-text $triggerTextPath --briefing-text $briefingTextPath --force-names $forceNamesPath
    if ($LASTEXITCODE -ne 0) {
        throw "String encoding recovery failed."
    }

    Copy-Item -LiteralPath $recoveredOut -Destination $MapPath -Force
    Write-Host "[strings] updated clean map string table."
}

function Invoke-NormalizeStrx([string]$Python, [string]$MapPath) {
    $normalizedOut = Join-Path $WorkDir "kargas_strx_normalized.scx"
    Write-Host "[strx] Normalize STRx offsets after string recovery"
    Write-Host "[strx] $MapPath"
    Write-Host "[strx] -> $normalizedOut"
    & $Python $repairTool $MapPath --out $normalizedOut --work-dir $WorkDir
    if ($LASTEXITCODE -ne 0) {
        throw "STRx normalization failed."
    }

    Copy-Item -LiteralPath $normalizedOut -Destination $MapPath -Force
    Write-Host "[strx] updated clean map string table offsets."
}

function Protect-Map([string]$Python, [string]$CleanMap, [string]$ProtectedOut) {
    Write-Host "[protect] $CleanMap"
    Write-Host "[protect] -> $ProtectedOut"
    & $Python $protectTool $CleanMap --out $ProtectedOut --work-dir $WorkDir --locale 0x409
    if ($LASTEXITCODE -ne 0) {
        throw "Protected map build failed."
    }
}

function Test-Readable([string]$Python, [string]$Map) {
    $verifyLog = Join-Path $WorkDir "verify_kargas_protected_map.log"
    & $Python $repairTool $Map --analyze --work-dir $WorkDir > $verifyLog 2>&1
    if ($LASTEXITCODE -ne 0) {
        Get-Content -LiteralPath $verifyLog | Select-Object -First 40
        throw "Protected map verification failed."
    }

    Write-Host "[verify] protected map scenario.chk is readable."
}

function Copy-WithRetry([string]$SourcePath, [string]$DestinationPath) {
    for ($attempt = 1; $attempt -le 10; $attempt++) {
        try {
            Copy-Item -LiteralPath $SourcePath -Destination $DestinationPath -Force -ErrorAction Stop
            return
        }
        catch {
            if ($attempt -eq 10) {
                throw
            }

            Start-Sleep -Milliseconds 500
        }
    }
}

$sourceMap = Resolve-SourceMap $Source
if ($sourceMap.Extension -notmatch "^\.(scx|scm)$") {
    throw "Input must be .scx or .scm: $($sourceMap.FullName)"
}

$cleanOut = Join-Path $sourceMap.DirectoryName ($sourceMap.BaseName + "_clean.scx")
$protectedOut = Join-Path $sourceMap.DirectoryName ($sourceMap.BaseName + "_clean_protected.scx")
$includedTestTriggerParts = Get-IncludedTestTriggerParts
$deployName = if ($includedTestTriggerParts.Count -gt 0) {
    Add-TestSuffixToMapName $DestinationName
}
else {
    $DestinationName
}
$destination = Join-Path $DestinationDir $deployName

Write-Host "[source]    $($sourceMap.FullName)"
Write-Host "[clean]     $cleanOut"
Write-Host "[protected] $protectedOut"
$testTriggerPartCount = Get-TestTriggerPartCount
if ($includedTestTriggerParts.Count -gt 0) {
    Write-Host "[test]      $($includedTestTriggerParts.Count) of $testTriggerPartCount test trigger part(s) included; deploy name gets _T suffix."
}
elseif ($testTriggerPartCount -gt 0) {
    Write-Host "[test]      0 of $testTriggerPartCount test trigger part(s) included; deploy name stays normal."
}
Write-Host "[deploy]    $destination"
Write-Host ""

if ($WhatIf) {
    Write-Host "[what-if] Clean/protect/deploy steps skipped."
    exit 0
}

Assert-BuildTools
$python = Resolve-Python

New-Item -ItemType Directory -Path $WorkDir -Force | Out-Null
Invoke-Repair $python $sourceMap.FullName $cleanOut
Invoke-StringRecovery $python $cleanOut
Invoke-NormalizeStrx $python $cleanOut
Protect-Map $python $cleanOut $protectedOut
Test-Readable $python $protectedOut

if (-not (Test-Path -LiteralPath $DestinationDir)) {
    Write-Host "[deploy] Creating destination: $DestinationDir"
    New-Item -ItemType Directory -Path $DestinationDir | Out-Null
}

Write-Host "[deploy] $protectedOut -> $destination"
Copy-WithRetry $protectedOut $destination

Write-Host ""
Write-Host "[done] Clean protected map built and copied to StarCraft Maps folder."
