# run_daily.ps1
# Chạy daily pipeline và push lên GitHub
# Được gọi bởi Windows Task Scheduler mỗi ngày lúc 07:30

$REPO = "C:\Users\dtran\OneDrive\Duy_Data\Trade\Stockie"
$VENV_PYTHON = "$REPO\.venv\Scripts\python.exe"
$SCRIPT = "$REPO\draft\analyze.py"
$LOG = "$REPO\run_daily.log"

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

Add-Content -Path $LOG -Value ""
Add-Content -Path $LOG -Value "===== $timestamp ====="

try {
    & $VENV_PYTHON $SCRIPT --mode daily 2>&1 | Tee-Object -FilePath $LOG -Append
    Add-Content -Path $LOG -Value "[OK] Pipeline hoàn tất lúc $(Get-Date -Format 'HH:mm:ss')"
} catch {
    Add-Content -Path $LOG -Value "[ERROR] $_"
    exit 1
}
