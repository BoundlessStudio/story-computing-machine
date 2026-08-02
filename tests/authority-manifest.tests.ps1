#Requires -Version 7.0

[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$RepoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$ScriptPath = Join-Path $RepoRoot '.agents/skills/story-integrity/scripts/New-AuthorityManifest.ps1'
$Pwsh = (Get-Command pwsh -ErrorAction Stop).Source
$TestRoot = Join-Path ([IO.Path]::GetTempPath()) ('authority-manifest-tests-' + [guid]::NewGuid().ToString('N'))
$Utf8 = [Text.UTF8Encoding]::new($false)
$script:Passed = 0
$script:Failed = 0

function Write-FixtureFile {
    param([Parameter(Mandatory = $true)][string]$Path, [Parameter(Mandatory = $true)][AllowEmptyString()][string]$Content)
    $Directory = Split-Path -Parent $Path
    if (-not (Test-Path -LiteralPath $Directory -PathType Container)) { $null = New-Item -ItemType Directory -Path $Directory -Force }
    [IO.File]::WriteAllText($Path, $Content.Replace("`r`n", "`n").Replace("`r", "`n"), $Utf8)
}

function Hash-File {
    param([Parameter(Mandatory = $true)][string]$Path)
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function New-AuthorityFixture {
    param([Parameter(Mandatory = $true)][string]$Name)
    $Root = Join-Path $TestRoot $Name
    $Work = Join-Path $Root 'stories/work-story'
    $Canon = Join-Path $Root 'stories/canon-story'
    Write-FixtureFile (Join-Path $Root 'universe/README.md') "# Authority`n"
    Write-FixtureFile (Join-Path $Root 'universe/rules.md') "# Rules`n"
    Write-FixtureFile (Join-Path $Root 'stories/INDEX.md') @'
# Story index

| Story | Title | Status | Canon | User disposition | Publish | Promotion date | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `canon-story` | *Canon Story* | final | yes | accepted | no | 2026-08-01 | Fixture. |
| `work-story` | *Work Story* | in-progress | no | pending | no | — | Fixture. |
'@
    $WorkMetadata = [ordered]@{
        schemaVersion = 1; slug = 'work-story'; title = 'Work Story'; created = '2026-08-02'
        stage = 'prompt'; status = 'in-progress'; canon = $false
        userDisposition = 'pending'; publish = $false; promotionDate = $null
    }
    $CanonMetadata = [ordered]@{
        schemaVersion = 1; slug = 'canon-story'; title = 'Canon Story'; created = '2026-08-01'
        stage = 'final'; status = 'final'; canon = $true
        userDisposition = 'accepted'; publish = $false; promotionDate = '2026-08-01'
    }
    Write-FixtureFile (Join-Path $Work 'story.json') (($WorkMetadata | ConvertTo-Json) + "`n")
    Write-FixtureFile (Join-Path $Work 'authority.json') "{}`n"
    Write-FixtureFile (Join-Path $Canon 'story.json') (($CanonMetadata | ConvertTo-Json) + "`n")
    Write-FixtureFile (Join-Path $Canon '05-story.md') "# Canon fixture`n"
    Write-FixtureFile (Join-Path $Canon '06-canon-delta.md') "# Delta`n"
    $Release = [ordered]@{
        schemaVersion = 2; certified = $true; storySlug = 'canon-story'
        artifacts = [ordered]@{
            story = [ordered]@{ path = '05-story.md'; sha256 = Hash-File (Join-Path $Canon '05-story.md') }
            canonDelta = [ordered]@{ path = '06-canon-delta.md'; sha256 = Hash-File (Join-Path $Canon '06-canon-delta.md') }
        }
    }
    Write-FixtureFile (Join-Path $Canon 'release.json') (($Release | ConvertTo-Json -Depth 8) + "`n")
    return [pscustomobject]@{ Root = $Root; Work = $Work; Canon = $Canon }
}

function Invoke-Authority {
    param([Parameter(Mandatory = $true)][string]$Root, [switch]$Verify)
    $Arguments = @('-NoLogo', '-NoProfile', '-NonInteractive', '-File', $ScriptPath,
        '-Story', 'work-story', '-OutputFormat', 'Json', '-ProjectRoot', $Root)
    if ($Verify) { $Arguments += '-Verify' }
    $Items = @(& $Pwsh @Arguments 2>&1)
    return [pscustomobject]@{ ExitCode = $LASTEXITCODE; Output = ($Items | Out-String).Trim() }
}

function Assert-True {
    param([Parameter(Mandatory = $true)][bool]$Condition, [Parameter(Mandatory = $true)][string]$Message)
    if (-not $Condition) { throw $Message }
}

function Invoke-Test {
    param([Parameter(Mandatory = $true)][string]$Name, [Parameter(Mandatory = $true)][scriptblock]$Body)
    try { & $Body; $script:Passed++; Write-Host "PASS $Name" }
    catch { $script:Failed++; Write-Host "FAIL $Name"; Write-Host $_.Exception.Message }
}

try {
    $null = New-Item -ItemType Directory -Path $TestRoot -Force
    Invoke-Test 'writes and verifies a reconciled stable authority snapshot' {
        $Fixture = New-AuthorityFixture 'valid'
        $Write = Invoke-Authority $Fixture.Root
        Assert-True ($Write.ExitCode -eq 0) "Authority write failed: $($Write.Output)"
        $Receipt = $Write.Output | ConvertFrom-Json
        Assert-True ($Receipt.passed -eq $true -and $Receipt.canonStories -eq 1 -and $Receipt.universeFiles -eq 2) 'Authority receipt counts are wrong.'
        $Verify = Invoke-Authority $Fixture.Root -Verify
        Assert-True ($Verify.ExitCode -eq 0) "Authority verify failed: $($Verify.Output)"
    }
    Invoke-Test 'rejects an index projection that disagrees with story metadata' {
        $Fixture = New-AuthorityFixture 'index-mismatch'
        $IndexPath = Join-Path $Fixture.Root 'stories/INDEX.md'
        $Index = [IO.File]::ReadAllText($IndexPath).Replace('*Canon Story*', '*Wrong Title*')
        Write-FixtureFile $IndexPath $Index
        $Result = Invoke-Authority $Fixture.Root
        Assert-True ($Result.ExitCode -ne 0 -and $Result.Output -match 'disagrees') 'Index mismatch was accepted.'
    }
    Invoke-Test 'rejects a story directory missing from the index' {
        $Fixture = New-AuthorityFixture 'orphan'
        $Orphan = Join-Path $Fixture.Root 'stories/orphan-story'
        Write-FixtureFile (Join-Path $Orphan 'story.json') '{"schemaVersion":1,"slug":"orphan-story"}'
        $Result = Invoke-Authority $Fixture.Root
        Assert-True ($Result.ExitCode -ne 0 -and $Result.Output -match 'exact bijection') 'Directory/index mismatch was accepted.'
    }
    Invoke-Test 'rejects a stale promoted-story release' {
        $Fixture = New-AuthorityFixture 'stale-release'
        Write-FixtureFile (Join-Path $Fixture.Canon '05-story.md') "# Mutated canon fixture`n"
        $Result = Invoke-Authority $Fixture.Root
        Assert-True ($Result.ExitCode -ne 0 -and $Result.Output -match 'current schema-version-2 release') 'Stale canon release was accepted.'
    }
    Invoke-Test 'rejects a partial final lifecycle projection' {
        $Fixture = New-AuthorityFixture 'partial-final'
        $MetadataPath = Join-Path $Fixture.Canon 'story.json'
        $Metadata = Get-Content -LiteralPath $MetadataPath -Raw | ConvertFrom-Json
        $Metadata.canon = $false
        Write-FixtureFile $MetadataPath (($Metadata | ConvertTo-Json) + "`n")
        $IndexPath = Join-Path $Fixture.Root 'stories/INDEX.md'
        Write-FixtureFile $IndexPath ([IO.File]::ReadAllText($IndexPath).Replace('| final | yes |', '| final | no |'))
        $Result = Invoke-Authority $Fixture.Root
        Assert-True ($Result.ExitCode -ne 0 -and $Result.Output -match 'partial or invalid final') 'Partial final lifecycle was accepted.'
    }
    Invoke-Test 'detects authority staleness after a universe mutation' {
        $Fixture = New-AuthorityFixture 'stale-verify'
        $Write = Invoke-Authority $Fixture.Root
        Assert-True ($Write.ExitCode -eq 0) "Initial authority write failed: $($Write.Output)"
        Write-FixtureFile (Join-Path $Fixture.Root 'universe/rules.md') "# Rules`n`nChanged.`n"
        $Verify = Invoke-Authority $Fixture.Root -Verify
        Assert-True ($Verify.ExitCode -ne 0 -and $Verify.Output -match 'stale') 'Stale authority manifest verified.'
    }
}
finally {
    if (Test-Path -LiteralPath $TestRoot -PathType Container) { Remove-Item -LiteralPath $TestRoot -Recurse -Force }
}

Write-Host "`n$($script:Passed) passed, $($script:Failed) failed."
if ($script:Failed -gt 0) { exit 1 }
