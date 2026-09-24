param(
    [Parameter(Mandatory=$true)][string]$DocxPath,
    [Parameter(Mandatory=$true)][string]$OutputDir
)

$ErrorActionPreference = 'Stop'
$docx = (Resolve-Path -LiteralPath $DocxPath).Path
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
$out = (Resolve-Path -LiteralPath $OutputDir).Path
$stem = [System.IO.Path]::GetFileNameWithoutExtension($docx)
$pdf = Join-Path $out ($stem + '.pdf')
if (Test-Path -LiteralPath $pdf) { Remove-Item -LiteralPath $pdf }

$word = $null
$doc = $null
try {
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $doc = $word.Documents.Open($docx, $false, $true, $false)
    $doc.ExportAsFixedFormat($pdf, 17)
} finally {
    if ($doc) {
        $doc.Close(0)
        [System.Runtime.InteropServices.Marshal]::ReleaseComObject($doc) | Out-Null
    }
    if ($word) {
        $word.Quit()
        [System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null
    }
}

$pdftoppm = 'C:\Users\CJ\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\poppler\Library\bin\pdftoppm.exe'
if (!(Test-Path -LiteralPath $pdftoppm)) { throw 'Bundled pdftoppm not found' }
& $pdftoppm -png -r 130 $pdf (Join-Path $out 'page')
if ($LASTEXITCODE -ne 0) { throw 'pdftoppm failed' }
Get-ChildItem -LiteralPath $out -Filter 'page-*.png' | Sort-Object Name | Select-Object FullName,Length
