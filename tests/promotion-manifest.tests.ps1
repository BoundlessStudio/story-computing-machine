#Requires -Version 7.0

[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$RepoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$PromotionScript = Join-Path $RepoRoot '.agents/skills/canon-maintenance/scripts/Complete-CanonPromotion.ps1'
$Pwsh = (Get-Command pwsh -ErrorAction Stop).Source
$TestRoot = Join-Path ([IO.Path]::GetTempPath()) (
    'story-promotion-manifest-tests-' + [guid]::NewGuid().ToString('N')
)
$script:Passed = 0
$script:Failed = 0
$Utf8NoBom = [Text.UTF8Encoding]::new($false)
. (Join-Path $RepoRoot '.agents/skills/story-integrity/scripts/PromotionContracts.ps1')

function Write-FixtureFile {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][AllowEmptyString()][string]$Content
    )

    $Directory = Split-Path -Parent $Path
    if (-not (Test-Path -LiteralPath $Directory -PathType Container)) {
        $null = New-Item -ItemType Directory -Path $Directory -Force
    }
    [IO.File]::WriteAllText($Path, $Content.Replace("`r`n", "`n").Replace("`r", "`n"), $Utf8NoBom)
}

function Get-Sha256Bytes {
    param([Parameter(Mandatory = $true)][byte[]]$Bytes)

    return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($Bytes)).ToLowerInvariant()
}

function Get-Sha256File {
    param([Parameter(Mandatory = $true)][string]$Path)

    return Get-Sha256Bytes ([IO.File]::ReadAllBytes($Path))
}

function Get-Sha256Text {
    param([Parameter(Mandatory = $true)][AllowEmptyString()][string]$Text)

    return Get-Sha256Bytes ($Utf8NoBom.GetBytes($Text))
}

function Get-RecordDigest {
    param([Parameter(Mandatory = $true)][AllowEmptyCollection()][string[]]$Lines)

    [Array]::Sort($Lines, [StringComparer]::Ordinal)
    $Text = if ($Lines.Count -eq 0) { '' } else { ($Lines -join "`n") + "`n" }
    return Get-Sha256Text $Text
}

function Get-AuthoritySetDigest {
    param([Parameter(Mandatory = $true)][object]$Manifest)

    $Payload = [ordered]@{
        schemaVersion = 1
        storySlug = [string]$Manifest.storySlug
        generatedAt = [string]$Manifest.generatedAt
        universeFiles = @($Manifest.universeFiles)
        canonStories = @($Manifest.canonStories)
    }
    return Get-Sha256Text ($Payload | ConvertTo-Json -Depth 12 -Compress)
}

function Get-ByteSnapshot {
    param([Parameter(Mandatory = $true)][string[]]$Paths)

    $Snapshot = @{}
    foreach ($Path in $Paths) { $Snapshot[$Path] = [IO.File]::ReadAllBytes($Path) }
    return $Snapshot
}

function Assert-True {
    param(
        [Parameter(Mandatory = $true)][bool]$Condition,
        [Parameter(Mandatory = $true)][string]$Message
    )

    if (-not $Condition) { throw $Message }
}

function Assert-BytesEqual {
    param(
        [Parameter(Mandatory = $true)][byte[]]$Expected,
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Label
    )

    $Actual = [IO.File]::ReadAllBytes($Path)
    Assert-True (
        [Convert]::ToBase64String($Expected) -ceq [Convert]::ToBase64String($Actual)
    ) "$Label bytes changed."
}

function Invoke-Promotion {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [string]$Story = 'manifest-story'
    )

    $OutputItems = @(& $Pwsh -NoLogo -NoProfile -NonInteractive -File $PromotionScript -Story $Story -PromotionDate '2026-08-02' -ProjectRoot $Root 2>&1)
    return [pscustomobject]@{
        ExitCode = $LASTEXITCODE
        Output = ($OutputItems | Out-String).Trim()
    }
}

function New-PromotionFixture {
    param([Parameter(Mandatory = $true)][string]$Name)

    $Root = Join-Path $TestRoot $Name
    $Story = 'manifest-story'
    $StoryDirectory = Join-Path $Root "stories/$Story"
    $UniverseReadme = Join-Path $Root 'universe/README.md'
    $UniverseTarget = Join-Path $Root 'universe/rules.md'
    $IndexPath = Join-Path $Root 'stories/INDEX.md'
    $NamesPath = Join-Path $Root 'stories/NAMES.md'
    $StoryPath = Join-Path $StoryDirectory '05-story.md'
    $DeltaPath = Join-Path $StoryDirectory '06-canon-delta.md'
    $ReleasePath = Join-Path $StoryDirectory 'release.json'
    $ManifestPath = Join-Path $StoryDirectory 'promotion.json'
    $AuthorityPath = Join-Path $StoryDirectory 'authority.json'

    Write-FixtureFile $UniverseReadme "# Fixture authority`n"
    $UniversePreText = "# Rules`n`nNo promoted fixture fact yet.`n"
    $UniversePostText = @"
# Rules

## Fixture fact

- Status: CANON
- Summary: The manifest fixture proves transactional promotion.
- First established: stories/manifest-story/05-story.md
- Aliases: None
- Notes: Synthetic test fact.
"@
    Write-FixtureFile $UniverseTarget $UniversePreText
    [byte[]]$UniversePreBytes = [IO.File]::ReadAllBytes($UniverseTarget)
    $UniversePreSha = Get-Sha256Bytes $UniversePreBytes
    $UniversePostSha = Get-Sha256Text ($UniversePostText.Replace("`r`n", "`n").Replace("`r", "`n"))

    Write-FixtureFile (Join-Path $StoryDirectory 'story.json') (@{
        schemaVersion = 1
        slug = $Story
        title = 'Manifest Story'
        created = '2026-08-01'
        stage = 'candidate'
        status = 'candidate'
        canon = $false
        userDisposition = 'accepted'
        publish = $false
        promotionDate = $null
    } | ConvertTo-Json -Depth 10)
    Write-FixtureFile (Join-Path $StoryDirectory 'README.md') @"
# Manifest Story

- Current stage: candidate
- Status: candidate
- Canon: no
- User disposition: accepted
- Publish: no
- Promotion date: —

- [ ] Canon promotion explicitly approved (optional)
"@
    Write-FixtureFile (Join-Path $StoryDirectory '04-review.md') "# Review`n`nSynthetic passing review fixture.`n"
    Write-FixtureFile $StoryPath "# Manifest Story`n`nA certified synthetic story.`n"
    Write-FixtureFile $DeltaPath "# Canon delta`n`n- D-001: Fixture fact.`n"
    Write-FixtureFile $IndexPath @'
# Story index

| Story | Title | Status | Canon | User disposition | Publish | Promotion date | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `manifest-story` | *Manifest Story* | candidate | no | accepted | no | — | Fixture. |
'@
    Write-FixtureFile $NamesPath @'
# Names

<!-- registry:start -->
| Character / entity | Aliases | Story source | State | Reuse status | Notes |
| --- | --- | --- | --- | --- | --- |
| Ada Vale | `Ada Vale`; `Ada` | `manifest-story` | candidate | unique | Fixture. |
<!-- registry:end -->
'@

    $StorySha = Get-Sha256File $StoryPath
    $DeltaSha = Get-Sha256File $DeltaPath
    $AuthorityManifest = [ordered]@{
        schemaVersion = 1
        storySlug = $Story
        generatedAt = '2026-08-02T11:30:00Z'
        universeFiles = @(
            [ordered]@{ path = 'universe/README.md'; sha256 = Get-Sha256File $UniverseReadme }
            [ordered]@{ path = 'universe/rules.md'; sha256 = $UniversePreSha }
        )
        canonStories = @()
        manifestSha256 = $null
    }
    $AuthoritySetSha = Get-AuthoritySetDigest $AuthorityManifest
    $AuthorityManifest.manifestSha256 = $AuthoritySetSha
    Write-FixtureFile $AuthorityPath ($AuthorityManifest | ConvertTo-Json -Depth 20)
    $AuthorityRawSha = Get-Sha256File $AuthorityPath
    $RegistryReceiptSha = ('a' * 64)
    $Release = [ordered]@{
        schemaVersion = 2
        certified = $true
        storySlug = $Story
        certifiedAt = '2026-08-02T10:00:00Z'
        artifacts = [ordered]@{
            story = [ordered]@{ path = '05-story.md'; sha256 = $StorySha }
            canonDelta = [ordered]@{ path = '06-canon-delta.md'; sha256 = $DeltaSha }
        }
        review = [ordered]@{
            artifact = '05-story.md'; pass = 1; verdict = 'PASS'
            reviewer = 'fixture-reviewer'; unresolvedCritical = 0; unresolvedMajor = 0
        }
        nameCheck = [ordered]@{
            story = $Story; passed = $true; checkedAt = '2026-08-02T10:00:00Z'
            scopedRegistrySha256 = $RegistryReceiptSha
        }
        provenance = [ordered]@{
            authorityManifestSha256 = $AuthorityRawSha
            reviewAuthorityManifestSha256 = $AuthorityRawSha
            promotionPreparationSha256 = $null
        }
    }
    Write-FixtureFile $ReleasePath ($Release | ConvertTo-Json -Depth 20)
    $ReleaseSha = Get-Sha256File $ReleasePath

    Write-FixtureFile (Join-Path $Root '.agents/skills/story-name-validation/scripts/check-story-names.ps1') @'
#Requires -Version 7.0
param([string]$Story, [string]$Phase, [string]$OutputFormat, [string]$ProjectRoot)
function Hash([string]$Path) {
    [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData([IO.File]::ReadAllBytes($Path))).ToLowerInvariant()
}
$release = Get-Content -LiteralPath (Join-Path $ProjectRoot "stories/$Story/release.json") -Raw | ConvertFrom-Json
[ordered]@{
    passed = $true
    story = $Story
    phase = 'Final'
    storySha256 = Hash (Join-Path $ProjectRoot "stories/$Story/05-story.md")
    canonDeltaSha256 = Hash (Join-Path $ProjectRoot "stories/$Story/06-canon-delta.md")
    scopedRegistrySha256 = $release.nameCheck.scopedRegistrySha256
} | ConvertTo-Json -Compress
'@
    Write-FixtureFile (Join-Path $Root '.agents/skills/story-integrity/scripts/New-StoryRelease.ps1') @'
#Requires -Version 7.0
param([string]$Story, [string]$ProjectRoot, [switch]$PromotionFinalize)
function Hash([string]$Path) {
    [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData([IO.File]::ReadAllBytes($Path))).ToLowerInvariant()
}
$path = Join-Path $ProjectRoot "stories/$Story/release.json"
$release = Get-Content -LiteralPath $path -Raw | ConvertFrom-Json
$release.certifiedAt = '2026-08-02T12:30:00Z'
$release.nameCheck.scopedRegistrySha256 = ('b' * 64)
if ($PromotionFinalize) {
    $promotion = Get-Content -LiteralPath (Join-Path $ProjectRoot "stories/$Story/promotion.json") -Raw | ConvertFrom-Json
    $release.provenance.authorityManifestSha256 = Hash (Join-Path $ProjectRoot "stories/$Story/authority.json")
    $release.provenance.reviewAuthorityManifestSha256 = $promotion.authority.sha256
    $release.provenance.promotionPreparationSha256 = $promotion.preparationSha256
}
[IO.File]::WriteAllText($path, (($release | ConvertTo-Json -Depth 20) + "`n"), [Text.UTF8Encoding]::new($false))
Write-Output 'fixture release reissued'
'@
    Write-FixtureFile (Join-Path $Root '.agents/skills/story-integrity/scripts/Test-StoryIntegrity.ps1') @'
#Requires -Version 7.0
param([string]$Story, [string]$OutputFormat, [string]$ProjectRoot)
if (-not $Story -and (Test-Path -LiteralPath (Join-Path $ProjectRoot 'fail-repository'))) {
    Write-Error 'synthetic repository integrity failure'
    exit 1
}
if ($Story) {
    [ordered]@{ passed = $true; mode = 'story'; story = $Story; checkedStories = 1 } | ConvertTo-Json -Compress
}
else {
    [ordered]@{ passed = $true; mode = 'repository'; story = $null; checkedStories = 1 } | ConvertTo-Json -Compress
}
'@
    Write-FixtureFile (Join-Path $Root '.agents/skills/story-integrity/scripts/New-AuthorityManifest.ps1') @'
#Requires -Version 7.0
param([string]$Story, [switch]$Verify, [string]$OutputFormat, [string]$ProjectRoot)
function Hash([string]$Path) {
    [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData([IO.File]::ReadAllBytes($Path))).ToLowerInvariant()
}
function SetHash([object]$Manifest) {
    $payload = [ordered]@{
        schemaVersion = 1
        storySlug = [string]$Manifest.storySlug
        generatedAt = [string]$Manifest.generatedAt
        universeFiles = @($Manifest.universeFiles)
        canonStories = @($Manifest.canonStories)
    }
    $json = ($payload | ConvertTo-Json -Depth 12 -Compress).Replace("`r`n", "`n").Replace("`r", "`n")
    [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData([Text.UTF8Encoding]::new($false).GetBytes($json))).ToLowerInvariant()
}
$universe = @(Get-ChildItem -LiteralPath (Join-Path $ProjectRoot 'universe') -Recurse -File -Filter '*.md' | Sort-Object FullName | ForEach-Object {
    [ordered]@{ path = [IO.Path]::GetRelativePath($ProjectRoot, $_.FullName).Replace('\', '/'); sha256 = Hash $_.FullName }
})
$directory = Join-Path $ProjectRoot "stories/$Story"
$metadata = Get-Content -LiteralPath (Join-Path $directory 'story.json') -Raw | ConvertFrom-Json
$canon = @()
if ($metadata.canon -eq $true) {
    $canon = @([ordered]@{
        slug = $Story
        promotionDate = [string]$metadata.promotionDate
        storySha256 = Hash (Join-Path $directory '05-story.md')
        canonDeltaSha256 = Hash (Join-Path $directory '06-canon-delta.md')
    })
}
$manifest = [ordered]@{
    schemaVersion = 1; storySlug = $Story; generatedAt = '2026-08-02T12:20:00Z'
    universeFiles = $universe; canonStories = $canon; manifestSha256 = $null
}
$manifest.manifestSha256 = SetHash $manifest
$path = Join-Path $directory 'authority.json'
[IO.File]::WriteAllText($path, (($manifest | ConvertTo-Json -Depth 20) + "`n"), [Text.UTF8Encoding]::new($false))
[ordered]@{
    schemaVersion = 1; story = $Story; passed = $true
    manifestSha256 = Hash $path; authoritySetSha256 = $manifest.manifestSha256
    universeFiles = $universe.Count; canonStories = $canon.Count
} | ConvertTo-Json -Compress
'@

    $AuthorityLines = @(
        "stories/INDEX.md`t$(Get-Sha256File $IndexPath)",
        "universe/README.md`t$(Get-Sha256File $UniverseReadme)",
        "universe/rules.md`t$UniversePreSha"
    )
    $AuthorityDigest = Get-RecordDigest $AuthorityLines
    $Disposition = [pscustomobject]@{
        id = 'D-001'
        disposition = 'promote'
        target = 'universe/rules.md#Fixture fact'
        rationale = 'The synthetic reusable fact is explicitly approved for this test.'
    }
    $DispositionDigest = Get-RecordDigest @(
        "$($Disposition.id)`t$($Disposition.disposition)`t$($Disposition.target)`t$($Disposition.rationale)"
    )
    $Authorization = 'user turn fixture-authorize-manifest-story'
    $Handoff = @(
        'STEWARDSHIP_HANDOFF'
        "story: $Story"
        "authorization: $Authorization"
        'steward: canon_steward'
        'candidateRelease: VERIFIED'
        "candidateReleaseSha256: $ReleaseSha"
        'authorityRecheck: PASS'
        "authorityManifestSha256: $AuthorityRawSha"
        'resolutionQuestion: none'
        'nameCheckReceipt: VERIFIED'
        "storySha256: $StorySha"
        "canonDeltaSha256: $DeltaSha"
        "deltaDispositionsSha256: $DispositionDigest"
        'retconEvidenceSha256: none'
        'modifiedCanonFiles: universe/rules.md'
        'deltaDispositions: D-001'
        'retcon: none'
        'primaryWritesRequired: production records, release, validators'
        'result: CANON_APPLIED_AWAITING_PRIMARY'
    ) -join "`n"
    $Handoff += "`n"
    $Manifest = [ordered]@{
        schemaVersion = 1
        state = 'ready'
        storySlug = $Story
        promotionDate = '2026-08-02'
        preparedAt = '2026-08-02T12:00:00Z'
        preparationSha256 = $null
        authorization = [ordered]@{
            approved = $true; scope = 'canon-promotion'; storySlug = $Story
            reference = $Authorization
        }
        stewardship = [ordered]@{
            identity = 'canon_steward'; handoffText = $Handoff
            handoffSha256 = Get-Sha256Text $Handoff
            candidateRelease = 'VERIFIED'; authorityRecheck = 'PASS'
            nameCheckReceipt = 'VERIFIED'; result = 'CANON_APPLIED_AWAITING_PRIMARY'
        }
        authority = [ordered]@{
            path = "stories/$Story/authority.json"
            sha256 = $AuthorityRawSha
            authoritySetSha256 = $AuthoritySetSha
            capturedAt = '2026-08-02T11:30:00Z'; fileCount = 3
            manifestSha256 = $AuthorityDigest
            files = @(
                [ordered]@{ path = 'stories/INDEX.md'; sha256 = Get-Sha256File $IndexPath }
                [ordered]@{ path = 'universe/README.md'; sha256 = Get-Sha256File $UniverseReadme }
                [ordered]@{ path = 'universe/rules.md'; sha256 = $UniversePreSha }
            )
        }
        bundle = [ordered]@{
            release = [ordered]@{ path = "stories/$Story/release.json"; sha256 = $ReleaseSha }
            story = [ordered]@{ path = "stories/$Story/05-story.md"; sha256 = $StorySha }
            canonDelta = [ordered]@{ path = "stories/$Story/06-canon-delta.md"; sha256 = $DeltaSha }
        }
        deltaInventory = [ordered]@{
            sourceArtifactSha256 = $DeltaSha; itemCount = 1
            dispositionsSha256 = $DispositionDigest
        }
        deltaDispositions = @($Disposition)
        universeChanges = @([ordered]@{
            path = 'universe/rules.md'; preSha256 = $UniversePreSha
            postSha256 = $UniversePostSha
            preImageBase64 = [Convert]::ToBase64String($UniversePreBytes)
            deltaIds = @('D-001')
        })
        retcon = $null
        completion = $null
    }
    $Manifest.preparationSha256 = Get-PromotionPreparationSha256 $Manifest
    Write-FixtureFile $ManifestPath ($Manifest | ConvertTo-Json -Depth 30)
    Write-FixtureFile $UniverseTarget $UniversePostText

    return [pscustomobject]@{
        Root = $Root
        StoryDirectory = $StoryDirectory
        ManifestPath = $ManifestPath
        UniverseTarget = $UniverseTarget
        UniversePreBytes = $UniversePreBytes
        UniversePostBytes = [IO.File]::ReadAllBytes($UniverseTarget)
        UniverseReadme = $UniverseReadme
        ProductionPaths = @(
            (Join-Path $StoryDirectory 'story.json'), $ReleasePath,
            (Join-Path $StoryDirectory 'README.md'), $IndexPath, $NamesPath, $ManifestPath
            $AuthorityPath
        )
        StoryPath = $StoryPath
    }
}

function Invoke-Test {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][scriptblock]$Body
    )

    try {
        & $Body
        $script:Passed++
        Write-Host "PASS $Name"
    }
    catch {
        $script:Failed++
        Write-Host "FAIL $Name"
        Write-Host $_.Exception.Message
    }
}

try {
    $null = New-Item -ItemType Directory -Path $TestRoot -Force

    Invoke-Test 'refuses direct promotion when promotion.json is missing' {
        $Fixture = New-PromotionFixture 'missing'
        $Snapshots = Get-ByteSnapshot @($Fixture.ProductionPaths | Where-Object { $_ -cne $Fixture.ManifestPath })
        Remove-Item -LiteralPath $Fixture.ManifestPath -Force
        $Result = Invoke-Promotion $Fixture.Root
        Assert-True ($Result.ExitCode -ne 0 -and $Result.Output -match 'promotion.json') 'Missing manifest was not rejected.'
        foreach ($Path in $Snapshots.Keys) { Assert-BytesEqual $Snapshots[$Path] $Path "Missing manifest $Path" }
        Assert-BytesEqual $Fixture.UniversePostBytes $Fixture.UniverseTarget 'Missing manifest universe post-image'
        Assert-True (-not (Test-Path -LiteralPath (Join-Path $Fixture.Root '.story-locks'))) 'Missing-manifest refusal left transaction-lock state.'
    }

    Invoke-Test 'refuses a schema-valid manifest for the wrong story' {
        $Fixture = New-PromotionFixture 'wrong-story'
        $Manifest = Get-Content -LiteralPath $Fixture.ManifestPath -Raw | ConvertFrom-Json
        $Manifest.storySlug = 'different-story'
        $Manifest.authorization.storySlug = 'different-story'
        Write-FixtureFile $Fixture.ManifestPath ($Manifest | ConvertTo-Json -Depth 30)
        $Snapshots = Get-ByteSnapshot $Fixture.ProductionPaths
        $Result = Invoke-Promotion $Fixture.Root
        Assert-True ($Result.ExitCode -ne 0 -and $Result.Output -match 'exact story') 'Wrong-story manifest was not rejected.'
        foreach ($Path in $Snapshots.Keys) { Assert-BytesEqual $Snapshots[$Path] $Path "Wrong story $Path" }
    }

    Invoke-Test 'refuses an incomplete manifest at the JSON Schema gate' {
        $Fixture = New-PromotionFixture 'incomplete'
        $Manifest = Get-Content -LiteralPath $Fixture.ManifestPath -Raw | ConvertFrom-Json
        $Manifest.PSObject.Properties.Remove('deltaInventory')
        Write-FixtureFile $Fixture.ManifestPath ($Manifest | ConvertTo-Json -Depth 30)
        $Snapshots = Get-ByteSnapshot $Fixture.ProductionPaths
        $Result = Invoke-Promotion $Fixture.Root
        Assert-True ($Result.ExitCode -ne 0 -and $Result.Output -match 'schema validation') 'Incomplete manifest was not rejected by schema validation.'
        foreach ($Path in $Snapshots.Keys) { Assert-BytesEqual $Snapshots[$Path] $Path "Incomplete $Path" }
    }

    Invoke-Test 'rolls back the steward universe write when the bound story becomes stale' {
        $Fixture = New-PromotionFixture 'stale'
        Write-FixtureFile $Fixture.StoryPath "# Manifest Story`n`nStale bytes after stewardship.`n"
        $Snapshots = Get-ByteSnapshot $Fixture.ProductionPaths
        [byte[]]$StaleStoryBytes = [IO.File]::ReadAllBytes($Fixture.StoryPath)
        $Result = Invoke-Promotion $Fixture.Root
        Assert-True ($Result.ExitCode -ne 0 -and $Result.Output -match 'bundle hashes are stale') 'Stale manifest was not rejected.'
        Assert-True ($Result.Output -match 'restored byte-for-byte') 'Stale transaction did not report rollback.'
        foreach ($Path in $Snapshots.Keys) { Assert-BytesEqual $Snapshots[$Path] $Path "Stale $Path" }
        Assert-BytesEqual $StaleStoryBytes $Fixture.StoryPath 'Stale reviewed story'
        Assert-BytesEqual $Fixture.UniversePreBytes $Fixture.UniverseTarget 'Stale universe rollback'
    }

    Invoke-Test 'refuses a ready manifest whose immutable preparation changed' {
        $Fixture = New-PromotionFixture 'tampered-preparation'
        $Manifest = Get-Content -LiteralPath $Fixture.ManifestPath -Raw | ConvertFrom-Json
        $Manifest.authorization.reference = 'tampered authorization after preparation'
        Write-FixtureFile $Fixture.ManifestPath ($Manifest | ConvertTo-Json -Depth 30)
        $Snapshots = Get-ByteSnapshot $Fixture.ProductionPaths
        $Result = Invoke-Promotion $Fixture.Root
        Assert-True ($Result.ExitCode -ne 0 -and $Result.Output -match 'immutable preparation') 'Tampered preparation was accepted.'
        foreach ($Path in $Snapshots.Keys) { Assert-BytesEqual $Snapshots[$Path] $Path "Tampered preparation $Path" }
        Assert-BytesEqual $Fixture.UniversePostBytes $Fixture.UniverseTarget 'Untrusted manifest universe post-image'
    }

    Invoke-Test 'completes an authorization-bound promotion and persists provenance' {
        $Fixture = New-PromotionFixture 'positive'
        [byte[]]$UniverseReadmeBefore = [IO.File]::ReadAllBytes($Fixture.UniverseReadme)
        $Result = Invoke-Promotion $Fixture.Root
        Assert-True ($Result.ExitCode -eq 0 -and $Result.Output -match 'result: PROMOTED') "Positive promotion failed: $($Result.Output)"
        $Metadata = Get-Content -LiteralPath (Join-Path $Fixture.StoryDirectory 'story.json') -Raw | ConvertFrom-Json
        Assert-True ($Metadata.canon -eq $true -and $Metadata.status -eq 'final' -and $Metadata.stage -eq 'final') 'Lifecycle was not promoted.'
        $Manifest = Get-Content -LiteralPath $Fixture.ManifestPath -Raw | ConvertFrom-Json
        $FinalRelease = Get-Content -LiteralPath (Join-Path $Fixture.StoryDirectory 'release.json') -Raw | ConvertFrom-Json
        Assert-True (
            $Manifest.state -ceq 'completed' -and $Manifest.completion.result -ceq 'PROMOTED' -and
            $Manifest.completion.candidateReleaseSha256 -cne $Manifest.completion.finalReleaseSha256 -and
            $Manifest.stewardship.identity -ceq 'canon_steward' -and
            (Get-PromotionPreparationSha256 $Manifest) -ceq $Manifest.preparationSha256 -and
            $FinalRelease.provenance.reviewAuthorityManifestSha256 -ceq $Manifest.authority.sha256 -and
            $FinalRelease.provenance.promotionPreparationSha256 -ceq $Manifest.preparationSha256
        ) 'Durable completed promotion provenance is incomplete.'
        Assert-BytesEqual $Fixture.UniversePostBytes $Fixture.UniverseTarget 'Positive universe post-image'
        Assert-BytesEqual $UniverseReadmeBefore $Fixture.UniverseReadme 'Positive non-target universe file'
        Assert-True (-not (Test-Path -LiteralPath (Join-Path $Fixture.Root '.story-locks'))) 'Successful promotion left transaction-lock state.'
    }

    Invoke-Test 'rolls universe and production back after a post-write repository failure' {
        $Fixture = New-PromotionFixture 'rollback'
        $Snapshots = Get-ByteSnapshot $Fixture.ProductionPaths
        Write-FixtureFile (Join-Path $Fixture.Root 'fail-repository') "fail`n"
        $Result = Invoke-Promotion $Fixture.Root
        Assert-True ($Result.ExitCode -ne 0 -and $Result.Output -match 'repository integrity validation failed') 'Synthetic post-write failure was not reached.'
        Assert-True ($Result.Output -match 'result: NO_CHANGES') 'Rollback did not report NO_CHANGES.'
        foreach ($Path in $Snapshots.Keys) { Assert-BytesEqual $Snapshots[$Path] $Path "Rollback $Path" }
        Assert-BytesEqual $Fixture.UniversePreBytes $Fixture.UniverseTarget 'Rollback steward universe write'
        $Temps = @(Get-ChildItem -LiteralPath $Fixture.Root -Recurse -File -Filter '*.tmp.*')
        Assert-True ($Temps.Count -eq 0) 'Rollback left atomic-write temporary files.'
        Assert-True (-not (Test-Path -LiteralPath (Join-Path $Fixture.Root '.story-locks'))) 'Rollback left transaction-lock state.'
    }
}
finally {
    if (Test-Path -LiteralPath $TestRoot -PathType Container) {
        Remove-Item -LiteralPath $TestRoot -Recurse -Force
    }
}

Write-Host "`n$($script:Passed) passed, $($script:Failed) failed."
if ($script:Failed -gt 0) { exit 1 }
