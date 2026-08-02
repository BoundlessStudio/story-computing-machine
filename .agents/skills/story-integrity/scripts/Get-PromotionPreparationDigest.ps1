#Requires -Version 7.0

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ManifestPath
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'PromotionContracts.ps1')

$Resolved = (Resolve-Path -LiteralPath $ManifestPath).Path
$Parameters = @{}
if ((Get-Command ConvertFrom-Json).Parameters.ContainsKey('DateKind')) {
    $Parameters.DateKind = 'String'
}
$Manifest = Get-Content -LiteralPath $Resolved -Raw | ConvertFrom-Json @Parameters
Get-PromotionPreparationSha256 $Manifest
