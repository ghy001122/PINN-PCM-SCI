param(
    [string]$Root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
)

$ErrorActionPreference = 'Stop'
$outputDir = $PSScriptRoot
$word = $null

function Set-StyleFont {
    param($Document, [int]$StyleId, [string]$FontName, [double]$Size, [bool]$Bold)
    try {
        $style = $Document.Styles.Item($StyleId)
        $style.Font.Name = $FontName
        $style.Font.NameAscii = $FontName
        $style.Font.NameFarEast = $FontName
        $style.Font.Size = $Size
        $style.Font.Bold = if ($Bold) { -1 } else { 0 }
        $style.Font.Color = 0
    } catch {
        # Built-in style names can vary by Office language. HTML formatting
        # remains the fallback if a localized style lookup is unavailable.
    }
}

function Format-Document {
    param($Document, [string]$DocumentTitle)

    foreach ($section in $Document.Sections) {
        $section.PageSetup.PaperSize = 2
        $section.PageSetup.Orientation = 0
        $section.PageSetup.TopMargin = $word.InchesToPoints(0.72)
        $section.PageSetup.BottomMargin = $word.InchesToPoints(0.72)
        $section.PageSetup.LeftMargin = $word.InchesToPoints(0.76)
        $section.PageSetup.RightMargin = $word.InchesToPoints(0.76)
        try {
            $footer = $section.Footers.Item(1)
            $footer.Range.Text = ''
            $footer.Range.ParagraphFormat.Alignment = 1
            $footer.Range.Font.Name = 'Times New Roman'
            $footer.Range.Font.Size = 8
            $null = $footer.PageNumbers.Add(1, $true)
        } catch {}
    }

    Set-StyleFont $Document -1 'Times New Roman' 10.5 $false
    Set-StyleFont $Document -2 'Times New Roman' 13 $true
    Set-StyleFont $Document -3 'Times New Roman' 11.5 $true
    Set-StyleFont $Document -63 'Times New Roman' 16 $true

    $firstText = $null
    $nonEmpty = @()
    foreach ($p in $Document.Paragraphs) {
        $text = ($p.Range.Text -replace "[\r\a]", '').Trim()
        if ($text.Length -gt 0) { $nonEmpty += $p }
    }
    if ($nonEmpty.Count -gt 0) {
        try { $nonEmpty[0].Style = -63 } catch {}
        $nonEmpty[0].Range.ParagraphFormat.Alignment = 1
        $nonEmpty[0].Range.Font.Color = 0
        $firstText = (($nonEmpty[0].Range.Text -replace "[\r\a]", '').Trim())
    }
    if ($nonEmpty.Count -gt 1) { $nonEmpty[1].Range.ParagraphFormat.Alignment = 1 }
    if ($nonEmpty.Count -gt 2 -and $nonEmpty[2].Range.Text -match 'Corresponding') {
        $nonEmpty[2].Range.ParagraphFormat.Alignment = 1
    }

    foreach ($p in $Document.Paragraphs) {
        $styleName = ''
        try { $styleName = [string]$p.Style.NameLocal } catch {}
        if ($styleName -match 'Heading|标题') {
            $p.Range.Font.Color = 0
            $p.Range.ParagraphFormat.KeepWithNext = -1
            $p.Range.ParagraphFormat.WidowControl = -1
        }
    }

    foreach ($table in $Document.Tables) {
        $table.Borders.Enable = 1
        $table.AllowAutoFit = -1
        try { $table.AutoFitBehavior(2) } catch {}
        $table.TopPadding = 3
        $table.BottomPadding = 3
        $table.LeftPadding = 4
        $table.RightPadding = 4
        $table.Range.Font.Name = 'Times New Roman'
        $table.Range.Font.Size = 8.5
        if ($table.Rows.Count -ge 1) {
            $header = $table.Rows.Item(1)
            $header.HeadingFormat = -1
            $header.Range.Font.Bold = -1
            $header.Range.Font.Color = 16777215
            $header.Shading.BackgroundPatternColor = 7944993
            $header.Range.ParagraphFormat.Alignment = 1
        }
        for ($r = 2; $r -le $table.Rows.Count; $r++) {
            if (($r % 2) -eq 0) {
                $table.Rows.Item($r).Shading.BackgroundPatternColor = 16119285
            }
        }
    }

    foreach ($shape in $Document.InlineShapes) {
        try {
            # Word imports HTML images as external links. Break each link so
            # the delivered DOCX remains complete on another computer.
            $link = $shape.LinkFormat
            if ($null -ne $link) {
                $link.SavePictureWithDocument = -1
                $link.BreakLink()
            }
            $shape.LockAspectRatio = -1
            $maxWidth = $word.InchesToPoints(6.75)
            if ($shape.Width -gt $maxWidth) { $shape.Width = $maxWidth }
        } catch {}
    }

    try {
        $Document.BuiltInDocumentProperties.Item('Title').Value = $DocumentTitle
        $Document.BuiltInDocumentProperties.Item('Author').Value = ''
        $Document.BuiltInDocumentProperties.Item('Company').Value = ''
    } catch {}
}

function Convert-HtmlToDocx {
    param([string]$HtmlName, [string]$DocxName, [string]$Title)
    $htmlPath = (Resolve-Path (Join-Path $outputDir $HtmlName)).Path
    $docxPath = Join-Path $outputDir $DocxName
    if (Test-Path -LiteralPath $docxPath) { Remove-Item -LiteralPath $docxPath }
    $doc = $word.Documents.Open($htmlPath, $false, $false, $false)
    try {
        Format-Document $doc $Title
        $doc.SaveAs2($docxPath, 16)
    } finally {
        $doc.Close(0)
        [System.Runtime.InteropServices.Marshal]::ReleaseComObject($doc) | Out-Null
    }
    if (!(Test-Path -LiteralPath $docxPath)) { throw "DOCX was not created: $docxPath" }
    return $docxPath
}

try {
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $manuscript = Convert-HtmlToDocx 'manuscript_condensed.html' 'PINN_PCM_Condensed_Manuscript.docx' 'Training Time Electrical Elimination in Physics Informed Electrothermal Phase Reconstruction'
    $supplement = Convert-HtmlToDocx 'supplement_condensed.html' 'PINN_PCM_Condensed_Supplement.docx' 'Supplementary Material'
    Write-Output $manuscript
    Write-Output $supplement
} finally {
    if ($word) {
        $word.Quit()
        [System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null
    }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}
