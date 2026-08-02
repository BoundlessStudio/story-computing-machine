#Requires -Version 7.0
[CmdletBinding()]param([ValidateSet('Text','Json')][string]$OutputFormat='Text',[string]$ProjectRoot)
$ErrorActionPreference='Stop'
if([string]::IsNullOrWhiteSpace($ProjectRoot)){$ProjectRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../../..'))}
$errors=[Collections.Generic.List[string]]::new();$files=@(Get-ChildItem -LiteralPath (Join-Path $ProjectRoot 'universe') -Filter *.md -File)
$required=@('README.md','premise.md','rules.md','timeline.md','characters.md','locations.md','factions.md','glossary.md','style-guide.md','retcons.md')
foreach($name in $required){if(-not (Test-Path -LiteralPath (Join-Path $ProjectRoot "universe/$name"))){$errors.Add("Missing universe file: $name")}}
foreach($file in $files){
 $text=Get-Content -LiteralPath $file.FullName -Raw
 if($text -notmatch '(?m)^# '){$errors.Add("$($file.Name) has no title heading.")}
 if($file.Name -notin @('README.md','retcons.md','style-guide.md') -and $text -match '(?m)^## ' -and $text -notmatch '(?m)^- Status: (LOCKED|CANON|PROVISIONAL|RETIRED)\s*$'){$errors.Add("$($file.Name) has entries but no authority status markers.")}
}
$result=[ordered]@{schemaVersion=1;passed=($errors.Count -eq 0);checkedFiles=$files.Count;errors=@($errors)}
if($OutputFormat -ceq 'Json'){$result|ConvertTo-Json -Depth 8}else{if($result.passed){"Universe integrity passed ($($files.Count) files)."}else{$errors|ForEach-Object{"ERROR: $_"}}}
if(-not $result.passed){exit 1}
