[CmdletBinding()]
param(
    [ValidatePattern('^[a-z0-9]+(?:-[a-z0-9]+)*$')]
    [string]$Story,

    [switch]$Strict
)

$ErrorActionPreference = 'Stop'

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$RegistryPath = Join-Path $ProjectRoot 'stories/NAMES.md'

if (-not (Test-Path -LiteralPath $RegistryPath -PathType Leaf)) {
    throw "Name registry not found: $RegistryPath"
}

$Lines = Get-Content -LiteralPath $RegistryPath
$Start = [Array]::IndexOf($Lines, '<!-- registry:start -->')
$End = [Array]::IndexOf($Lines, '<!-- registry:end -->')

if ($Start -lt 0 -or $End -le $Start) {
    throw 'Name registry markers are missing or out of order.'
}

$Rows = foreach ($Line in $Lines[($Start + 1)..($End - 1)]) {
    if ($Line -notmatch '^\|') {
        continue
    }

    $Cells = $Line.Trim().Trim('|').Split('|') | ForEach-Object { $_.Trim() }
    if ($Cells.Count -ne 6 -or $Cells[0] -eq 'Character / entity' -or
        $Cells[0] -match '^-+$') {
        continue
    }

    $Forms = ($Cells[1] -replace '`', '').Split(';') |
        ForEach-Object { $_.Trim() } |
        Where-Object { -not [string]::IsNullOrWhiteSpace($_) }

    if ($Forms.Count -eq 0) {
        throw "Registry row has no reserved forms: $Line"
    }

    [pscustomobject]@{
        Character = $Cells[0] -replace '`', ''
        Forms = $Forms
        Source = $Cells[2] -replace '`', ''
        State = $Cells[3]
        ReuseStatus = $Cells[4].ToLowerInvariant()
        Rationale = $Cells[5]
    }
}

if ($Rows.Count -eq 0) {
    throw 'Name registry contains no data rows.'
}

$AllowedStatuses = @('unique', 'deliberate', 'unresolved')
$InvalidStatuses = $Rows | Where-Object { $_.ReuseStatus -notin $AllowedStatuses }
if ($InvalidStatuses) {
    $Names = ($InvalidStatuses | ForEach-Object Character) -join ', '
    throw "Invalid reuse status for: $Names"
}

$FormUses = foreach ($Row in $Rows) {
    foreach ($Form in $Row.Forms) {
        [pscustomobject]@{
            Normalized = $Form.ToLowerInvariant()
            Form = $Form
            Character = $Row.Character
            Source = $Row.Source
            ReuseStatus = $Row.ReuseStatus
            Rationale = $Row.Rationale
        }
    }
}

$Failures = [System.Collections.Generic.List[string]]::new()
$Warnings = [System.Collections.Generic.List[string]]::new()

foreach ($Group in ($FormUses | Group-Object Normalized)) {
    $Uses = @($Group.Group)
    $DistinctIdentities = @($Uses.Character | Sort-Object -Unique)
    if ($DistinctIdentities.Count -lt 2) {
        continue
    }

    $MeaningfulReuse = $Uses | Where-Object {
        $_.ReuseStatus -eq 'deliberate' -and
        $_.Rationale -notin @('', '—', '-')
    }
    $Allowed = $MeaningfulReuse.Count -eq $Uses.Count
    if ($Allowed) {
        continue
    }

    $Description = "'$($Uses[0].Form)' => " +
        (($Uses | ForEach-Object { "$($_.Character) [$($_.Source)]" }) -join '; ')
    $TouchesStory = -not [string]::IsNullOrWhiteSpace($Story) -and
        ($Uses | Where-Object { $_.Source -like "$Story*" })

    if ($Strict -or $TouchesStory) {
        $Failures.Add($Description)
    }
    else {
        $Warnings.Add($Description)
    }
}

if (-not [string]::IsNullOrWhiteSpace($Story)) {
    $StoryDirectory = Join-Path $ProjectRoot "stories/$Story"
    $DeltaPath = Join-Path $StoryDirectory '06-canon-delta.md'

    if (-not (Test-Path -LiteralPath $StoryDirectory -PathType Container)) {
        throw "Story directory not found: $StoryDirectory"
    }

    if (Test-Path -LiteralPath $DeltaPath -PathType Leaf) {
        $Delta = Get-Content -LiteralPath $DeltaPath -Raw
        $CharacterSection = [regex]::Match(
            $Delta,
            '(?ms)^## New characters or character facts\s*(.*?)(?=^## )'
        )

        if ($CharacterSection.Success) {
            $DeclaredNames = [regex]::Matches(
                $CharacterSection.Groups[1].Value,
                '(?m)^- \*\*(.+?)(?: \(proposed\))?:\*\*'
            ) | ForEach-Object { $_.Groups[1].Value.Trim() }

            $StoryRows = @($Rows | Where-Object { $_.Source -like "$Story*" })
            foreach ($Name in $DeclaredNames) {
                if ($StoryRows.Character -notcontains $Name) {
                    $Failures.Add(
                        "Final delta name '$Name' is not registered for '$Story'."
                    )
                }
            }
        }
    }
}

foreach ($Warning in $Warnings) {
    Write-Warning "Unresolved registry collision: $Warning"
}

if ($Failures.Count -gt 0) {
    $Message = "Name registry check failed:`n- " + ($Failures -join "`n- ")
    throw $Message
}

$Scope = if ([string]::IsNullOrWhiteSpace($Story)) {
    'global registry'
}
else {
    "story '$Story'"
}

$Summary = "Name registry check passed for {0}: {1} entries, {2} reserved " +
    "forms, {3} global warning(s)."
Write-Output ($Summary -f $Scope, $Rows.Count, $FormUses.Count, $Warnings.Count)
