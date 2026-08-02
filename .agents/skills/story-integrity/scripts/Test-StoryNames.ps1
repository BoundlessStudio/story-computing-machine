#Requires -Version 7.0

[CmdletBinding()]
param(
    [ValidatePattern('^[a-z0-9]+(?:-[a-z0-9]+)*$')]
    [string]$Story,

    [ValidateSet('Auto', 'Plan', 'Final')]
    [string]$Phase = 'Auto',

    [ValidateSet('Text', 'Json')]
    [string]$OutputFormat = 'Text',

    [switch]$Strict,

    [switch]$SkipConfusable,

    [string]$ProjectRoot
)

$ErrorActionPreference = 'Stop'
$CheckerVersion = 'story-names/2'

function Get-Sha256ForText {
    param([Parameter(Mandatory = $true)][AllowNull()][AllowEmptyString()][string]$Text)

    if ($null -eq $Text) { $Text = '' }
    $Bytes = [System.Text.UTF8Encoding]::new($false).GetBytes($Text)
    $Hash = [System.Security.Cryptography.SHA256]::HashData($Bytes)
    return [Convert]::ToHexString($Hash).ToLowerInvariant()
}

function Get-Sha256ForFile {
    param([Parameter(Mandatory = $true)][string]$Path)

    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function ConvertFrom-MarkdownCell {
    param([Parameter(Mandatory = $true)][AllowEmptyString()][string]$Value)

    return ($Value.Trim() -replace '`', '').Trim()
}

function Split-MarkdownRow {
    param(
        [Parameter(Mandatory = $true)][string]$Line,
        [Parameter(Mandatory = $true)][int]$ExpectedCells,
        [Parameter(Mandatory = $true)][string]$Context
    )

    if ($Line -notmatch '^\s*\|.*\|\s*$') {
        throw "Malformed Markdown table row in ${Context}: $Line"
    }

    $Cells = @($Line.Trim().Trim('|').Split('|') | ForEach-Object { $_.Trim() })
    if ($Cells.Count -ne $ExpectedCells) {
        throw "Malformed Markdown table row in $Context (expected $ExpectedCells cells, found $($Cells.Count)): $Line"
    }

    return ,$Cells
}

function Get-MarkdownSection {
    param(
        [Parameter(Mandatory = $true)][string]$Content,
        [Parameter(Mandatory = $true)][string]$Heading
    )

    $Pattern = '(?ms)^##\s+' + [regex]::Escape($Heading) +
        '\s*\r?\n(.*?)(?=^##\s+|\z)'
    $Match = [regex]::Match($Content, $Pattern)
    if (-not $Match.Success) {
        return $null
    }

    return $Match.Groups[1].Value.Trim()
}

function Test-SourceReferencesStory {
    param(
        [Parameter(Mandatory = $true)][string]$Source,
        [Parameter(Mandatory = $true)][string]$Slug
    )

    $CodeReferences = @([regex]::Matches($Source, '`([^`]+)`') |
        ForEach-Object { $_.Groups[1].Value.Trim() })
    if ($CodeReferences.Count -gt 0) {
        return $CodeReferences -contains $Slug
    }

    $Pattern = '(?i)(?<![a-z0-9-])' + [regex]::Escape($Slug) +
        '(?![a-z0-9-])'
    return [regex]::IsMatch($Source, $Pattern)
}

function Normalize-NameForm {
    param([Parameter(Mandatory = $true)][string]$Form)

    return (($Form.Normalize([Text.NormalizationForm]::FormKC)).Trim() -replace
        '\s+', ' ').ToLowerInvariant()
}

function Get-OrdinalSortedUniqueStrings {
    param(
        [Parameter(Mandatory = $true)]
        [AllowEmptyCollection()]
        [AllowEmptyString()]
        [string[]]$Values
    )

    $Unique = [System.Collections.Generic.HashSet[string]]::new(
        [StringComparer]::Ordinal
    )
    foreach ($Value in $Values) { $null = $Unique.Add($Value) }
    [string[]]$Sorted = @($Unique)
    [Array]::Sort($Sorted, [StringComparer]::Ordinal)
    return $Sorted
}

function Get-ConfusableKey {
    param([Parameter(Mandatory = $true)][string]$Form)

    $Normalized = Normalize-NameForm $Form
    $Normalized = $Normalized.Replace('0', 'o')
    return ($Normalized -replace '[^\p{L}\p{N}]', '')
}

function Get-ReversalKey {
    param([Parameter(Mandatory = $true)][string]$Form)

    $Parts = @((Normalize-NameForm $Form) -split '[\s,]+' |
        Where-Object { $_ })
    if ($Parts.Count -lt 2) {
        return $null
    }

    [array]::Reverse($Parts)
    return $Parts -join ' '
}

function Get-LevenshteinDistance {
    param(
        [Parameter(Mandatory = $true)][string]$Left,
        [Parameter(Mandatory = $true)][string]$Right
    )

    if ($Left.Length -eq 0) { return $Right.Length }
    if ($Right.Length -eq 0) { return $Left.Length }

    $Previous = [int[]]::new($Right.Length + 1)
    $Current = [int[]]::new($Right.Length + 1)
    for ($Column = 0; $Column -le $Right.Length; $Column++) {
        $Previous[$Column] = $Column
    }

    for ($Row = 1; $Row -le $Left.Length; $Row++) {
        $Current[0] = $Row
        for ($Column = 1; $Column -le $Right.Length; $Column++) {
            $Cost = if ($Left[$Row - 1] -ceq $Right[$Column - 1]) { 0 } else { 1 }
            $Current[$Column] = [Math]::Min(
                [Math]::Min($Current[$Column - 1] + 1, $Previous[$Column] + 1),
                $Previous[$Column - 1] + $Cost
            )
        }

        $Swap = $Previous
        $Previous = $Current
        $Current = $Swap
    }

    return $Previous[$Right.Length]
}

function Test-FormInProse {
    param(
        [Parameter(Mandatory = $true)][string]$Prose,
        [Parameter(Mandatory = $true)][string]$Form
    )

    $EscapedForm = [regex]::Escape($Form) -replace '\\\s', '\s+'
    $Pattern = '(?<![\p{L}\p{N}])' + $EscapedForm +
        '(?![\p{L}\p{N}])'
    return [regex]::IsMatch(
        $Prose,
        $Pattern,
        [Text.RegularExpressions.RegexOptions]::CultureInvariant -bor
            [Text.RegularExpressions.RegexOptions]::IgnoreCase
    )
}

function Test-FormUsedIndependently {
    param(
        [Parameter(Mandatory = $true)][string]$Prose,
        [Parameter(Mandatory = $true)][string]$Form,
        [Parameter(Mandatory = $true)][AllowEmptyCollection()][string[]]$InventoryForms
    )

    $EscapedForm = [regex]::Escape($Form) -replace '\\\s', '\s+'
    $Pattern = '(?<![\p{L}\p{N}])' + $EscapedForm +
        '(?![\p{L}\p{N}])'
    $Matches = @([regex]::Matches(
        $Prose,
        $Pattern,
        [Text.RegularExpressions.RegexOptions]::CultureInvariant -bor
            [Text.RegularExpressions.RegexOptions]::IgnoreCase
    ))
    foreach ($Match in $Matches) {
        $CoveredByLongerInventoryForm = $false
        foreach ($InventoryForm in $InventoryForms) {
            if ($InventoryForm.Length -le $Form.Length) { continue }
            $EscapedInventoryForm = [regex]::Escape($InventoryForm) -replace '\\\s', '\s+'
            $LongPattern = '(?<![\p{L}\p{N}])' + $EscapedInventoryForm +
                '(?![\p{L}\p{N}])'
            foreach ($LongMatch in [regex]::Matches(
                $Prose,
                $LongPattern,
                [Text.RegularExpressions.RegexOptions]::CultureInvariant -bor
                    [Text.RegularExpressions.RegexOptions]::IgnoreCase
            )) {
                if ($LongMatch.Index -le $Match.Index -and
                    ($LongMatch.Index + $LongMatch.Length) -ge ($Match.Index + $Match.Length)) {
                    $CoveredByLongerInventoryForm = $true
                    break
                }
            }
            if ($CoveredByLongerInventoryForm) { break }
        }
        if (-not $CoveredByLongerInventoryForm) { return $true }
    }
    return $false
}

function Get-RegistryRows {
    param([Parameter(Mandatory = $true)][string]$Path)

    $Lines = @(Get-Content -LiteralPath $Path)
    $Starts = @($Lines | Select-String -SimpleMatch '<!-- registry:start -->')
    $Ends = @($Lines | Select-String -SimpleMatch '<!-- registry:end -->')
    if ($Starts.Count -ne 1 -or $Ends.Count -ne 1) {
        throw 'Name registry must contain exactly one start marker and one end marker.'
    }

    $Start = $Starts[0].LineNumber - 1
    $End = $Ends[0].LineNumber - 1
    if ($End -le $Start + 2) {
        throw 'Name registry markers are out of order or the registry table is empty.'
    }

    $Rows = [System.Collections.Generic.List[object]]::new()
    $HeaderSeen = $false
    $SeparatorSeen = $false
    for ($Index = $Start + 1; $Index -lt $End; $Index++) {
        $Line = $Lines[$Index]
        if ([string]::IsNullOrWhiteSpace($Line)) { continue }
        if ($Line -notmatch '^\s*\|') {
            throw "Unexpected non-table content inside registry markers at line $($Index + 1): $Line"
        }

        $Cells = Split-MarkdownRow -Line $Line -ExpectedCells 6 -Context "registry line $($Index + 1)"
        if ($Cells[0] -eq 'Character / entity') {
            if ($HeaderSeen -or $Index -ne $Start + 1) {
                throw "Unexpected or duplicate registry header at line $($Index + 1)."
            }
            $HeaderSeen = $true
            continue
        }
        if (@($Cells | Where-Object { $_ -notmatch '^:?-{3,}:?$' }).Count -eq 0) {
            if (-not $HeaderSeen -or $SeparatorSeen) {
                throw "Unexpected or duplicate registry separator at line $($Index + 1)."
            }
            $SeparatorSeen = $true
            continue
        }
        if (-not $HeaderSeen -or -not $SeparatorSeen) {
            throw "Registry data appears before its header and separator at line $($Index + 1)."
        }

        $Character = ConvertFrom-MarkdownCell $Cells[0]
        $Forms = @((ConvertFrom-MarkdownCell $Cells[1]).Split(';') |
            ForEach-Object { $_.Trim() } | Where-Object { $_ })
        $Source = $Cells[2].Trim()
        $State = (ConvertFrom-MarkdownCell $Cells[3]).ToLowerInvariant()
        $ReuseStatus = (ConvertFrom-MarkdownCell $Cells[4]).ToLowerInvariant()
        $Rationale = ConvertFrom-MarkdownCell $Cells[5]
        if (-not $Character -or $Forms.Count -eq 0 -or
            -not (ConvertFrom-MarkdownCell $Source)) {
            throw "Registry row has a blank required field at line $($Index + 1): $Line"
        }

        $AllowedStates = @(
            'in-progress', 'candidate', 'final', 'canon', 'abandoned', 'released'
        )
        if ($State -notin $AllowedStates) {
            throw "Invalid registry state '$State' for '$Character' at line $($Index + 1)."
        }
        if ($ReuseStatus -notin @('unique', 'deliberate', 'unresolved')) {
            throw "Invalid reuse status '$ReuseStatus' for '$Character' at line $($Index + 1)."
        }
        if ($ReuseStatus -in @('deliberate', 'unresolved') -and
            $Rationale -in @('', '-', '—')) {
            throw "Registry row '$Character' requires a reuse rationale at line $($Index + 1)."
        }

        $CanonicalSource = (ConvertFrom-MarkdownCell $Source).ToLowerInvariant()
        $CanonicalCharacter = Normalize-NameForm $Character
        $CanonicalForms = @(Get-OrdinalSortedUniqueStrings -Values @(
            $Forms | ForEach-Object { Normalize-NameForm $_ }
        ))
        $IdentityKey = Get-Sha256ForText (
            "registry-identity-v1`n$CanonicalSource`n$CanonicalCharacter`n" +
            ($CanonicalForms -join "`n")
        )
        $Rows.Add([pscustomobject]@{
            IdentityKey = $IdentityKey
            Character = $Character
            Forms = $Forms
            Source = $Source
            State = $State
            ReuseStatus = $ReuseStatus
            Rationale = $Rationale
            LineNumber = $Index + 1
        })
    }

    if (-not $HeaderSeen -or -not $SeparatorSeen -or $Rows.Count -eq 0) {
        throw 'Name registry must contain one valid header, separator, and at least one data row.'
    }
    return @($Rows)
}

function Get-PlanInventory {
    param([Parameter(Mandatory = $true)][string]$Content)

    $Section = Get-MarkdownSection -Content $Content -Heading 'Name check'
    if ($null -eq $Section) {
        throw "02-story-plan.md is missing the 'Name check' section."
    }
    $WithoutComments = [regex]::Replace($Section, '(?ms)<!--.*?-->', '').Trim()
    if ($WithoutComments -match '^None\.?$') { return @() }

    $Lines = @($WithoutComments -split '\r?\n' |
        Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
    $Rows = [System.Collections.Generic.List[object]]::new()
    $HeaderSeen = $false
    $SeparatorSeen = $false
    foreach ($Line in $Lines) {
        if ($Line -notmatch '^\s*\|') {
            throw "Unexpected content in plan Name check table: $Line"
        }

        $Cells = Split-MarkdownRow -Line $Line -ExpectedCells 4 -Context '02-story-plan.md Name check'
        if ($Cells[0] -eq 'Character/entity') {
            if ($HeaderSeen) { throw 'Duplicate plan Name check header.' }
            $ExpectedHeader = @(
                'Character/entity',
                'Reserved forms used in prose',
                'Registry result',
                'Reuse rationale and reader disambiguation'
            )
            for ($CellIndex = 0; $CellIndex -lt $ExpectedHeader.Count; $CellIndex++) {
                if ($Cells[$CellIndex] -cne $ExpectedHeader[$CellIndex]) {
                    throw (
                        "Plan Name check column $($CellIndex + 1) must be " +
                        "'$($ExpectedHeader[$CellIndex])'."
                    )
                }
            }
            $HeaderSeen = $true
            continue
        }
        if (@($Cells | Where-Object { $_ -notmatch '^:?-{3,}:?$' }).Count -eq 0) {
            if (-not $HeaderSeen -or $SeparatorSeen) {
                throw 'Invalid plan Name check separator.'
            }
            $SeparatorSeen = $true
            continue
        }
        if (-not $HeaderSeen -or -not $SeparatorSeen) {
            throw 'Plan Name check data appears before its header and separator.'
        }

        $Character = ConvertFrom-MarkdownCell $Cells[0]
        $Forms = @((ConvertFrom-MarkdownCell $Cells[1]).Split(';') |
            ForEach-Object { $_.Trim() } | Where-Object { $_ })
        $RegistryResult = ConvertFrom-MarkdownCell $Cells[2]
        $ReuseRationale = ConvertFrom-MarkdownCell $Cells[3]
        if (-not $Character -or $Forms.Count -eq 0 -or
            $RegistryResult -in @('', '-', '—') -or
            $ReuseRationale -in @('', '-', '—')) {
            throw "Plan Name check row must populate all four columns: $Line"
        }
        $CombinedReuseText = "$RegistryResult`n$ReuseRationale"
        $ReuseStatus = if ($RegistryResult -match
            '(?i)\bunresolved\b|\bpending\b.{0,40}\bcollision\b|\bcollision\b.{0,40}\bpending\b') {
            'unresolved'
        }
        elseif ($CombinedReuseText -match '(?i)\bdeliberate(?:ly)?\b') {
            'deliberate'
        }
        else {
            'unique'
        }
        $Rows.Add([pscustomobject]@{
            Character = $Character
            Forms = $Forms
            RegistryResult = $RegistryResult
            ReuseRationale = $ReuseRationale
            ReuseStatus = $ReuseStatus
        })
    }

    if (-not $HeaderSeen -or -not $SeparatorSeen) {
        throw 'Plan Name check is not a valid four-column table.'
    }
    return @($Rows)
}

function Get-FinalInventory {
    param([Parameter(Mandatory = $true)][string]$Content)

    $Section = Get-MarkdownSection -Content $Content -Heading 'Final character-facing name inventory'
    if ($null -eq $Section) {
        throw "06-canon-delta.md is missing the 'Final character-facing name inventory' section."
    }
    $WithoutComments = [regex]::Replace($Section, '(?ms)<!--.*?-->', '').Trim()
    if ($WithoutComments -match '^None\.?$') { return @() }

    $Rows = [System.Collections.Generic.List[object]]::new()
    foreach ($Line in @($WithoutComments -split '\r?\n' |
        Where-Object { -not [string]::IsNullOrWhiteSpace($_) })) {
        $Match = [regex]::Match(
            $Line,
            '^-\s+\*\*(.+?)\*\*\s+(?:—|--|-)\s+Reserved forms:\s+(.+?)\s*$'
        )
        if (-not $Match.Success) {
            throw "Malformed final name inventory row: $Line"
        }

        $Character = $Match.Groups[1].Value.Trim().TrimEnd(':')
        $Forms = @([regex]::Matches($Match.Groups[2].Value, '`([^`]+)`') |
            ForEach-Object { $_.Groups[1].Value.Trim() } | Where-Object { $_ })
        if (-not $Character -or $Forms.Count -eq 0) {
            throw "Final name inventory row has a blank character or no backtick-delimited forms: $Line"
        }
        $Rows.Add([pscustomobject]@{ Character = $Character; Forms = $Forms })
    }
    return @($Rows)
}

function Get-DeltaDeclaredNames {
    param([Parameter(Mandatory = $true)][string]$Content)

    $Names = [System.Collections.Generic.List[string]]::new()
    foreach ($Heading in @('New characters or character facts')) {
        $Section = Get-MarkdownSection -Content $Content -Heading $Heading
        if ($null -eq $Section) { continue }
        foreach ($Match in [regex]::Matches($Section, '(?m)^-\s+\*\*(.+?)\*\*')) {
            $Label = $Match.Groups[1].Value.Trim().TrimEnd(':') -replace
                '\s+\(proposed\)$', ''
            foreach ($Name in @($Label -split '\s+/\s+' | Where-Object { $_ })) {
                $Names.Add($Name.Trim())
            }
        }
    }
    return @($Names | Sort-Object -Unique)
}

function Get-ProseAuditAllowlist {
    param([Parameter(Mandatory = $true)][string]$Content)

    $Section = Get-MarkdownSection -Content $Content -Heading 'Reviewed prose name-audit allowlist'
    if ($null -eq $Section) { return @() }
    $WithoutComments = [regex]::Replace($Section, '(?ms)<!--.*?-->', '').Trim()
    if ($WithoutComments -match '^None\.?$') { return @() }

    $Lines = @($WithoutComments -split '\r?\n' |
        Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
    $Rows = [System.Collections.Generic.List[object]]::new()
    $HeaderSeen = $false
    $SeparatorSeen = $false
    $AllowedClassifications = @(
        'common-word', 'formatting-artifact', 'non-character', 'organization',
        'place', 'quoted-text', 'setting-term'
    )
    foreach ($Line in $Lines) {
        $Cells = Split-MarkdownRow -Line $Line -ExpectedCells 3 -Context (
            '06-canon-delta.md Reviewed prose name-audit allowlist'
        )
        if ($Cells[0] -eq 'Candidate label') {
            if ($HeaderSeen) { throw 'Duplicate prose name-audit allowlist header.' }
            $ExpectedHeader = @('Candidate label', 'Classification', 'Review rationale')
            for ($CellIndex = 0; $CellIndex -lt $ExpectedHeader.Count; $CellIndex++) {
                if ($Cells[$CellIndex] -cne $ExpectedHeader[$CellIndex]) {
                    throw (
                        "Prose name-audit allowlist column $($CellIndex + 1) must be " +
                        "'$($ExpectedHeader[$CellIndex])'."
                    )
                }
            }
            $HeaderSeen = $true
            continue
        }
        if (@($Cells | Where-Object { $_ -notmatch '^:?-{3,}:?$' }).Count -eq 0) {
            if (-not $HeaderSeen -or $SeparatorSeen) {
                throw 'Invalid prose name-audit allowlist separator.'
            }
            $SeparatorSeen = $true
            continue
        }
        if (-not $HeaderSeen -or -not $SeparatorSeen) {
            throw 'Prose name-audit allowlist data appears before its header and separator.'
        }

        $Candidate = ConvertFrom-MarkdownCell $Cells[0]
        $Classification = (ConvertFrom-MarkdownCell $Cells[1]).ToLowerInvariant()
        $Rationale = ConvertFrom-MarkdownCell $Cells[2]
        if (-not $Candidate -or $Classification -notin $AllowedClassifications -or
            $Rationale -in @('', '-', '—')) {
            throw "Malformed prose name-audit allowlist row: $Line"
        }
        $Rows.Add([pscustomobject]@{
            Candidate = $Candidate
            Normalized = Normalize-NameForm $Candidate
            Classification = $Classification
            Rationale = $Rationale
        })
    }
    if (-not $HeaderSeen -or -not $SeparatorSeen) {
        throw 'Reviewed prose name-audit allowlist is not a valid three-column table.'
    }
    $Duplicate = @($Rows | Group-Object Normalized | Where-Object Count -gt 1)
    if ($Duplicate.Count -gt 0) {
        throw "Duplicate prose name-audit allowlist candidate '$($Duplicate[0].Group[0].Candidate)'."
    }
    return @($Rows)
}

function Remove-StoryMarkup {
    param([Parameter(Mandatory = $true)][string]$Content)

    $Result = [regex]::Replace($Content, '(?s)\A---\s*.*?\s*---\s*', '')
    $Result = [regex]::Replace($Result, '(?ms)<!--.*?-->', '')
    $Result = [regex]::Replace($Result, '(?m)^\s{0,3}#{1,6}\s+.*$', '')
    $Result = [regex]::Replace($Result, '(?m)^\s*```.*$', '')
    return $Result
}

function Remove-KnownNameForms {
    param(
        [Parameter(Mandatory = $true)][string]$Prose,
        [Parameter(Mandatory = $true)][AllowEmptyCollection()][string[]]$Forms
    )

    $Result = $Prose
    foreach ($Form in @($Forms | Sort-Object -Unique | Sort-Object Length -Descending)) {
        if ([string]::IsNullOrWhiteSpace($Form)) { continue }
        $EscapedForm = [regex]::Escape($Form) -replace '\\\s', '\s+'
        $Pattern = '(?<![\p{L}\p{N}])' + $EscapedForm + '(?![\p{L}\p{N}])'
        $Result = [regex]::Replace(
            $Result,
            $Pattern,
            ' ',
            [Text.RegularExpressions.RegexOptions]::CultureInvariant -bor
                [Text.RegularExpressions.RegexOptions]::IgnoreCase
        )
    }
    return $Result
}

function Get-ProseNameCandidates {
    param([Parameter(Mandatory = $true)][string]$Prose)

    $CommonWords = [System.Collections.Generic.HashSet[string]]::new(
        [StringComparer]::OrdinalIgnoreCase
    )
    foreach ($Word in @(
        'A', 'Across', 'After', 'Again', 'All', 'Along', 'Although', 'An', 'And',
        'Around', 'As', 'At', 'Before', 'Behind', 'Beyond', 'But', 'By', 'Down',
        'Even', 'Every', 'For', 'From', 'He', 'Her',
        'Here', 'His', 'How', 'However', 'I', 'If', 'In', 'Into', 'It', 'Its',
        'Inside', 'Later', 'Meanwhile', 'My', 'Near', 'Neither', 'No', 'Nor', 'Now', 'Of',
        'On', 'Once', 'Only', 'Or', 'Otherwise', 'Our', 'Over', 'She', 'So',
        'Outside', 'Still', 'That', 'The', 'Their', 'Then', 'There', 'These', 'They', 'This',
        'Those', 'Through', 'To', 'Under', 'Until', 'We', 'What', 'When', 'Where',
        'Whether', 'While', 'Who', 'Why', 'With', 'Without', 'Yes', 'Yet', 'You', 'Up',
        'Your'
    )) { $null = $CommonWords.Add($Word) }

    $TitleWords = @(
        'Adjudicator', 'Agent', 'Aunt', 'Captain', 'Chancellor', 'Chief', 'Colonel',
        'Commander', 'Councillor', 'Doctor', 'Dr', 'Duchess', 'Emperor', 'Examiner',
        'Father', 'General', 'Goddess', 'Host', 'Indexer', 'Instructor', 'King',
        'Lady', 'Lord', 'Majesty', 'Master', 'Minister', 'Mother', 'Mr', 'Mrs', 'Ms',
        'Officer', 'Prince', 'Princess', 'Professor', 'Queen', 'Saint', 'Sergeant',
        'Sister', 'Vicar', 'Warden'
    )
    $CapitalToken = '(?:(?:Dr|Mr|Mrs|Ms|St|[A-Z])\.|@?[A-Z][\p{L}\p{M}\p{N}\u2019''-]*)'
    $CandidatePattern = '(?<![\p{L}\p{N}@])' + $CapitalToken +
        '(?:[ \t]+(?:(?:of|the|and|de|da|van|von)|' + $CapitalToken + ')){0,5}'
    $Observed = [System.Collections.Generic.List[object]]::new()
    foreach ($Match in [regex]::Matches($Prose, $CandidatePattern)) {
        $Value = $Match.Value.Trim().TrimEnd('.', ',', ':', ';', '!', '?')
        $ValueIndex = $Match.Index
        $Tokens = @($Value -split '[ \t]+' | Where-Object { $_ })
        while ($Tokens.Count -gt 1 -and $CommonWords.Contains($Tokens[0])) {
            $Tokens = @($Tokens[1..($Tokens.Count - 1)])
        }
        if ($Tokens.Count -eq 0) { continue }
        $FirstTokenOffset = $Match.Value.IndexOf(
            $Tokens[0],
            [StringComparison]::Ordinal
        )
        if ($FirstTokenOffset -ge 0) {
            $ValueIndex = $Match.Index + $FirstTokenOffset
        }
        $Value = $Tokens -join ' '
        if ($Tokens.Count -eq 1 -and $CommonWords.Contains($Value)) { continue }
        if ($Value -match '^[IVXLCDM]+$' -or $Value -match '^\d+$') { continue }

        $BeforeStart = [Math]::Max(0, $ValueIndex - 48)
        $Before = $Prose.Substring($BeforeStart, $ValueIndex - $BeforeStart)
        $AfterStart = $Match.Index + $Match.Length
        $AfterLength = [Math]::Min(64, $Prose.Length - $AfterStart)
        $After = if ($AfterLength -gt 0) { $Prose.Substring($AfterStart, $AfterLength) } else { '' }
        $SentencePrefix = $Before -replace '(?s)^.*[.!?\u2026]\s*["''\u201d\u2019)]*', ''
        $AtSentenceStart = $SentencePrefix -match '^\s*["''\u201c\u2018(]*\s*$'
        $StrongBefore = $Before -match (
            '(?i)\b(?:answered|asked|called|greeted|heard|met|named|replied|' +
            'said|saw|thanked|told|warned|watched|known\s+as)\s+["''\u201c\u2018]*$'
        )
        $StrongAfter = $After -match (
            "^(?:['\u2019]s)?[,;:]?\s+(?i:agreed|answered|arrived|asked|breathed|" +
            'closed|crossed|did|entered|flinched|gave|had|held|laughed|leaned|' +
            'lifted|looked|lowered|nodded|opened|reached|refused|replied|returned|' +
            'said|sat|shouted|sighed|smiled|stood|stepped|took|turned|waited|' +
            'walked|was|watched|whispered|would)\b'
        )
        $HasTitle = $TitleWords -contains ($Tokens[0].TrimEnd('.'))
        $AllCapsLabel = $Tokens.Count -gt 1 -and $Value -cmatch '^[A-Z0-9@ .''\u2019-]+$'
        $Vocative = $After -match '^\s*,' -and $Before -match '["\u201c][^"\u201d]{0,80}$'
        $Observed.Add([pscustomobject]@{
            Form = $Value
            Normalized = Normalize-NameForm $Value
            Strong = [bool]($StrongBefore -or $StrongAfter -or $HasTitle -or
                $Vocative)
            AlwaysStrong = [bool]($StrongBefore -or $HasTitle -or $Vocative)
            AtSentenceStart = [bool]$AtSentenceStart
            AllCapsLabel = [bool]$AllCapsLabel
            TokenCount = $Tokens.Count
        })
    }

    $Candidates = [System.Collections.Generic.List[object]]::new()
    foreach ($Group in @($Observed | Group-Object Normalized)) {
        $Occurrences = @($Group.Group)
        $StrongOccurrences = @($Occurrences | Where-Object {
            $_.AlwaysStrong -or
                ($_.Strong -and -not $_.AllCapsLabel -and
                    (-not $_.AtSentenceStart -or $_.TokenCount -gt 1))
        })
        $RepeatedMixedPosition = $Occurrences.Count -ge 2 -and
            @($Occurrences | Where-Object {
                -not $_.AtSentenceStart -and -not $_.AllCapsLabel
            }).Count -gt 0
        if ($StrongOccurrences.Count -eq 0 -and -not $RepeatedMixedPosition) { continue }
        $Preferred = @($Occurrences | Sort-Object { $_.Form.Length } -Descending)[0]
        $Candidates.Add([pscustomobject]@{
            Form = $Preferred.Form
            Normalized = $Preferred.Normalized
            Occurrences = $Occurrences.Count
        })
    }
    return @($Candidates | Sort-Object Normalized)
}

function Get-CanonicalRegistryJson {
    param([Parameter(Mandatory = $true)][AllowEmptyCollection()][object[]]$RegistryRows)

    $Canonical = @($RegistryRows | Sort-Object IdentityKey | ForEach-Object {
        [ordered]@{
            identityKey = $_.IdentityKey
            character = $_.Character
            forms = @(Get-OrdinalSortedUniqueStrings -Values @($_.Forms))
            source = $_.Source
            # Lifecycle projections are validated separately.  Canonical name
            # receipts bind reservation identity, not a story's mutable stage.
            state = if ($_.State -ceq 'released') { 'released' } else { 'reserved' }
            reuseStatus = $_.ReuseStatus
            rationale = $_.Rationale
        }
    })
    return ConvertTo-Json -InputObject $Canonical -Depth 5 -Compress
}

function Test-MeaningfulReuseDocumentation {
    param([AllowNull()][AllowEmptyString()][string]$Text)

    return -not [string]::IsNullOrWhiteSpace($Text) -and
        $Text.Trim() -notin @('-', '—') -and $Text.Trim().Length -ge 12
}

function Add-PlanIdentityBindings {
    param(
        [Parameter(Mandatory = $true)][AllowEmptyCollection()][object[]]$PlanRows,
        [Parameter(Mandatory = $true)][AllowEmptyCollection()][object[]]$ScopedRegistryRows
    )

    foreach ($PlanRow in $PlanRows) {
        $PlanForms = @($PlanRow.Forms | ForEach-Object { Normalize-NameForm $_ })
        $Matches = @($ScopedRegistryRows | Where-Object {
            $RegistryForms = @($_.Forms | ForEach-Object { Normalize-NameForm $_ })
            @($PlanForms | Where-Object { $_ -notin $RegistryForms }).Count -eq 0
        })
        if ($Matches.Count -gt 1) {
            $CharacterMatches = @($Matches | Where-Object {
                (Normalize-NameForm $_.Character) -ceq
                    (Normalize-NameForm $PlanRow.Character)
            })
            if ($CharacterMatches.Count -eq 1) { $Matches = $CharacterMatches }
        }
        if ($Matches.Count -ne 1) {
            throw (
                "Plan Name check identity '$($PlanRow.Character)' must map to exactly one " +
                "story-scoped registry row; found $($Matches.Count)."
            )
        }
        $PlanRow | Add-Member -NotePropertyName RegistryIdentityKey -NotePropertyValue $Matches[0].IdentityKey -Force
    }
    $DuplicateBindings = @($PlanRows | Group-Object RegistryIdentityKey |
        Where-Object Count -gt 1)
    if ($DuplicateBindings.Count -gt 0) {
        throw (
            "Plan Name check contains multiple rows for registry identity " +
            "'$($DuplicateBindings[0].Group[0].Character)'."
        )
    }
    return @($PlanRows)
}

function Test-CollisionHasDeliberateDocumentation {
    param(
        [Parameter(Mandatory = $true)][object[]]$Uses,
        [Parameter(Mandatory = $true)][AllowEmptyCollection()][object[]]$PlanRows
    )

    foreach ($Use in $Uses) {
        if ($Use.ReuseStatus -ne 'deliberate' -or
            -not (Test-MeaningfulReuseDocumentation $Use.Rationale)) {
            return $false
        }
        if (-not $Use.TouchesStory) { continue }
        $MatchingPlanRows = @($PlanRows | Where-Object {
            $PlanNormalizedForms = @($_.Forms | ForEach-Object { Normalize-NameForm $_ })
            $_.RegistryIdentityKey -ceq $Use.IdentityKey -and
                $PlanNormalizedForms -contains $Use.Normalized
        })
        if ($MatchingPlanRows.Count -ne 1 -or
            $MatchingPlanRows[0].ReuseStatus -ne 'deliberate' -or
            -not (Test-MeaningfulReuseDocumentation $MatchingPlanRows[0].ReuseRationale)) {
            return $false
        }
    }
    return $true
}

if ([string]::IsNullOrWhiteSpace($ProjectRoot)) {
    $ProjectRoot = (Resolve-Path -LiteralPath (
        Join-Path $PSScriptRoot '../../../..'
    )).Path
}
else {
    $ProjectRoot = (Resolve-Path -LiteralPath $ProjectRoot).Path
}

$RegistryPath = Join-Path $ProjectRoot 'stories/NAMES.md'
if (-not (Test-Path -LiteralPath $RegistryPath -PathType Leaf)) {
    throw "Name registry not found: $RegistryPath"
}

$Rows = @(Get-RegistryRows -Path $RegistryPath)
$Failures = [System.Collections.Generic.List[string]]::new()
$Warnings = [System.Collections.Generic.List[string]]::new()
$ScopedRows = @()
$StoryMetadata = $null
$StoryDirectory = $null
$ArtifactHash = $null
$PlanHash = $null
$StoryHash = $null
$DeltaHash = $null

if ($Story -and $SkipConfusable) {
    $Failures.Add(
        '-SkipConfusable is not permitted for a story-scoped name gate.'
    )
}

if ($Story) {
    $StoryDirectory = Join-Path $ProjectRoot "stories/$Story"
    if (-not (Test-Path -LiteralPath $StoryDirectory -PathType Container)) {
        throw "Story directory not found: $StoryDirectory"
    }
    $MetadataPath = Join-Path $StoryDirectory 'story.json'
    if (-not (Test-Path -LiteralPath $MetadataPath -PathType Leaf)) {
        throw "Story metadata not found: $MetadataPath"
    }
    try {
        $StoryMetadata = Get-Content -LiteralPath $MetadataPath -Raw | ConvertFrom-Json
    }
    catch {
        throw "Invalid story metadata JSON: $($_.Exception.Message)"
    }
    if ($StoryMetadata.slug -cne $Story) {
        $Failures.Add("story.json slug '$($StoryMetadata.slug)' does not match '$Story'.")
    }

    $ScopedRows = @($Rows | Where-Object {
        Test-SourceReferencesStory -Source $_.Source -Slug $Story
    })
    $ExpectedState = if ($StoryMetadata.canon -eq $true) {
        'canon'
    }
    else {
        [string]$StoryMetadata.status
    }
    foreach ($Row in $ScopedRows) {
        $StateMatches = $Row.State -eq $ExpectedState
        if (-not $StateMatches) {
            $Failures.Add(
                "Registry state '$($Row.State)' for '$($Row.Character)' does not match story state '$ExpectedState'."
            )
        }
    }
}

$Inventory = @()
$PlanInventory = @()
$Allowlist = @()
$ProseCandidates = @()
if ($Story) {
    if ($Phase -eq 'Auto') {
        $Status = [string]$StoryMetadata.status
        $Stage = [string]$StoryMetadata.stage
        if (($Status -eq 'candidate' -and $Stage -eq 'candidate') -or
            ($Status -eq 'final' -and $Stage -eq 'final') -or
            ($Status -eq 'abandoned' -and $Stage -eq 'abandoned') -or
            ($Status -eq 'in-progress' -and $Stage -eq 'final-review')) {
            $Phase = 'Final'
        }
        elseif ($Status -eq 'in-progress' -and $Stage -in @(
            'prompt', 'canon-research', 'planning', 'drafting', 'draft-review',
            'final-edit'
        )) {
            $Phase = 'Plan'
        }
        else {
            $Failures.Add(
                "Cannot infer a name-check phase from invalid lifecycle state status='$Status', stage='$Stage'."
            )
            $Phase = 'Plan'
        }
    }

    if ($Phase -eq 'Plan') {
        $PlanPath = Join-Path $StoryDirectory '02-story-plan.md'
        if (-not (Test-Path -LiteralPath $PlanPath -PathType Leaf)) {
            $Failures.Add('02-story-plan.md is required for a plan name check.')
        }
        else {
            $PlanHash = Get-Sha256ForFile $PlanPath
            $ArtifactHash = $PlanHash
            try {
                $PlanInventory = @(Get-PlanInventory -Content (
                    Get-Content -LiteralPath $PlanPath -Raw
                ))
                $PlanInventory = @(Add-PlanIdentityBindings -PlanRows $PlanInventory -ScopedRegistryRows $ScopedRows)
                $Inventory = @($PlanInventory)
            }
            catch { $Failures.Add($_.Exception.Message) }
        }
    }
    else {
        $FinalPath = Join-Path $StoryDirectory '05-story.md'
        $DeltaPath = Join-Path $StoryDirectory '06-canon-delta.md'
        if (-not (Test-Path -LiteralPath $FinalPath -PathType Leaf)) {
            $Failures.Add('05-story.md is required for a final name check.')
        }
        if (-not (Test-Path -LiteralPath $DeltaPath -PathType Leaf)) {
            $Failures.Add('06-canon-delta.md is required for a final name check.')
        }
        if ((Test-Path -LiteralPath $FinalPath -PathType Leaf) -and
            (Test-Path -LiteralPath $DeltaPath -PathType Leaf)) {
            $StoryHash = Get-Sha256ForFile $FinalPath
            $DeltaHash = Get-Sha256ForFile $DeltaPath
            $ArtifactHash = Get-Sha256ForText "$StoryHash`n$DeltaHash"
            $FinalContent = Get-Content -LiteralPath $FinalPath -Raw
            $DeltaContent = Get-Content -LiteralPath $DeltaPath -Raw
            try {
                $Inventory = @(Get-FinalInventory -Content $DeltaContent)
                $DeclaredNames = @(Get-DeltaDeclaredNames -Content $DeltaContent)
                $Allowlist = @(Get-ProseAuditAllowlist -Content $DeltaContent)
            }
            catch {
                $Failures.Add($_.Exception.Message)
                $DeclaredNames = @()
            }

            $Prose = Remove-StoryMarkup $FinalContent
            $InventoryForms = @($Inventory | ForEach-Object Forms | ForEach-Object {
                Normalize-NameForm $_
            } | Sort-Object -Unique)
            $InventoryRawForms = @($Inventory | ForEach-Object Forms | Sort-Object -Unique)
            foreach ($Item in $Inventory) {
                foreach ($Form in $Item.Forms) {
                    if (-not (Test-FormInProse -Prose $Prose -Form $Form)) {
                        $Failures.Add("Final inventory form '$Form' does not appear in 05-story.md prose.")
                    }
                }
            }
            foreach ($Row in $ScopedRows) {
                foreach ($Form in $Row.Forms) {
                    if ((Test-FormUsedIndependently -Prose $Prose -Form $Form -InventoryForms $InventoryRawForms) -and
                        (Normalize-NameForm $Form) -notin $InventoryForms) {
                        $Failures.Add("Prose uses registered form '$Form', but the final name inventory omits it.")
                    }
                }
            }

            $RegisteredLabels = @($ScopedRows | ForEach-Object {
                @($_.Character) + @($_.Forms)
            } | ForEach-Object {
                Normalize-NameForm $_
            } | Sort-Object -Unique)
            foreach ($Name in $DeclaredNames) {
                $NormalizedName = Normalize-NameForm $Name
                if ($NormalizedName -notin $RegisteredLabels) {
                    $ProperTokens = @([regex]::Matches(
                        $Name,
                        '(?<![\p{L}\p{N}])[A-Z][\p{L}\p{M}\p{N}\u2019''-]*'
                    ) | ForEach-Object { $_.Value } | Where-Object {
                        $_ -notin @('A', 'An', 'The')
                    })
                    if ($ProperTokens.Count -gt 0) {
                        $Failures.Add("Delta-declared name '$Name' is not registered for exact story '$Story'.")
                    }
                }
            }

            $AuditProse = Remove-KnownNameForms -Prose $Prose -Forms $InventoryRawForms
            $ProseCandidates = @(Get-ProseNameCandidates -Prose $AuditProse)
            $AllowedCandidateKeys = @($Allowlist | ForEach-Object Normalized)
            foreach ($Candidate in $ProseCandidates) {
                if ($Candidate.Normalized -notin $AllowedCandidateKeys) {
                    $Failures.Add(
                        "Prose-derived candidate name '$($Candidate.Form)' is omitted from the final " +
                        'name inventory/registry and the reviewed prose name-audit allowlist.'
                    )
                }
            }
            $CandidateKeys = @($ProseCandidates | ForEach-Object Normalized)
            foreach ($Allowed in $Allowlist) {
                if ($Allowed.Normalized -notin $CandidateKeys) {
                    $Warnings.Add(
                        "Reviewed prose name-audit allowlist entry '$($Allowed.Candidate)' " +
                        'was not produced by the conservative candidate extractor.'
                    )
                }
            }
        }
    }

    $ScopedForms = @($ScopedRows | ForEach-Object Forms | ForEach-Object {
        Normalize-NameForm $_
    } | Sort-Object -Unique)
    foreach ($Item in $Inventory) {
        foreach ($Form in $Item.Forms) {
            if ((Normalize-NameForm $Form) -notin $ScopedForms) {
                $Failures.Add("Inventory form '$Form' is not registered for exact story '$Story'.")
            }
        }
    }
    if ($Inventory.Count -eq 0 -and $ScopedRows.Count -gt 0) {
        $Failures.Add("$Phase name inventory says none, but '$Story' has scoped registry rows.")
    }
    if ($Phase -eq 'Plan') {
        $PlannedForms = @($Inventory | ForEach-Object Forms | ForEach-Object {
            Normalize-NameForm $_
        } | Sort-Object -Unique)
        foreach ($Row in $ScopedRows) {
            foreach ($Form in $Row.Forms) {
                if ((Normalize-NameForm $Form) -notin $PlannedForms) {
                    $Failures.Add("Registry form '$Form' is absent from the plan Name check inventory.")
                }
            }
        }
        foreach ($Item in $PlanInventory | Where-Object ReuseStatus -eq 'unresolved') {
            $Failures.Add(
                "Plan Name check leaves target reuse unresolved for '$($Item.Character)'."
            )
        }
    }
    foreach ($Row in $ScopedRows | Where-Object ReuseStatus -eq 'unresolved') {
        $Failures.Add("Registry reuse remains unresolved for target identity '$($Row.Character)'.")
    }
}

$ActiveRows = @($Rows | Where-Object State -ne 'released')
$FormUses = [System.Collections.Generic.List[object]]::new()
foreach ($Row in $ActiveRows) {
    foreach ($Form in $Row.Forms) {
        $FormUses.Add([pscustomobject]@{
            IdentityKey = $Row.IdentityKey
            Normalized = Normalize-NameForm $Form
            ConfusableKey = Get-ConfusableKey $Form
            ReversalKey = Get-ReversalKey $Form
            Form = $Form
            Character = $Row.Character
            Source = $Row.Source
            ReuseStatus = $Row.ReuseStatus
            Rationale = $Row.Rationale
            TouchesStory = if ($Story) {
                Test-SourceReferencesStory -Source $Row.Source -Slug $Story
            }
            else { $false }
        })
    }
}
$FormUses = @($FormUses | Sort-Object IdentityKey, Normalized, Form)

$Collisions = [System.Collections.Generic.List[object]]::new()
foreach ($Group in @($FormUses | Group-Object Normalized)) {
    $Uses = @($Group.Group)
    $DistinctIdentityKeys = @($Uses.IdentityKey | Sort-Object -Unique)
    if ($DistinctIdentityKeys.Count -lt 2) { continue }
    $Description = "Exact collision '$($Uses[0].Form)' => " +
        (($Uses | ForEach-Object { "$($_.Character) [$($_.Source)]" }) -join '; ')
    $Collisions.Add([pscustomobject]@{
        Kind = 'exact'
        Uses = $Uses
        Description = $Description
        TouchesStory = @($Uses | Where-Object TouchesStory).Count -gt 0
    })
}

$ReportedPairs = [System.Collections.Generic.HashSet[string]]::new()
for ($LeftIndex = 0; -not $SkipConfusable -and $LeftIndex -lt $FormUses.Count; $LeftIndex++) {
    $Left = $FormUses[$LeftIndex]
    for ($RightIndex = $LeftIndex + 1; $RightIndex -lt $FormUses.Count; $RightIndex++) {
        $Right = $FormUses[$RightIndex]
        if ($Left.IdentityKey -ceq $Right.IdentityKey -or
            $Left.Normalized -ceq $Right.Normalized) { continue }
        if ($Story -and -not $Left.TouchesStory -and -not $Right.TouchesStory) { continue }
        $PairParts = @(
            "$($Left.IdentityKey):$($Left.Normalized)",
            "$($Right.IdentityKey):$($Right.Normalized)"
        ) | Sort-Object
        $PairKey = $PairParts -join "`0"
        if (-not $ReportedPairs.Add($PairKey)) { continue }

        $Kind = $null
        if ($Left.ConfusableKey -eq $Right.ConfusableKey) {
            $Kind = 'punctuation/spacing-confusable'
        }
        elseif (($Left.ReversalKey -and $Left.ReversalKey -eq $Right.Normalized) -or
            ($Right.ReversalKey -and $Right.ReversalKey -eq $Left.Normalized)) {
            $Kind = 'reversed-form'
        }
        else {
            $MinimumLength = [Math]::Min($Left.ConfusableKey.Length, $Right.ConfusableKey.Length)
            if ($MinimumLength -ge 4) {
                $Threshold = if ($MinimumLength -ge 8) { 2 } else { 1 }
                $Distance = Get-LevenshteinDistance $Left.ConfusableKey $Right.ConfusableKey
                if ($Distance -le $Threshold) { $Kind = "close-spelling(distance $Distance)" }
            }
        }
        if ($Kind) {
            $Collisions.Add([pscustomobject]@{
                Kind = $Kind
                Uses = @($Left, $Right)
                Description = "$Kind '$($Left.Form)' [$($Left.Source)] vs '$($Right.Form)' [$($Right.Source)]"
                TouchesStory = [bool]($Left.TouchesStory -or $Right.TouchesStory)
            })
        }
    }
}

$TargetCollisions = @($Collisions | Where-Object TouchesStory)
if ($Story -and $TargetCollisions.Count -gt 0 -and $Phase -eq 'Final') {
    $PlanPath = Join-Path $StoryDirectory '02-story-plan.md'
    if (-not (Test-Path -LiteralPath $PlanPath -PathType Leaf)) {
        $Failures.Add('02-story-plan.md is required to document deliberate target name reuse.')
    }
    else {
        $PlanHash = Get-Sha256ForFile $PlanPath
        $ArtifactHash = Get-Sha256ForText "$StoryHash`n$DeltaHash`n$PlanHash"
        try {
            $PlanInventory = @(Get-PlanInventory -Content (
                Get-Content -LiteralPath $PlanPath -Raw
            ))
            $PlanInventory = @(Add-PlanIdentityBindings -PlanRows $PlanInventory -ScopedRegistryRows $ScopedRows)
        }
        catch { $Failures.Add($_.Exception.Message) }
    }
}

foreach ($Collision in $Collisions) {
    $Allowed = Test-CollisionHasDeliberateDocumentation -Uses $Collision.Uses -PlanRows $PlanInventory
    if ($Story -and $Collision.TouchesStory) {
        if (-not $Allowed) {
            $Failures.Add(
                "$($Collision.Description). Target-touching collisions require consistent " +
                'deliberate reuse documentation in both the plan and every registry identity.'
            )
        }
        else {
            $Warnings.Add("Documented deliberate $($Collision.Description)")
        }
    }
    elseif (-not $Story -and $Strict -and -not $Allowed) {
        $Failures.Add($Collision.Description)
    }
    else {
        $Warnings.Add($Collision.Description)
    }
}

$RowsToHash = if ($Story) { $ScopedRows } else { $Rows }
$ScopedCanonical = Get-CanonicalRegistryJson -RegistryRows $RowsToHash
$ScopedHash = Get-Sha256ForText -Text $ScopedCanonical
$ActiveCanonical = Get-CanonicalRegistryJson -RegistryRows $ActiveRows
$ActiveRegistryHash = Get-Sha256ForText -Text $ActiveCanonical

if ($Failures.Count -gt 0) {
    throw ("Name registry check failed:`n- " +
        (@($Failures | Sort-Object -Unique) -join "`n- "))
}

$SortedWarnings = @(Get-OrdinalSortedUniqueStrings -Values @($Warnings))
$WarningsHash = Get-Sha256ForText -Text (
    ConvertTo-Json -InputObject $SortedWarnings -Compress
)
$ReceiptId = if ($Story) {
    Get-Sha256ForText (
        "$CheckerVersion`n$Story`n$($Phase.ToLowerInvariant())`n" +
        "$ArtifactHash`n$ScopedHash`n$ActiveRegistryHash`n$WarningsHash"
    )
}
else {
    Get-Sha256ForText (
        "$CheckerVersion`nregistry`n$ScopedHash`n$ActiveRegistryHash`n$WarningsHash"
    )
}
$Result = [ordered]@{
    schemaVersion = 1
    checkerVersion = $CheckerVersion
    receiptId = $ReceiptId
    story = if ($Story) { $Story } else { $null }
    phase = if ($Story) { $Phase } else { 'Registry' }
    passed = $true
    checkedAt = [DateTimeOffset]::UtcNow.ToString('o')
    planSha256 = $PlanHash
    storySha256 = $StoryHash
    canonDeltaSha256 = $DeltaHash
    registryEntries = $Rows.Count
    activeRegistryEntries = $ActiveRows.Count
    reservedForms = $FormUses.Count
    scopedEntries = $ScopedRows.Count
    inventoryEntries = $Inventory.Count
    proseCandidateEntries = $ProseCandidates.Count
    proseAllowlistEntries = $Allowlist.Count
    scopedRegistrySha256 = $ScopedHash
    activeRegistrySha256 = $ActiveRegistryHash
    warnings = $SortedWarnings
}

if ($OutputFormat -eq 'Json') {
    Write-Output ($Result | ConvertTo-Json -Depth 6)
}
else {
    foreach ($Warning in $Result.warnings) { Write-Warning $Warning }
    $Scope = if ($Story) { "story '$Story' ($($Result.phase))" } else { 'global registry' }
    Write-Output (
        "Name registry check passed for {0}: {1} entries, {2} reserved forms, {3} scoped entries, {4} warning(s)." -f
        $Scope, $Rows.Count, $FormUses.Count, $ScopedRows.Count, $Result.warnings.Count
    )
}
