param(
    [Parameter(Mandatory=$true)][string]$Journal,
    [ValidateSet('MissingControl','Interrupt')][string]$Mode
)
$ErrorActionPreference='Stop'
[Console]::OutputEncoding = New-Object Text.UTF8Encoding($false)
. (Join-Path $PSScriptRoot '../../otomasyon/baglanti/canrat_toggle.ps1')
$exe = Join-Path $PSScriptRoot '../../hedef_uygulama/CANRAT_3min/CANRat.exe'
$record = [ordered]@{schema_version=1; type='GERCEK_UI_KONTROLLU_DENETIM'; mode=$Mode; phase='preflight'; process_id=$null; process_start_ticks=$null; initial=$null; current=$null; mutation_attempted=$false; error=$null; cleanup_error=$null; guard=$null; timestamp=[DateTime]::UtcNow.ToString('o')}
$conn=$null; $box=$null; $locked=$false; $mutex=$null
function Save-AuditJournal {
    $temp=$Journal+'.tmp'
    [IO.File]::WriteAllText($temp, ($record | ConvertTo-Json -Depth 8), (New-Object Text.UTF8Encoding($false)))
    if ([IO.File]::Exists($Journal)) { [IO.File]::Replace($temp,$Journal,($Journal+'.previous')) }
    else { [IO.File]::Move($temp,$Journal) }
}
try {
    $conn=Connect-CanRat $exe
    $record.process_id=$conn.Process.Id
    $record.process_start_ticks=$conn.Process.StartTime.ToUniversalTime().Ticks.ToString()
    if ($Mode -eq 'MissingControl') {
        $null=Find-CanRatControl $conn 'MainWindow.centralwidget.__GOREV002_MISSING__'
        throw 'Beklenmeyen durum: denetim kimliği bulundu.'
    }
    $mutex=New-Object Threading.Mutex($false,"Local\CANRAT_UI_002_$($conn.Process.Id)")
    try { $locked=$mutex.WaitOne(0) } catch [Threading.AbandonedMutexException] { $locked=$true }
    if (-not $locked) { throw 'Başka otomasyon koşusu var.' }
    $box=Find-CanRatControl $conn 'MainWindow.centralwidget.cboxAppendRecieved'
    for ($i=0; $i -lt 2; $i++) {
        $record.guard=Read-CanRatGuard $conn
        if (-not $record.guard.idle) { throw 'Start etkin/belirsiz; kesinti denetimi başlatılmadı.' }
        Start-Sleep -Milliseconds 150
    }
    $record.initial=Read-CanRatStableState $box
    $record.phase='initial_saved'
    Save-AuditJournal
    $record.guard=Read-CanRatGuard $conn
    if (-not $record.guard.idle) { throw 'Start durumu değişti.' }
    $record.mutation_attempted=$true
    $record.phase='toggle_attempt'
    Save-AuditJournal
    Invoke-CanRatCheckboxToggle $box
    $expected=if ($record.initial -eq 'Off') {'On'} else {'Off'}
    $record.current=Wait-CanRatState $box $expected
    if ($record.current -ne $expected) { throw 'Kesinti öncesi değişim doğrulanamadı.' }
    $record.phase='interrupted_after_change'
    Save-AuditJournal
    # Deliberate termination of THIS audit helper only. Parent supervises recovery.
    [Environment]::Exit(91)
} catch {
    $record.error=$_.Exception.Message
} finally {
    # Only executed for an unexpected error, not the deliberate Exit above.
    if ($locked -and $record.mutation_attempted -and $record.initial -in @('Off','On')) {
        try {
            if ((Read-CanRatStableState $box) -ne $record.initial) { Invoke-CanRatCheckboxToggle $box }
            $record.current=Wait-CanRatState $box $record.initial
            if ($record.current -ne $record.initial) { throw 'Temizlik doğrulanamadı.' }
        } catch { $record.cleanup_error=$_.Exception.Message }
    }
    try { Save-AuditJournal } finally { if ($locked) {$mutex.ReleaseMutex()}; if ($null -ne $mutex) {$mutex.Dispose()} }
}
$record | ConvertTo-Json -Depth 8 -Compress
exit 2
