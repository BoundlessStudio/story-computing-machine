#Requires -Version 7.0

function Get-PipelineRawSha256 {
    param([Parameter(Mandatory = $true)][string]$Path)

    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function ConvertFrom-PipelineJson {
    param([Parameter(Mandatory = $true)][string]$Json)

    $Parameters = @{}
    if ((Get-Command ConvertFrom-Json).Parameters.ContainsKey('DateKind')) {
        $Parameters.DateKind = 'String'
    }
    return $Json | ConvertFrom-Json @Parameters
}

function Get-PipelineSha256ForBytes {
    param([Parameter(Mandatory = $true)][byte[]]$Bytes)

    return [Convert]::ToHexString(
        [Security.Cryptography.SHA256]::HashData($Bytes)
    ).ToLowerInvariant()
}

function Write-PipelineBytesAtomically {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][byte[]]$Bytes
    )

    $Temporary = "$Path.tmp.$([guid]::NewGuid().ToString('N'))"
    try {
        [IO.File]::WriteAllBytes($Temporary, $Bytes)
        [IO.File]::Move($Temporary, $Path, $true)
    }
    finally {
        if (Test-Path -LiteralPath $Temporary -PathType Leaf) {
            Remove-Item -LiteralPath $Temporary -Force
        }
    }
}

function Write-PipelineTextAtomically {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][AllowEmptyString()][string]$Text
    )

    $Normalized = $Text.Replace("`r`n", "`n").Replace("`r", "`n")
    $Bytes = [Text.UTF8Encoding]::new($false).GetBytes($Normalized)
    Write-PipelineBytesAtomically -Path $Path -Bytes $Bytes
}

function Enter-PipelineMutationLock {
    param(
        [Parameter(Mandatory = $true)][string]$ProjectRoot,
        [Parameter(Mandatory = $true)][string]$Operation
    )

    $Directory = Join-Path $ProjectRoot '.story-locks'
    New-Item -ItemType Directory -Path $Directory -Force | Out-Null
    $Path = Join-Path $Directory 'repository.lock'
    $Id = "$Operation-$([guid]::NewGuid().ToString('N'))"
    try {
        $Stream = [IO.File]::Open(
            $Path,
            [IO.FileMode]::CreateNew,
            [IO.FileAccess]::Write,
            [IO.FileShare]::None
        )
        try {
            $Bytes = [Text.UTF8Encoding]::new($false).GetBytes($Id)
            $Stream.Write($Bytes, 0, $Bytes.Length)
        }
        finally { $Stream.Dispose() }
    }
    catch {
        $Owner = if (Test-Path -LiteralPath $Path -PathType Leaf) {
            Get-Content -LiteralPath $Path -Raw
        }
        else { 'unknown' }
        throw "Another pipeline mutation is active ($Owner)."
    }
    return [pscustomobject]@{ Id = $Id; Path = $Path }
}

function Exit-PipelineMutationLock {
    param([Parameter(Mandatory = $true)][object]$Lock)

    if ((Test-Path -LiteralPath $Lock.Path -PathType Leaf) -and
        (Get-Content -LiteralPath $Lock.Path -Raw) -ceq $Lock.Id) {
        Remove-Item -LiteralPath $Lock.Path -Force
    }
}

function New-PipelineSnapshot {
    param([Parameter(Mandatory = $true)][string[]]$Path)

    return @($Path | ForEach-Object {
        if (-not (Test-Path -LiteralPath $_ -PathType Leaf)) {
            throw "Transaction input is missing: $_"
        }
        $Bytes = [IO.File]::ReadAllBytes($_)
        [pscustomobject]@{
            Path = $_
            Bytes = $Bytes
            Sha256 = Get-PipelineSha256ForBytes $Bytes
        }
    })
}

function Assert-PipelineSnapshotCurrent {
    param(
        [Parameter(Mandatory = $true)][object[]]$Snapshot,
        [Parameter(Mandatory = $true)][string]$Context
    )

    foreach ($Entry in $Snapshot) {
        if (-not (Test-Path -LiteralPath $Entry.Path -PathType Leaf) -or
            (Get-PipelineRawSha256 $Entry.Path) -cne $Entry.Sha256) {
            throw "$Context compare-and-swap failed for $($Entry.Path)."
        }
    }
}

function Restore-PipelineSnapshot {
    param([Parameter(Mandatory = $true)][object[]]$Snapshot)

    foreach ($Entry in $Snapshot) {
        Write-PipelineBytesAtomically -Path $Entry.Path -Bytes $Entry.Bytes
    }
}

function Set-ProductionReadmeValues {
    param(
        [Parameter(Mandatory = $true)][string]$Content,
        [Parameter(Mandatory = $true)][hashtable]$Values,
        [Parameter(Mandatory = $true)][hashtable]$Checklist
    )

    $Updated = $Content.Replace("`r`n", "`n").Replace("`r", "`n")
    foreach ($Pair in $Values.GetEnumerator()) {
        $Pattern = '(?m)^- ' + [regex]::Escape([string]$Pair.Key) + ':.*$'
        $Matches = @([regex]::Matches($Updated, $Pattern))
        if ($Matches.Count -ne 1) {
            throw "Production README must contain exactly one '$($Pair.Key)' field."
        }
        $Updated = [regex]::Replace(
            $Updated,
            $Pattern,
            "- $($Pair.Key): $($Pair.Value)"
        )
    }
    foreach ($Pair in $Checklist.GetEnumerator()) {
        $Pattern = '(?m)^- \[[ xX]\] ' + [regex]::Escape([string]$Pair.Key) + '[ \t]*$'
        $Matches = @([regex]::Matches($Updated, $Pattern))
        if ($Matches.Count -ne 1) {
            throw "Production README must contain exactly one '$($Pair.Key)' checklist item."
        }
        $Mark = if ([bool]$Pair.Value) { 'x' } else { ' ' }
        $Updated = [regex]::Replace(
            $Updated,
            $Pattern,
            "- [$Mark] $($Pair.Key)"
        )
    }
    return $Updated
}

function Set-StoryIndexProjection {
    param(
        [Parameter(Mandatory = $true)][string]$Content,
        [Parameter(Mandatory = $true)][string]$Story,
        [Parameter(Mandatory = $true)][string]$Title,
        [Parameter(Mandatory = $true)][string]$Status,
        [Parameter(Mandatory = $true)][bool]$Canon,
        [Parameter(Mandatory = $true)][string]$Disposition,
        [Parameter(Mandatory = $true)][bool]$Publish,
        [AllowNull()][string]$PromotionDate,
        [Parameter(Mandatory = $true)][string]$Notes
    )

    if ($Title -match '[\r\n|]' -or $Notes -match '[\r\n|]') {
        throw 'Index title and notes must be single-line values without table pipes.'
    }
    $Normalized = $Content.Replace("`r`n", "`n").Replace("`r", "`n")
    $Pattern = '(?m)^\|\s*`' + [regex]::Escape($Story) +
        '`\s*\|[^\n]*\|[ \t]*$'
    $Matches = @([regex]::Matches($Normalized, $Pattern))
    if ($Matches.Count -ne 1) {
        throw "stories/INDEX.md must contain exactly one row for '$Story'."
    }
    $CanonText = if ($Canon) { 'yes' } else { 'no' }
    $PublishText = if ($Publish) { 'yes' } else { 'no' }
    $PromotionText = if ([string]::IsNullOrWhiteSpace($PromotionDate)) {
        '—'
    }
    else { $PromotionDate }
    $Row = "| ``$Story`` | *$Title* | $Status | $CanonText | $Disposition | $PublishText | $PromotionText | $Notes |"
    return [regex]::Replace($Normalized, $Pattern, $Row)
}

function Set-RegistryStoryState {
    param(
        [Parameter(Mandatory = $true)][string]$Content,
        [Parameter(Mandatory = $true)][string]$Story,
        [Parameter(Mandatory = $true)][ValidateSet('in-progress', 'candidate', 'canon', 'abandoned')][string]$State
    )

    [string[]]$Lines = $Content.Replace("`r`n", "`n").Replace("`r", "`n") -split "`n", -1
    $Changed = 0
    for ($Index = 0; $Index -lt $Lines.Count; $Index++) {
        if ($Lines[$Index] -notmatch '^\s*\|.*\|\s*$') { continue }
        $Cells = @($Lines[$Index].Trim().Trim('|').Split('|') | ForEach-Object { $_.Trim() })
        if ($Cells.Count -ne 6 -or $Cells[2] -cne "``$Story``") { continue }
        $Cells[3] = $State
        $Lines[$Index] = '| ' + ($Cells -join ' | ') + ' |'
        $Changed++
    }
    return [pscustomobject]@{
        Content = $Lines -join "`n"
        ChangedRows = $Changed
    }
}
