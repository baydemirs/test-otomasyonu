param(
    [Parameter(Mandatory=$true)][string]$Journal,
    [Parameter(Mandatory=$true)][string]$Python,
    [ValidateSet('Auto','Existing','Closed')][string]$Expected='Auto'
)
$ErrorActionPreference='Stop'
[Console]::OutputEncoding=New-Object Text.UTF8Encoding($false)
. (Join-Path $PSScriptRoot '../../uygulama_baglantilari/canrat_yasam.ps1')
. (Join-Path $PSScriptRoot '../../uygulama_baglantilari/canrat_toggle.ps1')
$root=(Resolve-Path (Join-Path $PSScriptRoot '../..')).ProviderPath
$exe=(Resolve-Path (Join-Path $root 'hedef_uygulama/CANRAT_3min/CANRat.exe')).ProviderPath
$record=[ordered]@{schema_version=1; task='GOREV-006'; adapter='pywinauto'; expected=$Expected; before=@(); identity=$null; owned=$false; working_directory=(Split-Path $exe -Parent); start=[ordered]@{status='BASLATILMADI'}; test=[ordered]@{status='CALISTIRILMADI'}; close=[ordered]@{status='DENENMEDI'}; error=$null; cleanup_error=$null; result='HATA'; events=@()}
$target=$null; $tester=$null; $mutex=$null; $locked=$false
function Save-Life([string]$Phase) {
    $record.events += @{phase=$Phase;time_utc=[DateTime]::UtcNow.ToString('o')}
    $tmp=$Journal+'.tmp'
    [IO.File]::WriteAllText($tmp,($record|ConvertTo-Json -Depth 15),(New-Object Text.UTF8Encoding($false)))
    if ([IO.File]::Exists($Journal)) {[IO.File]::Replace($tmp,$Journal,($Journal+'.previous'))} else {[IO.File]::Move($tmp,$Journal)}
}
try {
    $mutex=New-Object Threading.Mutex($false,'Local\CANRAT_LIFECYCLE')
    try {$locked=$mutex.WaitOne(0)} catch [Threading.AbandonedMutexException] {$locked=$true}
    if (-not $locked) {throw 'Başka yaşam döngüsü koşusu etkin.'}
    $record.before=@(Get-CanRatInstances)
    Save-Life 'before'
    if ($record.before.Count -gt 1) {throw 'Birden fazla CANRat örneği var; seçim belirsiz.'}
    if ($Expected -eq 'Closed' -and $record.before.Count -ne 0) {throw 'Kapalı başlangıç bekleniyordu; mevcut uygulamaya dokunulmadı.'}
    if ($Expected -eq 'Existing' -and $record.before.Count -ne 1) {throw 'Önceden açık örnek bekleniyordu; uygulama başlatılmadı.'}
    if ($record.before.Count -eq 0) {
        $info=New-Object Diagnostics.ProcessStartInfo
        $info.FileName=$exe
        $info.WorkingDirectory=$record.working_directory
        $info.UseShellExecute=$false
        $record.start=[ordered]@{status='BASLATILIYOR';exe=$exe;working_directory=$info.WorkingDirectory}
        Save-Life 'launch_intent'
        $target=[Diagnostics.Process]::Start($info)
        $record.owned=$true
        $record.identity=@{pid=$target.Id;start_ticks=$target.StartTime.ToUniversalTime().Ticks.ToString();path=$exe}
        $record.start.status='BASLATILDI'
    } else {
        if ($record.before[0].path -ne $exe) {throw 'Açık örnek belirtilen EXE ile eşleşmiyor veya yolu okunamıyor.'}
        $target=Get-Process -Id $record.before[0].pid
        $record.identity=$record.before[0]
        $record.start=[ordered]@{status='MEVCUDA_BAGLANILDI';exe=$exe}
    }
    Save-Life 'identity'
    $record.start.window=Wait-CanRatWindow $target $record.identity $exe
    $record.start.window_ready=$true
    Save-Life 'window_ready'
    # Existing test retains its own collection guard, cleanup and time limits.
    $stdout=Join-Path (Split-Path $Journal -Parent) 'test-stdout.txt'
    $stderr=Join-Path (Split-Path $Journal -Parent) 'test-stderr.txt'
    $script=Join-Path $root 'tests/canrat_ui_002_pywinauto.py'
    $record.test=[ordered]@{status='CALISIYOR';command=@($Python,$script,'--mode','Exercise');stdout=$stdout;stderr=$stderr}
    Save-Life 'test_start'
    $testInfo=New-Object Diagnostics.ProcessStartInfo
    $testInfo.FileName=$Python
    $testInfo.Arguments='"'+$script+'" --mode Exercise'
    $testInfo.WorkingDirectory=$root
    $testInfo.UseShellExecute=$false
    $testInfo.CreateNoWindow=$true
    $testInfo.WindowStyle=[Diagnostics.ProcessWindowStyle]::Hidden
    $testInfo.RedirectStandardOutput=$true
    $testInfo.RedirectStandardError=$true
    $testInfo.EnvironmentVariables['CANRAT_EXPECTED_PID']=[string]$record.identity.pid
    $testInfo.EnvironmentVariables['CANRAT_EXPECTED_TICKS']=[string]$record.identity.start_ticks
    $testInfo.EnvironmentVariables['CANRAT_EXPECTED_EXE']=$exe
    $tester=New-Object Diagnostics.Process
    $tester.StartInfo=$testInfo
    if (-not $tester.Start()) {throw 'Test alt sureci baslatilamadi.'}
    $outTask=$tester.StandardOutput.ReadToEndAsync()
    $errTask=$tester.StandardError.ReadToEndAsync()
    if (-not $tester.WaitForExit(55000)) {throw 'Test 55 saniyede sonlanmadı; hedef kapatılmayacak.'}
    [IO.File]::WriteAllText($stdout,$outTask.Result,(New-Object Text.UTF8Encoding($false)))
    [IO.File]::WriteAllText($stderr,$errTask.Result,(New-Object Text.UTF8Encoding($false)))
    $record.test.exit_code=$tester.ExitCode
    $lines=Get-Content -LiteralPath $stdout -Encoding UTF8
    $jsonLine=@($lines | Where-Object {$_.StartsWith('{')})
    if ($jsonLine.Count -ne 1) {throw 'Tek test raporu okunamadı.'}
    $testReport=$jsonLine[0] | ConvertFrom-Json
    $record.test.report_path=$testReport.kanit_yolu
    $record.test.status=$testReport.test_sonucu
    $record.test.observed_identity=@{pid=$testReport.gozlem.process_id;start_ticks=$testReport.gozlem.process_start_ticks}
    if ($testReport.gozlem.process_id -ne $record.identity.pid -or $testReport.gozlem.process_start_ticks -ne $record.identity.start_ticks) {throw 'Test raporu başka sürece ait.'}
    if ($tester.ExitCode -ne 0 -or $record.test.status -ne 'GECTI') {throw 'CANRAT-UI-002 başarılı değil.'}
    Save-Life 'test_finished'
} catch {$record.error=$_.Exception.Message} finally {
    if ($null -ne $target -and $null -ne $record.identity) {
        try {
            if ($record.owned) {
                if ($null -ne $tester -and -not $tester.HasExited) {throw 'Test alt süreci hâlâ etkin; otomatik kapatma yapılmadı.'}
                # Do not close an app while another UI test holds its lock.
                $uiMutex=New-Object Threading.Mutex($false,"Local\CANRAT_UI_002_$($record.identity.pid)")
                $uiLock=$false
                try {
                    try {$uiLock=$uiMutex.WaitOne(0)} catch [Threading.AbandonedMutexException] {$uiLock=$true}
                    if (-not $uiLock) {throw 'UI testi etkin; normal kapatma ertelendi.'}
                    Confirm-CanRatIdentity $target $record.identity $exe
                    $conn=Connect-CanRat $exe
                    $guard=Read-CanRatGuard $conn
                    if (-not $guard.idle) {throw 'CAN göstergesi etkin/belirsiz; kapatma yapılmadı.'}
                    $record.close=Close-OwnedCanRat $target $record.identity $exe $record.owned
                } finally {if ($uiLock) {$uiMutex.ReleaseMutex()};$uiMutex.Dispose()}
            } else {
                Confirm-CanRatIdentity $target $record.identity $exe
                $record.close=[ordered]@{status='ACIK_BIRAKILDI';request_sent=$false;still_running=$true}
            }
        } catch {$record.cleanup_error=$_.Exception.Message;$record.close.status='HATA'}
    }
    $record.after=@(Get-CanRatInstances)
    if (-not $record.error -and -not $record.cleanup_error -and $record.test.status -eq 'GECTI' -and $record.close.status -in @('KAPANDI','ACIK_BIRAKILDI')) {$record.result='GECTI'}
    try {Save-Life 'finished'} finally {if ($locked) {$mutex.ReleaseMutex()};if ($null -ne $mutex) {$mutex.Dispose()}}
}
$record | ConvertTo-Json -Depth 15 -Compress
if ($record.result -eq 'GECTI') {exit 0} else {exit 2}
