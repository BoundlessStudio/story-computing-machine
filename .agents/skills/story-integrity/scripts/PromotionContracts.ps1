#Requires -Version 7.0

Set-StrictMode -Version Latest

function ConvertTo-PromotionCanonicalNode {
    param([AllowNull()][object]$Value)

    if ($null -eq $Value) { return $null }
    if ($Value -is [string] -or $Value -is [ValueType]) { return $Value }
    if ($Value -is [Collections.IDictionary]) {
        $Result = [ordered]@{}
        foreach ($Key in @($Value.Keys | ForEach-Object { [string]$_ } | Sort-Object)) {
            $Result[$Key] = ConvertTo-PromotionCanonicalNode $Value[$Key]
        }
        return $Result
    }
    if ($Value -is [Management.Automation.PSCustomObject]) {
        $Result = [ordered]@{}
        foreach ($Property in @($Value.PSObject.Properties | Sort-Object Name)) {
            $Result[$Property.Name] = ConvertTo-PromotionCanonicalNode $Property.Value
        }
        return $Result
    }
    if ($Value -is [Collections.IEnumerable]) {
        $Items = [Collections.Generic.List[object]]::new()
        foreach ($Item in $Value) {
            $Items.Add((ConvertTo-PromotionCanonicalNode $Item))
        }
        return ,([object[]]$Items.ToArray())
    }
    throw "Unsupported promotion canonicalization type '$($Value.GetType().FullName)'."
}

function Get-PromotionTextSha256 {
    param([Parameter(Mandatory = $true)][AllowEmptyString()][string]$Text)

    $Bytes = [Text.UTF8Encoding]::new($false).GetBytes(
        $Text.Replace("`r`n", "`n").Replace("`r", "`n")
    )
    return [Convert]::ToHexString(
        [Security.Cryptography.SHA256]::HashData($Bytes)
    ).ToLowerInvariant()
}

function Get-PromotionPreparationSha256 {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][object]$Manifest)

    $Required = @(
        'schemaVersion', 'storySlug', 'promotionDate', 'preparedAt',
        'authorization', 'stewardship', 'authority', 'bundle',
        'deltaInventory', 'deltaDispositions', 'universeChanges', 'retcon'
    )
    $IsDictionary = $Manifest -is [Collections.IDictionary]
    $Properties = if ($IsDictionary) {
        @($Manifest.Keys | ForEach-Object { [string]$_ })
    }
    else {
        @($Manifest.PSObject.Properties.Name)
    }
    $Missing = @($Required | Where-Object { $_ -cnotin $Properties })
    if ($Missing.Count -gt 0) {
        throw "Promotion preparation is missing field(s): $($Missing -join ', ')."
    }
    $State = if ($IsDictionary) { $Manifest['state'] } else { $Manifest.state }
    if ($State -notin @('ready', 'completed')) {
        throw "A preparation digest requires ready/completed state, found '$State'."
    }
    $Projection = [ordered]@{}
    foreach ($Field in $Required) {
        $FieldValue = if ($IsDictionary) { $Manifest[$Field] } else { $Manifest.$Field }
        $Projection[$Field] = ConvertTo-PromotionCanonicalNode $FieldValue
    }
    $Canonical = $Projection | ConvertTo-Json -Depth 100 -Compress
    return Get-PromotionTextSha256 $Canonical
}

function Assert-PromotionPreparationSha256 {
    [CmdletBinding()]
    param([Parameter(Mandatory = $true)][object]$Manifest)

    if ([string]$Manifest.preparationSha256 -cnotmatch '^[a-f0-9]{64}$') {
        throw 'promotion.json preparationSha256 is missing or malformed.'
    }
    $Expected = Get-PromotionPreparationSha256 $Manifest
    if ([string]$Manifest.preparationSha256 -cne $Expected) {
        throw 'promotion.json preparationSha256 does not match its immutable preparation fields.'
    }
    return $Expected
}
