# Conversión local con Word oculto: fallback cuando el runtime no contiene LibreOffice.
param([string]$Only = '')
$ErrorActionPreference = 'Stop'
$workspacePath = (Get-Location).Path
$outputPath = Join-Path $workspacePath 'entrega_academica'
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
try {
    foreach ($file in (Get-ChildItem -LiteralPath $outputPath -Filter 'DOC_*.docx')) {
        if ($Only -and $file.BaseName -ne $Only) { continue }
        $document = $null
        try {
            $document = $word.Documents.Open($file.FullName, $false, $true, $false)
            $pdfPath = [System.IO.Path]::ChangeExtension($file.FullName, '.pdf')
            $document.ExportAsFixedFormat($pdfPath, 17)
            Write-Output "PDF generado: $($file.BaseName)"
        } finally {
            if ($null -ne $document) { $document.Close(0) }
        }
    }
} finally { $word.Quit() }
