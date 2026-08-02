#Requires -Version 7.0

[CmdletBinding(SupportsShouldProcess = $true, DefaultParameterSetName = 'Story')]
param(
    [Parameter(Mandatory = $true, ParameterSetName = 'Story')]
    [ValidatePattern('^[a-z0-9]+(?:-[a-z0-9]+)*$')]
    [string]$Story,

    [Parameter(Mandatory = $true, ParameterSetName = 'All')]
    [switch]$All,

    [string]$ProjectRoot
)

$ErrorActionPreference = 'Stop'

function Read-JsonRecord {
    param([Parameter(Mandatory = $true)][string]$Path, [Parameter(Mandatory = $true)][string]$Label)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $null }
    try {
        $Parameters = @{}
        if ((Get-Command ConvertFrom-Json).Parameters.ContainsKey('DateKind')) { $Parameters.DateKind = 'String' }
        return (Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json @Parameters)
    }
    catch { throw "$Label is invalid JSON: $($_.Exception.Message)" }
}

function Get-TerminalRecordAssessment {
    param([Parameter(Mandatory = $true)][string]$StorySlug)
    $Directory = Join-Path $ProjectRoot "stories/$StorySlug"
    if (-not (Test-Path -LiteralPath $Directory -PathType Container)) { throw "Story directory not found: $Directory" }
    $Metadata = Read-JsonRecord (Join-Path $Directory 'story.json') "$StorySlug/story.json"
    if ($null -eq $Metadata -or $Metadata.schemaVersion -ne 1 -or $Metadata.slug -cne $StorySlug -or
        $Metadata.status -notin @('candidate', 'final') -or $Metadata.stage -cne $Metadata.status) {
        throw "'$StorySlug' is not an exact terminal candidate/final record."
    }

    $Release = Read-JsonRecord (Join-Path $Directory 'release.json') "$StorySlug/release.json"
    $Handoffs = Read-JsonRecord (Join-Path $Directory 'handoffs.json') "$StorySlug/handoffs.json"
    $Authority = Read-JsonRecord (Join-Path $Directory 'authority.json') "$StorySlug/authority.json"
    $Promotion = Read-JsonRecord (Join-Path $Directory 'promotion.json') "$StorySlug/promotion.json"
    $StructuralCurrent = $null -ne $Release -and $Release.schemaVersion -eq 2 -and
        $Release.certified -eq $true -and $Release.storySlug -ceq $StorySlug -and
        $null -ne $Handoffs -and $Handoffs.schemaVersion -eq 2 -and
        $Handoffs.storySlug -ceq $StorySlug -and
        $null -ne $Authority -and $Authority.schemaVersion -eq 1 -and
        $Authority.storySlug -ceq $StorySlug -and
        $null -ne $Promotion -and $Promotion.schemaVersion -eq 1
    $SyntheticActors = if ($null -eq $Handoffs) { @() } else {
        @($Handoffs.entries | Where-Object {
            $_.actor -ceq 'pipeline_migration' -or $_.persister -ceq 'pipeline_migration'
        })
    }
    if ($Metadata.status -ceq 'final' -and
        ($null -eq $Promotion -or $Promotion.state -cne 'completed')) {
        $StructuralCurrent = $false
    }
    if ($Metadata.status -ceq 'candidate' -and $null -ne $Promotion -and
        $Promotion.state -notin @('not-prepared', 'ready')) {
        $StructuralCurrent = $false
    }
    if ($SyntheticActors.Count -gt 0) { $StructuralCurrent = $false }

    $Requirements = @(
        'regenerate and verify authority.json against current reconciled authority',
        'repeat live canon research in a guarded canon_librarian handoff',
        'repeat each dependent plan/draft/final handoff under the schema-v2 guard',
        'obtain fresh independent draft and final continuity_critic review payloads',
        'run the strict story-name gate and issue a new schema-v2 release'
    )
    if ($Metadata.status -ceq 'final') {
        $Requirements += 're-establish genuine user authorization, canon_steward evidence, and completed promotion provenance'
    }
    return [pscustomobject][ordered]@{
        story = $StorySlug
        status = [string]$Metadata.status
        structurallyCurrent = $StructuralCurrent
        syntheticMigrationReceipts = $SyntheticActors.Count
        requirements = $Requirements
    }
}

if ([string]::IsNullOrWhiteSpace($ProjectRoot)) {
    $ProjectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../../../..')).Path
}
else { $ProjectRoot = (Resolve-Path -LiteralPath $ProjectRoot).Path }

$Targets = if ($All) {
    @(Get-ChildItem -LiteralPath (Join-Path $ProjectRoot 'stories') -Directory |
        Where-Object Name -notmatch '^[_.]' | Sort-Object Name | ForEach-Object {
            $Metadata = Read-JsonRecord (Join-Path $_.FullName 'story.json') "$($_.Name)/story.json"
            if ($null -ne $Metadata -and $Metadata.status -in @('candidate', 'final') -and
                $Metadata.stage -ceq $Metadata.status) { $_.Name }
        })
}
else { @($Story) }
if ($Targets.Count -eq 0) { throw 'No candidate or final terminal story records were found to assess.' }

$IntegrityScript = Join-Path $ProjectRoot '.agents/skills/story-integrity/scripts/Test-StoryIntegrity.ps1'
foreach ($Target in $Targets) {
    $Assessment = Get-TerminalRecordAssessment $Target
    if ($Assessment.structurallyCurrent) {
        if (-not (Test-Path -LiteralPath $IntegrityScript -PathType Leaf)) {
            throw "Integrity validator is missing; '$Target' cannot be declared current."
        }
        $Pwsh = (Get-Command pwsh -ErrorAction Stop).Source
        $ReceiptText = & $Pwsh -NoLogo -NoProfile -NonInteractive -File $IntegrityScript `
            -Story $Target -OutputFormat Json -ProjectRoot $ProjectRoot
        $IntegrityExitCode = $LASTEXITCODE
        try { $Receipt = $ReceiptText | ConvertFrom-Json }
        catch { throw "Integrity validator returned invalid JSON for '$Target'." }
        if ($IntegrityExitCode -eq 0 -and $Receipt.passed -eq $true -and
            $Receipt.story -ceq $Target -and $Receipt.checkedStories -eq 1) {
            ([pscustomobject][ordered]@{
                story = $Target
                result = 'ALREADY_CURRENT'
                changed = $false
                requirements = @()
            } | ConvertTo-Json -Depth 5 -Compress)
            continue
        }
    }

    $Result = [pscustomobject][ordered]@{
        story = $Target
        result = 'REVALIDATION_REQUIRED'
        changed = $false
        requirements = @($Assessment.requirements)
    }
    if ($WhatIfPreference) {
        $Result | ConvertTo-Json -Depth 5 -Compress
        continue
    }
    throw (
        "Pipeline v2 migration refused for '$Target': terminal evidence cannot be synthesized or relabeled. " +
        "No files were changed. Required live work: $($Assessment.requirements -join '; ')."
    )
}
