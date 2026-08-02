Set-StrictMode -Version Latest
$script:RepoRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$script:Pwsh=(Get-Command pwsh -ErrorAction Stop).Source
function Assert-True([bool]$Condition,[string]$Message){if(-not$Condition){throw $Message}}
function Assert-Equal($Expected,$Actual,[string]$Message){if($Expected-cne$Actual){throw "$Message Expected '$Expected', got '$Actual'."}}
function Invoke-TestScript([string]$Path,[string[]]$Arguments=@()){ $output=@(& $script:Pwsh -NoLogo -NoProfile -File $Path @Arguments 2>&1);[pscustomobject]@{Succeeded=$?;Output=($output-join"`n")} }
function New-TestRoot([string]$Label){$root=Join-Path ([IO.Path]::GetTempPath()) ("scm-$Label-$([guid]::NewGuid().ToString('N'))");$null=New-Item -ItemType Directory -Path $root;return $root}
function Remove-TestRoot([string]$Root){$resolved=[IO.Path]::GetFullPath($Root);$temp=[IO.Path]::GetFullPath([IO.Path]::GetTempPath());if(-not$resolved.StartsWith($temp,[StringComparison]::OrdinalIgnoreCase)-or-not([IO.Path]::GetFileName($resolved).StartsWith('scm-'))){throw "Unsafe test cleanup target: $resolved"};if(Test-Path -LiteralPath $resolved){Remove-Item -LiteralPath $resolved -Recurse -Force}}
function Write-TestJson([string]$Path,[object]$Value){$parent=Split-Path -Parent $Path;if(-not(Test-Path $parent)){$null=New-Item -ItemType Directory -Path $parent -Force};[IO.File]::WriteAllText($Path,(($Value|ConvertTo-Json -Depth 100)+"`n"),[Text.UTF8Encoding]::new($false))}
function Initialize-TestGit([string]$Root,[string]$Branch='main'){& git -C $Root init -q;& git -C $Root config user.email tests@example.invalid;& git -C $Root config user.name 'Pipeline Tests';& git -C $Root checkout -q -b $Branch}
function Commit-TestGit([string]$Root,[string]$Message){& git -C $Root add -A;& git -C $Root commit -q -m $Message;if($LASTEXITCODE-ne0){throw "Test commit failed: $Message"}}
