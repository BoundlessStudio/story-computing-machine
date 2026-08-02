#Requires -Version 7.0

[CmdletBinding()]
param(
    [string]$ProjectRoot
)

$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrWhiteSpace($ProjectRoot)) {
    $ProjectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
}
else {
    $ProjectRoot = [IO.Path]::GetFullPath($ProjectRoot)
}

$Failures = [Collections.Generic.List[string]]::new()

function Read-ContractFile {
    param([Parameter(Mandatory = $true)][string]$RelativePath)

    $Path = Join-Path $ProjectRoot $RelativePath
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        $Failures.Add("Missing contract file: $RelativePath")
        return ''
    }
    return Get-Content -LiteralPath $Path -Raw
}

function Assert-ContractToken {
    param(
        [Parameter(Mandatory = $true)][string]$RelativePath,
        [Parameter(Mandatory = $true)][string]$Content,
        [Parameter(Mandatory = $true)][string]$Token
    )

    if (-not $Content.Contains($Token, [StringComparison]::Ordinal)) {
        $Failures.Add("$RelativePath lacks required token: $Token")
    }
}

function Assert-ContractRegex {
    param(
        [Parameter(Mandatory = $true)][string]$RelativePath,
        [Parameter(Mandatory = $true)][string]$Content,
        [Parameter(Mandatory = $true)][string]$Pattern,
        [Parameter(Mandatory = $true)][string]$Description
    )

    if ($Content -cnotmatch $Pattern) {
        $Failures.Add("$RelativePath violates $Description")
    }
}

$Roles = @(
    [ordered]@{
        file = '.codex/agents/canon-librarian.toml'
        skill = '.agents/skills/canon-research/SKILL.md'
        name = 'canon_librarian'
        sandbox = 'read-only'
        modes = @('RESEARCH_CANON')
        owners = @('coordinator', 'user')
        nameStatus = $false
    },
    [ordered]@{
        file = '.codex/agents/continuity-critic.toml'
        skill = '.agents/skills/continuity-review/SKILL.md'
        name = 'continuity_critic'
        sandbox = 'read-only'
        modes = @('REVIEW_DRAFT', 'REVIEW_FINAL')
        owners = @('coordinator', 'canon_librarian', 'story_architect', 'prose_writer', 'story_editor', 'user')
        nameStatus = $false
    },
    [ordered]@{
        file = '.codex/agents/prose-writer.toml'
        skill = '.agents/skills/prose-drafting/SKILL.md'
        name = 'prose_writer'
        sandbox = 'workspace-write'
        modes = @('CREATE_DRAFT', 'REVISE_DRAFT')
        owners = @('coordinator', 'prose_writer', 'user')
        nameStatus = $true
    },
    [ordered]@{
        file = '.codex/agents/story-architect.toml'
        skill = '.agents/skills/story-architecture/SKILL.md'
        name = 'story_architect'
        sandbox = 'workspace-write'
        modes = @('CREATE_PLAN', 'REVISE_PLAN')
        owners = @('coordinator', 'story_architect', 'user')
        nameStatus = $true
    },
    [ordered]@{
        file = '.codex/agents/story-editor.toml'
        skill = '.agents/skills/final-edit/SKILL.md'
        name = 'story_editor'
        sandbox = 'workspace-write'
        modes = @('CREATE_FINAL', 'REVISE_FINAL')
        owners = @('coordinator', 'story_editor', 'user')
        nameStatus = $true
    }
)

$RequiredStatuses = @('READY', 'HANDOFF_ERROR', 'USER_RULING_REQUIRED')
$AllOwnedContracts = [Collections.Generic.List[object]]::new()

foreach ($Role in $Roles) {
    $Agent = Read-ContractFile $Role.file
    $Skill = Read-ContractFile $Role.skill
    $AllOwnedContracts.Add([pscustomobject]@{ Path = $Role.file; Content = $Agent })
    $AllOwnedContracts.Add([pscustomobject]@{ Path = $Role.skill; Content = $Skill })

    Assert-ContractRegex $Role.file $Agent `
        "(?m)^name = `"$([regex]::Escape($Role.name))`"\r?$" 'role-name parity'
    Assert-ContractRegex $Role.file $Agent `
        "(?m)^sandbox_mode = `"$([regex]::Escape($Role.sandbox))`"\r?$" 'sandbox intent'

    foreach ($Mode in $Role.modes) {
        Assert-ContractToken $Role.file $Agent $Mode
        Assert-ContractToken $Role.skill $Skill $Mode
    }
    foreach ($Status in $RequiredStatuses) {
        Assert-ContractToken $Role.file $Agent $Status
        Assert-ContractToken $Role.skill $Skill $Status
    }
    if ($Role.nameStatus) {
        Assert-ContractToken $Role.file $Agent 'NAME_REGISTRATION_REQUIRED'
        Assert-ContractToken $Role.skill $Skill 'NAME_REGISTRATION_REQUIRED'
    }

    $ExpectedStatuses = @($RequiredStatuses)
    if ($Role.nameStatus) { $ExpectedStatuses += 'NAME_REGISTRATION_REQUIRED' }
    $AgentStatusLine = 'status: ' + ($ExpectedStatuses -join ' | ')
    $SkillStatusLine = 'status: <' + ($ExpectedStatuses -join '|') + '>'
    Assert-ContractToken $Role.file $Agent $AgentStatusLine
    Assert-ContractToken $Role.skill $Skill $SkillStatusLine

    $AgentModeLine = 'mode: ' + ($Role.modes -join ' | ')
    $SkillModeLine = if ($Role.modes.Count -eq 1) {
        'mode: ' + $Role.modes[0]
    }
    else {
        'mode: <' + ($Role.modes -join '|') + '>'
    }
    Assert-ContractToken $Role.file $Agent $AgentModeLine
    Assert-ContractToken $Role.skill $Skill $SkillModeLine

    $AgentOwnerLine = 'resolutionOwner: ' + ($Role.owners -join ' | ')
    $SkillOwnerLine = 'resolutionOwner: <' + ($Role.owners -join '|') + '>'
    Assert-ContractToken $Role.file $Agent $AgentOwnerLine
    Assert-ContractToken $Role.skill $Skill $SkillOwnerLine
    Assert-ContractToken $Role.file $Agent '-ReportText'
    Assert-ContractToken $Role.skill $Skill '-ReportText'
    Assert-ContractToken $Role.file $Agent 'reportSha256'
    Assert-ContractToken $Role.skill $Skill 'reportSha256'
}

$PromotionRole = [ordered]@{
    file = '.codex/agents/canon-steward.toml'
    skill = '.agents/skills/canon-maintenance/SKILL.md'
    name = 'canon_steward'
    sandbox = 'workspace-write'
}
$PromotionAgent = Read-ContractFile $PromotionRole.file
$PromotionSkill = Read-ContractFile $PromotionRole.skill
$AllOwnedContracts.Add([pscustomobject]@{ Path = $PromotionRole.file; Content = $PromotionAgent })
$AllOwnedContracts.Add([pscustomobject]@{ Path = $PromotionRole.skill; Content = $PromotionSkill })
Assert-ContractRegex $PromotionRole.file $PromotionAgent `
    "(?m)^name = `"$([regex]::Escape($PromotionRole.name))`"\r?$" 'promotion role-name parity'
Assert-ContractRegex $PromotionRole.file $PromotionAgent `
    "(?m)^sandbox_mode = `"$([regex]::Escape($PromotionRole.sandbox))`"\r?$" 'promotion sandbox intent'

$StoryRoomPath = '.agents/skills/story-room/SKILL.md'
$StoryRoom = Read-ContractFile $StoryRoomPath
$AllOwnedContracts.Add([pscustomobject]@{ Path = $StoryRoomPath; Content = $StoryRoom })
foreach ($Mode in @(
    'RESEARCH_CANON', 'CREATE_PLAN', 'REVISE_PLAN', 'CREATE_DRAFT',
    'REVISE_DRAFT', 'REVIEW_DRAFT', 'CREATE_FINAL', 'REVISE_FINAL',
    'REVIEW_FINAL'
)) {
    Assert-ContractToken $StoryRoomPath $StoryRoom $Mode
}
foreach ($Status in @($RequiredStatuses + 'NAME_REGISTRATION_REQUIRED')) {
    Assert-ContractToken $StoryRoomPath $StoryRoom $Status
}
foreach ($RoleName in @(
    'canon_librarian', 'story_architect', 'prose_writer',
    'continuity_critic', 'story_editor', 'canon_steward'
)) {
    Assert-ContractToken $StoryRoomPath $StoryRoom $RoleName
}

$RequiredByPath = [ordered]@{
    '.codex/agents/canon-librarian.toml' = @(
        'PERSISTENCE_HANDOFF', 'authorityManifestSha256',
        'handoffLedgerSha256', 'handoffLedgerChainHead',
        'stories/<slug>/authority.json', 'verificationStatus', 'verified',
        'descriptive-only', 'accessRequirements',
        'authority: <LOCKED|CANON|evidence-none>'
    )
    '.agents/skills/canon-research/SKILL.md' = @(
        'PERSISTENCE_HANDOFF', 'authorityManifestSha256',
        'handoffLedgerSha256', 'handoffLedgerChainHead',
        'stories/<slug>/authority.json', 'verificationStatus', 'verified',
        'descriptive-only', 'accessRequirements',
        'authority: <LOCKED|CANON|evidence-none>'
    )
    '.codex/agents/story-architect.toml' = @(
        'beforePlanSha256', 'planScaffoldSha256', 'nameProposals',
        'REGISTER_NAMES_AND_REVISE_PLAN', 'invalidatesDownstream'
    )
    '.agents/skills/story-architecture/SKILL.md' = @(
        'beforePlanSha256', 'planScaffoldSha256', 'nameProposals',
        'REGISTER_NAMES_AND_REVISE_PLAN', 'invalidatesDownstream'
    )
    '.codex/agents/prose-writer.toml' = @(
        'beforeDraftSha256', 'draftScaffoldSha256', 'nameProposals',
        'handoffLedgerSha256', 'invalidatesDownstream'
    )
    '.agents/skills/prose-drafting/SKILL.md' = @(
        'beforeDraftSha256', 'draftScaffoldSha256', 'nameProposals',
        'handoffLedgerSha256', 'invalidatesDownstream'
    )
    '.codex/agents/story-editor.toml' = @(
        'inputPlanSha256', 'inputDraftSha256', 'inputScopedRegistrySha256',
        'beforeStorySha256', 'beforeCanonDeltaSha256',
        'storyScaffoldSha256', 'canonDeltaScaffoldSha256',
        'requiresRegistryReconciliationBeforeReview', 'nameProposals',
        'Reviewed prose name-audit allowlist', 'proseNameAuditAllowlist',
        'reopens it to', 'final-review'
    )
    '.agents/skills/final-edit/SKILL.md' = @(
        'inputPlanSha256', 'inputDraftSha256', 'inputScopedRegistrySha256',
        'beforeStorySha256', 'beforeCanonDeltaSha256',
        'storyScaffoldSha256', 'canonDeltaScaffoldSha256',
        'requiresRegistryReconciliationBeforeReview', 'nameProposals',
        'Reviewed prose name-audit allowlist', 'proseNameAuditAllowlist',
        'Final name validation', 'REVIEW_FINAL', 'reopens it to', 'final-review'
    )
    '.codex/agents/continuity-critic.toml' = @(
        'authorityManifestSha256', 'handoffLedgerSha256',
        'canon_librarian', 'story_architect', 'prose_writer', 'story_editor',
        'UNRECONCILED_REGISTRY', 'reviewer: continuity_critic',
        'pre-review', 'previousEntrySha256',
        'Reviewed prose name-audit allowlist'
    )
    '.agents/skills/continuity-review/SKILL.md' = @(
        'authorityManifestSha256', 'handoffLedgerSha256',
        'canon_librarian', 'story_architect', 'prose_writer', 'story_editor',
        'UNRECONCILED_REGISTRY', 'reviewer: continuity_critic',
        'pre-review', 'previousEntrySha256',
        'Reviewed prose name-audit allowlist'
    )
    '.codex/agents/canon-steward.toml' = @(
        'user explicitly authorized', 'one named story', 'STEWARDSHIP_HANDOFF',
        'candidateReleaseSha256', 'authorityManifestSha256',
        'deltaDispositionsSha256', 'No story artifact',
        'do not write the promotion manifest', 'roll the entire transaction back'
    )
    '.agents/skills/canon-maintenance/SKILL.md' = @(
        'explicit user approval', 'one controlled, named-story transaction',
        'STEWARDSHIP_HANDOFF', 'candidateReleaseSha256',
        'authorityManifestSha256', 'deltaDispositionsSha256',
        'canon_steward', 'may write only affected `universe/*.md`',
        'The primary alone writes `promotion.json`', 'Never manufacture a handoff',
        'restores every'
    )
    '.agents/skills/story-room/SKILL.md' = @(
        'New-StoryHandoffGuard.ps1', 'Complete-StoryHandoffGuard.ps1',
        'stories/<slug>/handoffs.json', 'chainHead', 'New-AuthorityManifest.ps1',
        'Complete-StoryCandidate.ps1', 'Test-StoryHandoffs.ps1',
        '-ReportText', 'reportSha256',
        'guardSha256', '-RecoverCommittedGuard', '`persister`',
        'independent `continuity_critic`', 'independent `canon_steward`',
        'Pre-review registry reconciliation', 'Downstream invalidation map',
        'pre-review snapshot', 'previousEntrySha256',
        'atomic reopen transaction', 'userDisposition: pending'
    )
}

foreach ($Pair in $RequiredByPath.GetEnumerator()) {
    $Content = Read-ContractFile $Pair.Key
    foreach ($Token in $Pair.Value) {
        Assert-ContractToken $Pair.Key $Content $Token
    }
}

foreach ($Contract in $AllOwnedContracts) {
    foreach ($Forbidden in @(
        'COORDINATOR_REPAIR_REQUIRED',
        'explicit primary fallback identifier',
        'reviewer: <continuity_critic|'
    )) {
        if ($Contract.Content.Contains($Forbidden, [StringComparison]::Ordinal)) {
            $Failures.Add("$($Contract.Path) contains retired contract token: $Forbidden")
        }
    }
}

if ($Failures.Count -gt 0) {
    throw "Agent contract parity failed:`n - $($Failures -join "`n - ")"
}

"Agent contract parity passed for $($Roles.Count + 1) roles and $($AllOwnedContracts.Count) contract files."
