# Xuất DOCX -> PDF bằng Microsoft Word, cập nhật mục lục và số trang.   [TV4]
# Dùng: powershell -File docs/tv4/export_pdf.ps1 -Docx docs/tv4/BaoCao_DoAn_BigData.docx
param([string]$Docx = "docs/tv4/BaoCao_DoAn_BigData.docx")
$ErrorActionPreference = 'Stop'
$src = (Resolve-Path $Docx).Path
$pdf = [System.IO.Path]::ChangeExtension($src, '.pdf')
$app = New-Object -ComObject Word.Application
$app.Visible = $false
$doc = $null
try {
  $doc = $app.Documents.Open($src, $false, $false, $false)
  $doc.Repaginate()
  if ($doc.TablesOfContents.Count -gt 0) { $doc.TablesOfContents.Item(1).Update() }
  $doc.Fields.Update() | Out-Null
  $doc.Repaginate()
  $doc.Save()
  $doc.ExportAsFixedFormat($pdf, 17)
  Write-Output "PDF: $pdf pages=$($doc.ComputeStatistics(2))"
} finally {
  if ($doc) { $doc.Close($false) }
  $app.Quit()
}
