$Action = New-ScheduledTaskAction -Execute "C:\Users\magno\AppData\Local\Programs\Python\Python314\python.exe" -Argument "c:\Users\magno\OneDrive\Documentos\finance-etl-pipeline\src\main.py" -WorkingDirectory "c:\Users\magno\OneDrive\Documentos\finance-etl-pipeline"

$Trigger = New-ScheduledTaskTrigger -Daily -At 6pm

$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable

$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive

try {
    Register-ScheduledTask -TaskName "InfiosFinanceOS_DailyClosing" -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -Description "A pipeline that evaluates accounting revenue details against LATAM templates." -Force
    Write-Host "✅ Enterprise Task Scheduler Created: InfiosFinanceOS_DailyClosing will now automatically run at 18:00 every day using your local python, processing background compliance." -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to create scheduled task. Try invoking PowerShell as Administrator." -ForegroundColor Red
}
