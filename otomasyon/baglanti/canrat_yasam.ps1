$ErrorActionPreference='Stop'
function Get-CanRatInstances {
    $items = @(Get-Process -Name CANRat -ErrorAction SilentlyContinue)
    return @($items | ForEach-Object {
        [ordered]@{pid=$_.Id; start_ticks=$_.StartTime.ToUniversalTime().Ticks.ToString(); path=$_.Path; window=$_.MainWindowHandle.ToInt64()}
    })
}
function Confirm-CanRatIdentity($Process, $Identity, [string]$Exe) {
    $Process.Refresh()
    if ($Process.HasExited -or $Process.Id -ne $Identity.pid -or
        $Process.StartTime.ToUniversalTime().Ticks.ToString() -ne $Identity.start_ticks -or $Process.Path -ne $Exe) {
        throw 'PID/başlangıç zamanı/EXE sahiplik eşleştirmesi başarısız.'
    }
}
function Wait-CanRatWindow($Process, $Identity, [string]$Exe) {
    $timer=[Diagnostics.Stopwatch]::StartNew()
    do {
        Confirm-CanRatIdentity $Process $Identity $Exe
        $items=@(Get-CanRatInstances)
        if ($items.Count -ne 1 -or $items[0].pid -ne $Identity.pid) { throw 'Pencere beklenirken örnek sayısı/kimliği değişti.' }
        if ($Process.MainWindowHandle -ne 0) { return $Process.MainWindowHandle.ToInt64() }
        Start-Sleep -Milliseconds 200
    } while ($timer.ElapsedMilliseconds -lt 15000)
    throw 'Ana pencere 15 saniyede hazır olmadı.'
}
function Close-OwnedCanRat($Process, $Identity, [string]$Exe, [bool]$Owned) {
    if (-not $Owned) { throw 'Sahip olunmayan süreç kapatılamaz.' }
    Confirm-CanRatIdentity $Process $Identity $Exe
    $Process.Refresh()
    if ($Process.MainWindowHandle -eq 0) { throw 'Normal kapatma için ana pencere yok.' }
    $sent=$Process.CloseMainWindow()
    if (-not $sent) { throw 'CloseMainWindow isteği kabul edilmedi.' }
    if (-not $Process.WaitForExit(10000)) { throw 'Normal kapatma 10 saniyede tamamlanmadı; süreç zorla sonlandırılmadı.' }
    return [ordered]@{status='KAPANDI'; method='CloseMainWindow'; request_sent=$sent; exited=$true; exit_code=$Process.ExitCode}
}
