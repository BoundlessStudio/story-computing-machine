#Requires -Version 7.0

[CmdletBinding()]
param(
    [ValidateSet('Text', 'Json')]
    [string]$OutputFormat = 'Text',

    [string]$ProjectRoot
)

$ErrorActionPreference = 'Stop'
$Errors = [Collections.Generic.List[string]]::new()
. (Join-Path $PSScriptRoot 'ReviewContracts.ps1')

function Add-ContractError {
    param([Parameter(Mandatory = $true)][string]$Message)
    $Errors.Add($Message)
}

function Test-ExactSet {
    param(
        [Parameter(Mandatory = $true)][string[]]$Actual,
        [Parameter(Mandatory = $true)][string[]]$Expected,
        [Parameter(Mandatory = $true)][string]$Context
    )
    $Missing = @($Expected | Where-Object { $_ -cnotin $Actual })
    $Extra = @($Actual | Where-Object { $_ -cnotin $Expected })
    if ($Missing.Count -gt 0 -or $Extra.Count -gt 0) {
        Add-ContractError "$Context mismatch; missing=[$($Missing -join ', ')], extra=[$($Extra -join ', ')]."
    }
}

if ([string]::IsNullOrWhiteSpace($ProjectRoot)) {
    $ProjectRoot = (Resolve-Path -LiteralPath (
        Join-Path $PSScriptRoot '../../../..'
    )).Path
}
else { $ProjectRoot = (Resolve-Path -LiteralPath $ProjectRoot).Path }

$ContractPath = Join-Path $ProjectRoot 'schemas/pipeline-contract.json'
$SchemaPath = Join-Path $ProjectRoot 'schemas/pipeline-contract.schema.json'
foreach ($Path in @($ContractPath, $SchemaPath)) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Pipeline contract file not found: $Path"
    }
}
$ContractJson = Get-Content -LiteralPath $ContractPath -Raw
$SchemaFailures = @()
if (-not (Test-Json -Json $ContractJson -SchemaFile $SchemaPath `
    -ErrorVariable +SchemaFailures -ErrorAction SilentlyContinue)) {
    Add-ContractError 'schemas/pipeline-contract.json fails pipeline-contract.schema.json.'
}
try {
    $Parameters = @{}
    if ((Get-Command ConvertFrom-Json).Parameters.ContainsKey('DateKind')) {
        $Parameters.DateKind = 'String'
    }
    $Contract = $ContractJson | ConvertFrom-Json @Parameters
}
catch { throw "Pipeline contract is invalid JSON: $($_.Exception.Message)" }

$Statuses = @($Contract.story.statuses)
$LifecycleStatuses = @($Contract.lifecycle.states.PSObject.Properties.Name)
Test-ExactSet -Actual $LifecycleStatuses -Expected $Statuses `
    -Context 'lifecycle state keys versus story statuses'
foreach ($Status in $LifecycleStatuses) {
    $State = $Contract.lifecycle.states.$Status
    foreach ($Stage in @($State.stages)) {
        if ($Stage -cnotin @($Contract.story.stages)) {
            Add-ContractError "Lifecycle '$Status' references unknown stage '$Stage'."
        }
    }
    foreach ($Disposition in @($State.userDispositions)) {
        if ($Disposition -cnotin @($Contract.story.userDispositions)) {
            Add-ContractError "Lifecycle '$Status' references unknown user disposition '$Disposition'."
        }
    }
}
foreach ($Status in @($Contract.lifecycle.publishableStatuses)) {
    if ($Status -cnotin $Statuses -or $true -cnotin @($Contract.lifecycle.states.$Status.publish)) {
        Add-ContractError "Publishable status '$Status' is absent or cannot publish."
    }
}
foreach ($Status in $LifecycleStatuses) {
    if ($true -cin @($Contract.lifecycle.states.$Status.publish) -and
        $Status -cnotin @($Contract.lifecycle.publishableStatuses)) {
        Add-ContractError "Lifecycle '$Status' permits publication but is not publishable."
    }
}

$PromotionSchema = Join-Path $ProjectRoot ([string]$Contract.promotion.schemaPath)
if (-not (Test-Path -LiteralPath $PromotionSchema -PathType Leaf)) {
    Add-ContractError "Promotion schema path is missing: $($Contract.promotion.schemaPath)"
}
if ($Contract.release.schemaVersion -ne 2) {
    Add-ContractError 'The active release contract must be schema version 2.'
}
if ($Contract.handoffLedger.schemaVersion -ne 2) {
    Add-ContractError 'The active handoff-ledger contract must be schema version 2.'
}
$DeclaredReviewFields = @($Contract.reviewPass.fields)
$ParserReviewFields = @($script:ReviewPayloadFieldOrder)
if ($DeclaredReviewFields.Count -ne $ParserReviewFields.Count) {
    Add-ContractError "The review payload contract has $($DeclaredReviewFields.Count) fields but the parser requires $($ParserReviewFields.Count)."
}
else {
    for ($Index = 0; $Index -lt $ParserReviewFields.Count; $Index++) {
        if ($DeclaredReviewFields[$Index] -cne $ParserReviewFields[$Index]) {
            Add-ContractError (
                "Review payload field $($Index + 1) must be '$($ParserReviewFields[$Index])'; " +
                "the central contract declares '$($DeclaredReviewFields[$Index])'."
            )
        }
    }
}
$ModeNames = @($Contract.handoffLedger.modeContracts.PSObject.Properties.Name)
$FamilyModes = @($Contract.handoffLedger.releaseFamilies | ForEach-Object { @($_) })
foreach ($Mode in $ModeNames) {
    $ModeContract = $Contract.handoffLedger.modeContracts.$Mode
    if ($ModeContract.persister -cnotin @('coordinator', [string]$ModeContract.actor)) {
        Add-ContractError "Handoff mode '$Mode' has unsupported persister '$($ModeContract.persister)'."
    }
    foreach ($Status in @($ModeContract.statuses)) {
        if ($Status -cnotin @($Contract.handoffLedger.statuses)) {
            Add-ContractError "Handoff mode '$Mode' references unknown status '$Status'."
        }
    }
    foreach ($Stage in @($ModeContract.allowedStages)) {
        if ($Stage -cnotin @($Contract.lifecycle.states.'in-progress'.stages)) {
            Add-ContractError "Handoff mode '$Mode' references non-working stage '$Stage'."
        }
    }
    if ('stories/{story}/story.json' -cnotin @($ModeContract.requiredInputs) -or
        'stories/{story}/handoffs.json' -cnotin @($ModeContract.requiredInputs)) {
        Add-ContractError "Handoff mode '$Mode' must bind story.json and handoffs.json."
    }
    if ($Mode -cnotin $FamilyModes) {
        Add-ContractError "Handoff mode '$Mode' is absent from the release families."
    }
}
foreach ($Mode in $FamilyModes) {
    if ($Mode -cnotin $ModeNames) {
        Add-ContractError "Release family references unknown handoff mode '$Mode'."
    }
}
if (@($FamilyModes | Group-Object | Where-Object Count -ne 1).Count -gt 0) {
    Add-ContractError 'Every handoff mode must occur in exactly one release family.'
}

foreach ($TemplateSpec in @(
    [pscustomobject]@{ Name = 'story.json'; Contract = @($Contract.story.fields) },
    [pscustomobject]@{ Name = 'release.json'; Contract = @($Contract.release.fields) },
    [pscustomobject]@{ Name = 'handoffs.json'; Contract = @($Contract.handoffLedger.fields) }
)) {
    $TemplatePath = Join-Path $ProjectRoot "stories/_template/$($TemplateSpec.Name)"
    if (-not (Test-Path -LiteralPath $TemplatePath -PathType Leaf)) {
        Add-ContractError "Required template is missing: stories/_template/$($TemplateSpec.Name)"
        continue
    }
    try {
        $TemplateJson = (Get-Content -LiteralPath $TemplatePath -Raw).
            Replace('{{slug}}', 'contract-fixture').
            Replace('{{title_yaml}}', '"Contract fixture"').
            Replace('{{title}}', 'Contract fixture').
            Replace('{{date}}', '2000-01-01')
        $Template = $TemplateJson | ConvertFrom-Json
    }
    catch {
        Add-ContractError "Template $($TemplateSpec.Name) is invalid JSON."
        continue
    }
    Test-ExactSet -Actual @($Template.PSObject.Properties.Name) `
        -Expected @($TemplateSpec.Contract) -Context "template $($TemplateSpec.Name) fields"
    if ($TemplateSpec.Name -ceq 'story.json' -and
        $Template.schemaVersion -ne $Contract.story.schemaVersion) {
        Add-ContractError 'Template story.json schemaVersion is stale.'
    }
    if ($TemplateSpec.Name -ceq 'release.json') {
        if ($Template.schemaVersion -ne $Contract.release.schemaVersion) {
            Add-ContractError 'Template release.json schemaVersion is stale.'
        }
        Test-ExactSet -Actual @($Template.artifacts.PSObject.Properties.Name) `
            -Expected @($Contract.release.artifactContainerFields) `
            -Context 'template release.json artifact containers'
        foreach ($ArtifactName in @($Contract.release.artifactContainerFields)) {
            Test-ExactSet -Actual @($Template.artifacts.$ArtifactName.PSObject.Properties.Name) `
                -Expected @($Contract.release.artifactFields) `
                -Context "template release.json artifacts.$ArtifactName fields"
        }
        Test-ExactSet -Actual @($Template.review.PSObject.Properties.Name) `
            -Expected @($Contract.release.reviewFields) `
            -Context 'template release.json review fields'
        Test-ExactSet -Actual @($Template.nameCheck.PSObject.Properties.Name) `
            -Expected @($Contract.release.nameCheckFields) `
            -Context 'template release.json name-check fields'
        Test-ExactSet -Actual @($Template.provenance.PSObject.Properties.Name) `
            -Expected @($Contract.release.provenanceFields) `
            -Context 'template release.json provenance fields'
    }
    if ($TemplateSpec.Name -ceq 'handoffs.json' -and
        ($Template.schemaVersion -ne $Contract.handoffLedger.schemaVersion -or
        $null -ne $Template.chainHead -or @($Template.entries).Count -ne 0)) {
        Add-ContractError 'Template handoffs.json is not the current empty-ledger contract.'
    }
}
$PromotionTemplatePath = Join-Path $ProjectRoot 'stories/_template/promotion.json'
if (Test-Path -LiteralPath $PromotionTemplatePath -PathType Leaf) {
    $PromotionTemplateJson = Get-Content -LiteralPath $PromotionTemplatePath -Raw
    $PromotionSchemaErrors = @()
    if (-not (Test-Json -Json $PromotionTemplateJson.Replace('{{slug}}', 'contract-fixture') `
        -SchemaFile $PromotionSchema -ErrorVariable +PromotionSchemaErrors `
        -ErrorAction SilentlyContinue)) {
        Add-ContractError 'Template promotion.json fails the normative promotion schema.'
    }
}
else { Add-ContractError 'Required template is missing: stories/_template/promotion.json' }

$UniqueErrors = @($Errors | Sort-Object -Unique)
$Result = [ordered]@{
    schemaVersion = 1
    passed = $UniqueErrors.Count -eq 0
    errors = $UniqueErrors
}
if ($OutputFormat -eq 'Json') { $Result | ConvertTo-Json -Depth 5 }
elseif ($UniqueErrors.Count -eq 0) { 'Pipeline contract validation passed.' }
else { foreach ($Message in $UniqueErrors) { Write-Host "- $Message" -ForegroundColor Red } }
if ($UniqueErrors.Count -gt 0) { exit 1 }
