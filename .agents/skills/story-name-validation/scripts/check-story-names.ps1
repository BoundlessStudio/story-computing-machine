#Requires -Version 7.0

[CmdletBinding()]
param(
    [ValidatePattern('^[a-z0-9]+(?:-[a-z0-9]+)*$')]
    [string]$Story,

    [switch]$Strict,

    [ValidateSet('Auto', 'Plan', 'Final')]
    [string]$Phase = 'Auto',

    [ValidateSet('Text', 'Json')]
    [string]$OutputFormat = 'Text',

    [switch]$SkipConfusable,

    [string]$ProjectRoot
)

$ErrorActionPreference = 'Stop'

$Implementation = (Resolve-Path -LiteralPath (
    Join-Path $PSScriptRoot '../../story-integrity/scripts/Test-StoryNames.ps1'
)).Path
& $Implementation @PSBoundParameters
