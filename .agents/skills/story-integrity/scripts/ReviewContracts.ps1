Set-StrictMode -Version Latest
function Get-StructuredReviewPasses {
 param([Parameter(Mandatory)][string]$Path)
 $text=Get-Content -LiteralPath $Path -Raw;$passes=[Collections.Generic.List[object]]::new()
 foreach($m in [regex]::Matches($text,'(?s)REVIEW_PASS_PAYLOAD\s*\n(?<json>\{.*?\})\s*\nEND_REVIEW_PASS_PAYLOAD')){try{$passes.Add(($m.Groups['json'].Value|ConvertFrom-Json -Depth 100 -DateKind String))}catch{throw "Invalid review payload in $Path"}}
 return @($passes)
}
function Assert-ReviewPayload {
 param([Parameter(Mandatory)][object]$Value,[Parameter(Mandatory)][object]$Contract)
 . (Join-Path $PSScriptRoot 'PipelineCommon.ps1');Assert-PipelineFields $Value @($Contract.reviewPass.fields) 'review payload'
 if($Value.mode-cnotin@($Contract.reviewPass.modes)-or$Value.status-cnotin@($Contract.reviewPass.persistedStatuses)-or$Value.verdict-cnotin@($Contract.reviewPass.verdicts)-or[int]$Value.pass-lt1){throw 'Review payload mode, status, verdict, or pass is invalid.'}
 Assert-PipelineFields $Value.unresolvedCounts @('Critical','Major','Minor') 'review unresolvedCounts'
}
function Get-LatestStructuredReview {param([Parameter(Mandatory)][string]$Path,[Parameter(Mandatory)][string]$Mode);return @(Get-StructuredReviewPasses $Path|Where-Object mode -CEQ $Mode|Sort-Object {[int]$_.pass})|Select-Object -Last 1}