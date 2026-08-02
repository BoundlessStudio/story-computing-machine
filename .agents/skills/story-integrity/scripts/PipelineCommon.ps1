Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Read-PipelineJson {
    param([Parameter(Mandatory)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "Missing JSON file: $Path" }
    try { return Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json -Depth 100 -DateKind String }
    catch { throw "Invalid JSON '$Path': $($_.Exception.Message)" }
}

function Write-PipelineJson {
    param([Parameter(Mandatory)][string]$Path,[Parameter(Mandatory)][object]$Value)
    $parent = Split-Path -Parent $Path
    if (-not (Test-Path -LiteralPath $parent)) { $null = New-Item -ItemType Directory -Path $parent -Force }
    $text = ($Value | ConvertTo-Json -Depth 100).Replace("`r`n","`n").Replace("`r","`n") + "`n"
    $temporary = "$Path.tmp.$([guid]::NewGuid().ToString('N'))"
    try {
        [IO.File]::WriteAllText($temporary,$text,[Text.UTF8Encoding]::new($false))
        Move-Item -LiteralPath $temporary -Destination $Path -Force
    }
    finally { if(Test-Path -LiteralPath $temporary){Remove-Item -LiteralPath $temporary -Force} }
}

function Assert-PipelineFields {
    param([Parameter(Mandatory)][object]$Value,[Parameter(Mandatory)][string[]]$Fields,[Parameter(Mandatory)][string]$Label)
    $actual = @($Value.PSObject.Properties.Name)
    $missing = @($Fields | Where-Object { $_ -cnotin $actual })
    $extra = @($actual | Where-Object { $_ -cnotin $Fields })
    if($missing.Count -or $extra.Count){ throw "$Label fields differ; missing=[$($missing -join ', ')], extra=[$($extra -join ', ')]." }
}

function Get-PipelineContract {
    param([Parameter(Mandatory)][string]$ProjectRoot)
    return Read-PipelineJson (Join-Path $ProjectRoot 'schemas/pipeline-contract.json')
}

function Get-RepositoryBranch {
    param([Parameter(Mandatory)][string]$ProjectRoot)
    $git = Get-Command git -ErrorAction SilentlyContinue
    if($null -eq $git -or -not (Test-Path -LiteralPath (Join-Path $ProjectRoot '.git'))){ return $null }
    $value = (& git -C $ProjectRoot branch --show-current 2>$null | Out-String).Trim()
    if($LASTEXITCODE -ne 0){ return $null }
    return $value
}

function Assert-ProductionBranch {
    param([Parameter(Mandatory)][string]$ProjectRoot)
    $branch = Get-RepositoryBranch $ProjectRoot
    if($branch -ceq 'main'){ throw 'Story and universe mutations are forbidden on main. Create a codex/story-<slug> or implementation branch.' }
}

function Test-PipelineSlug { param([string]$Value) return $Value -cmatch '^[a-z0-9]+(?:-[a-z0-9]+)*$' }
function Test-PipelineDate { param([object]$Value) return $Value -is [string] -and $Value -cmatch '^\d{4}-\d{2}-\d{2}$' }
function Test-PipelineTimestamp { param([object]$Value) if($Value -isnot [string]){return $false}; $parsed=[DateTimeOffset]::MinValue; return [DateTimeOffset]::TryParse($Value,[ref]$parsed) }
function Get-RelativeUnixPath { param([string]$Root,[string]$Path) return [IO.Path]::GetRelativePath($Root,$Path).Replace('\','/') }

function Test-StoryLifecycleRecord {
    param([Parameter(Mandatory)][object]$Record,[Parameter(Mandatory)][object]$Contract)
    $errors=[Collections.Generic.List[string]]::new()
    try { Assert-PipelineFields $Record @($Contract.story.fields) 'story.json' } catch {$errors.Add($_.Exception.Message)}
    if($Record.schemaVersion -ne $Contract.story.schemaVersion){$errors.Add("story.json schemaVersion must be $($Contract.story.schemaVersion).")}
    if(-not (Test-PipelineSlug ([string]$Record.slug))){$errors.Add('story.json slug is invalid.')}
    if(-not (Test-PipelineDate $Record.created)){$errors.Add('story.json created must be YYYY-MM-DD.')}
    if([string]$Record.provenance -cnotin @($Contract.story.provenanceValues)){$errors.Add('story.json provenance is invalid.')}
    $state=$Contract.lifecycle.states.PSObject.Properties[[string]$Record.status].Value
    if($null -eq $state){$errors.Add('story.json status is invalid.');return $errors}
    if([string]$Record.stage -cnotin @($state.stages)){$errors.Add('story.json stage/status combination is invalid.')}
    if([bool]$Record.canon -ne [bool]$state.canon){$errors.Add('story.json canon flag conflicts with status.')}
    if([string]$Record.userDisposition -cnotin @($state.userDispositions)){$errors.Add('story.json disposition conflicts with status.')}
    if([bool]$Record.publish -cnotin @($state.publish)){$errors.Add('story.json publication conflicts with status.')}
    if([string]$state.promotionDate -ceq 'required' -and -not (Test-PipelineDate $Record.promotionDate)){$errors.Add('story.json final state requires a promotion date.')}
    if([string]$state.promotionDate -ceq 'null' -and $null -ne $Record.promotionDate){$errors.Add('story.json non-final state cannot have a promotion date.')}
    return $errors
}

function Get-IndexRows {
    param([Parameter(Mandatory)][string]$Path)
    $rows=@{}
    foreach($line in Get-Content -LiteralPath $Path){
        if($line -notmatch '^\| `(?<slug>[a-z0-9-]+)` \| \*(?<title>[^*]+)\* \| (?<status>[^|]+) \| (?<canon>yes|no) \| (?<disposition>[^|]+) \| (?<publish>yes|no) \| (?<date>[^|]+) \| (?<notes>.*) \|$'){continue}
        $rows[$Matches.slug]=[pscustomobject]@{slug=$Matches.slug;title=$Matches.title;status=$Matches.status.Trim();canon=$Matches.canon;disposition=$Matches.disposition.Trim();publish=$Matches.publish;promotionDate=$Matches.date.Trim();notes=$Matches.notes.Trim()}
    }
    return $rows
}

function Get-LegacyAcceptance {
    param([Parameter(Mandatory)][string]$ProjectRoot)
    $path=Join-Path $ProjectRoot 'stories/legacy-acceptance.json'
    if(-not (Test-Path -LiteralPath $path)){return $null}
    $value=Read-PipelineJson $path
    Assert-PipelineFields $value @('schemaVersion','acceptedBy','acceptedAt','reviewBasis','stories') 'legacy acceptance'
    if($value.schemaVersion -ne 1 -or [string]::IsNullOrWhiteSpace([string]$value.acceptedBy) -or -not (Test-PipelineTimestamp $value.acceptedAt)){throw 'Legacy acceptance header is invalid.'}
    $seen=@{}
    foreach($item in @($value.stories)){
        Assert-PipelineFields $item @('slug','promotionDate') 'legacy acceptance story'
        if(-not (Test-PipelineSlug ([string]$item.slug)) -or -not (Test-PipelineDate $item.promotionDate)){throw 'Legacy acceptance story entry is invalid.'}
        if($seen.ContainsKey([string]$item.slug)){throw "Duplicate legacy acceptance slug: $($item.slug)"}
        $seen[[string]$item.slug]=$item
    }
    return [pscustomobject]@{record=$value;bySlug=$seen}
}

function Get-ReviewCertification {
    param([Parameter(Mandatory)][string]$Path)
    $text=Get-Content -LiteralPath $Path -Raw
    $artifact=[regex]::Match($text,'(?m)^- Reviewed artifact: `?(?<v>[^`\r\n]+)`?\s*$').Groups['v'].Value
    $passText=[regex]::Match($text,'(?m)^- Review pass: (?<v>\d+)\s*$').Groups['v'].Value
    $verdict=[regex]::Match($text,'(?m)^- Verdict: (?<v>PASS|REVISE|BLOCK)\s*$').Groups['v'].Value
    $updated=[regex]::Match($text,'(?m)^- Updated: (?<v>[^\r\n]+)\s*$').Groups['v'].Value
    return [pscustomobject]@{artifact=$artifact;pass=$(if($passText){[int]$passText}else{0});verdict=$verdict;updated=$updated}
}
