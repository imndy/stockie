# run_daily.ps1
# Chạy daily pipeline và push lên GitHub
# Được gọi bởi Windows Task Scheduler mỗi ngày lúc 07:30

$REPO = "C:\Users\dtran\OneDrive\Duy_Data\Trade\Stockie"
$VENV_PYTHON = "$REPO\.venv\Scripts\python.exe"
$SCRIPT = "$REPO\draft\analyze.py"
$LOG = "$REPO\run_daily.log"

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

# Force UTF-8 for Python stdout/stderr so Vietnamese text doesn't crash cp1252.
# PYTHONUTF8=1 enables Python's UTF-8 mode (equiv to python -Xutf8).
$env:PYTHONUTF8          = "1"
$env:PYTHONIOENCODING    = "utf-8"

# Ensure NativeCommandErrors (e.g. emoji in vnstock stderr) never abort the pipeline.
$ErrorActionPreference   = "Continue"

# Tell PowerShell to use UTF-8 when reading child-process output.
try { [Console]::InputEncoding  = [System.Text.Encoding]::UTF8 } catch {}
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}

Add-Content -Path $LOG -Value ""
Add-Content -Path $LOG -Value "===== $timestamp ====="

& $VENV_PYTHON $SCRIPT --mode daily 2>&1 | Tee-Object -FilePath $LOG -Append

if ($LASTEXITCODE -ne 0) {
    Add-Content -Path $LOG -Value "[ERROR] Python exited with code $LASTEXITCODE at $(Get-Date -Format 'HH:mm:ss')"
    exit $LASTEXITCODE
}
Add-Content -Path $LOG -Value "[OK] Pipeline hoàn tất lúc $(Get-Date -Format 'HH:mm:ss')"
