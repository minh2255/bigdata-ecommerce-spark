"""Render with installed Microsoft Word, then packaged DOCX rasterizer/Poppler.

Windows has no bundled LibreOffice in this runtime. This explicit fallback
does not use a desktop LibreOffice or modify the managed renderer package.
Requires Microsoft Word and the runtime's pdf2image/Poppler dependencies.
"""
import importlib.util
import os
import subprocess
import sys
from pathlib import Path


input_path = Path(sys.argv[1]).resolve()
out = Path(sys.argv[2]).resolve()
out.mkdir(parents=True, exist_ok=True)
runtime = Path(sys.executable).parent.parent if Path(sys.executable).parent.name == "bin" else Path(sys.executable).parent
deps = runtime.parent
poppler = next((deps / "native/poppler").rglob("pdftoppm.exe")).parent
os.environ["PATH"] = str(poppler) + os.pathsep + os.environ["PATH"]
skill = Path("C:/Users/Khiem/.codex/plugins/cache/openai-primary-runtime/documents/26.1015.12040/skills/documents")
spec = importlib.util.spec_from_file_location("packaged_docx_renderer", skill / "render_docx.py")
renderer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(renderer)
script = out / "export_word_pdf.ps1"
script.write_text('''param([string]$SourcePath,[string]$PdfPath)
$ErrorActionPreference='Stop'
$app=New-Object -ComObject Word.Application
$own=($app.Documents.Count -eq 0)
$document=$null
try {
 if ($own) { $app.Visible=$false }
 $document=$app.Documents.Open($SourcePath,$false,$true,$false)
 $document.Repaginate()
 $document.ExportAsFixedFormat($PdfPath,17)
 Write-Output "Word PDF export succeeded"
} finally {
 if ($null -ne $document) { $document.Close($false); [void][System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($document) }
 if ($own) { $app.Quit() }
 [void][System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($app)
}
''', encoding="utf-8")


def word_pdf(doc_path, user_profile, convert_tmp_dir, stem, verbose=False):
    pdf = Path(convert_tmp_dir) / (stem + ".pdf")
    result = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script),
                             "-SourcePath", str(Path(doc_path).resolve()), "-PdfPath", str(pdf)],
                            capture_output=True, text=True, timeout=120)
    if result.returncode or not pdf.exists():
        raise RuntimeError(result.stdout + result.stderr)
    return str(pdf), result.stdout


renderer.convert_to_pdf = word_pdf
pages = renderer.rasterize(str(input_path), str(out), 115, verbose=False, emit_pdf=True)
print(f"Rendered {len(pages)} pages using Microsoft Word + packaged rasterize: {out}")
