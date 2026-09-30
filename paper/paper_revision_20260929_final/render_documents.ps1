param([ValidateSet('manuscript','supplement','both')][string]$Document = 'both')
$ErrorActionPreference = 'Stop'
$paperRoot = $PSScriptRoot
$workspaceRoot = (Resolve-Path -LiteralPath (Join-Path $paperRoot '..\..')).Path
$renderer = Join-Path $workspaceRoot 'paper\advisor_review_20260924\render_with_word.ps1'
$names = if ($Document -eq 'both') { @('manuscript','supplement') } else { @($Document) }
foreach ($name in $names) {
    $docx = Join-Path $paperRoot ($name + '.docx')
    $renderRoot = Join-Path $paperRoot ('build\render-' + $name)
    & $renderer -DocxPath $docx -OutputDir $renderRoot | Out-Null
    if (!(Test-Path -LiteralPath (Join-Path $renderRoot ($name + '.pdf')))) { throw 'PDF export missing' }
    Copy-Item -LiteralPath (Join-Path $renderRoot ($name + '.pdf')) -Destination (Join-Path $paperRoot ($name + '.pdf')) -Force
    Write-Output ('Rendered ' + $name + ' for visual review')
}
