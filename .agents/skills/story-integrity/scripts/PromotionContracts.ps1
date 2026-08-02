Set-StrictMode -Version Latest
function Assert-PromotionRecord {
 param([Parameter(Mandatory)][object]$Value,[Parameter(Mandatory)][string]$Story)
 . (Join-Path $PSScriptRoot 'PipelineCommon.ps1')
 Assert-PipelineFields $Value @('schemaVersion','state','storySlug','authorization','promotionDate','stewardship','deltaDispositions','modifiedFiles','completedAt','result','rollback') 'promotion.json'
 if($Value.schemaVersion-ne2-or$Value.storySlug-cne$Story){throw 'Promotion identity/version is invalid.'};if($Value.state-cnotin@('not-prepared','ready','completed')){throw 'Promotion state is invalid.'}
 Assert-PipelineFields $Value.rollback @('attempted','succeeded','detail') 'promotion rollback'
 if($Value.state-cin@('ready','completed')){
  Assert-PipelineFields $Value.authorization @('requestedBy','authorizedAt','basis') 'promotion authorization';Assert-PipelineFields $Value.stewardship @('identity','handoffText','authorityRecheck','nameCheck') 'promotion stewardship'
  if([string]::IsNullOrWhiteSpace([string]$Value.authorization.requestedBy)-or-not(Test-PipelineTimestamp $Value.authorization.authorizedAt)-or[string]::IsNullOrWhiteSpace([string]$Value.authorization.basis)-or-not(Test-PipelineDate $Value.promotionDate)-or[string]::IsNullOrWhiteSpace([string]$Value.stewardship.identity)-or[string]::IsNullOrWhiteSpace([string]$Value.stewardship.handoffText)-or$Value.stewardship.authorityRecheck-cne'PASS'-or$Value.stewardship.nameCheck-cne'VERIFIED'-or@($Value.deltaDispositions).Count-eq0){throw 'Prepared promotion lacks valid authorization, stewardship, date, or dispositions.'}
  $ids=@{};foreach($d in @($Value.deltaDispositions)){Assert-PipelineFields $d @('id','disposition','target','rationale') 'delta disposition';if($ids.ContainsKey([string]$d.id)){throw 'Duplicate delta disposition id.'};$ids[[string]$d.id]=$true;if($d.disposition-cnotin@('promote','story-local','defer','reject')){throw 'Invalid delta disposition.'};if($d.disposition-ceq'promote'-and[string]::IsNullOrWhiteSpace([string]$d.target)){throw 'Promoted delta requires target.'}}
 }
 if($Value.state-ceq'completed' -and ($Value.result-cne'PROMOTED'-or-not(Test-PipelineTimestamp $Value.completedAt))){throw 'Completed promotion lacks its result or completion time.'}
}