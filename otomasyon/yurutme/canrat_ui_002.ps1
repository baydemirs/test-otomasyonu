param(
    [Parameter(Mandatory=$true)][string]$TargetExe,
    [Parameter(Mandatory=$true)][string]$Journal,
    [ValidateSet('Inspect','Exercise','Recover')][string]$Mode = 'Inspect'
)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
. (Join-Path $PSScriptRoot '../baglanti/canrat_toggle.ps1')
$record = [ordered]@{
    schema_version = 1; mode = $Mode; phase = 'preflight'; process_id = $null; process_start_ticks = $null
    guard_before = @(); guard_after = $null; initial = $null; expected_changed = $null
    changed = $null; changed_verified = $false; final = $null; restored = $false
    mutation_attempted = $false; cleanup_attempted = $false; active_collection = $false
    error = $null; cleanup_error = $null; cleanup_journal_error = $null; events = @()
}
$connection = $null
$checkbox = $null
$mutex = $null
$locked = $false

function Save-Journal {
    $record.events += [ordered]@{ time_utc = [DateTime]::UtcNow.ToString('o'); phase = $record.phase }
    $json = $record | ConvertTo-Json -Depth 10
    $temp = $Journal + '.tmp'
    [IO.File]::WriteAllText($temp, $json, (New-Object Text.UTF8Encoding($false)))
    if ([IO.File]::Exists($Journal)) { [IO.File]::Replace($temp, $Journal, ($Journal + '.previous')) }
    else { [IO.File]::Move($temp, $Journal) }
}

try {
    $connection = Connect-CanRat $TargetExe
    $record.process_id = $connection.Process.Id
    $record.process_start_ticks = $connection.Process.StartTime.ToUniversalTime().Ticks.ToString()
    $mutex = New-Object Threading.Mutex($false, "Local\CANRAT_UI_002_$($record.process_id)")
    try { $locked = $mutex.WaitOne(0) } catch [Threading.AbandonedMutexException] { $locked = $true }
    if (-not $locked) { throw 'Aynı hedefte başka otomasyon koşusu var.' }
    $checkbox = Find-CanRatControl $connection 'MainWindow.centralwidget.cboxAppendRecieved'
    if ($Mode -eq 'Recover') {
        $previous = Get-Content -LiteralPath $Journal -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($previous.schema_version -ne 1 -or $previous.process_id -ne $record.process_id -or
            $previous.process_start_ticks -ne $record.process_start_ticks -or
            $previous.initial -notin @('Off', 'On')) { throw 'Geri yükleme günlüğü veya süreç kimliği güvenilir değil.' }
        $record.initial = $previous.initial
        $record.mutation_attempted = $previous.mutation_attempted
        $record.phase = 'recovery'
    } else {
        for ($i = 0; $i -lt 2; $i++) {
            $guard = Read-CanRatGuard $connection
            $record.guard_before += $guard
            if ($guard.active) { $record.active_collection = $true; throw 'Veri toplama etkin; etkileşim testi başlatılmadı.' }
            if (-not $guard.idle) { throw 'Start durumu belirsiz; etkileşim testi başlatılmadı.' }
            Start-Sleep -Milliseconds 150
        }
        $record.initial = Read-CanRatStableState $checkbox
        $record.expected_changed = if ($record.initial -eq 'Off') { 'On' } else { 'Off' }
        $record.phase = 'initial_saved'
        Save-Journal
        if ($Mode -eq 'Exercise') {
            # Re-read immediately before input to reduce stale-precondition risk.
            $guard = Read-CanRatGuard $connection
            $record.guard_before += $guard
            if (-not $guard.idle) {
                $record.active_collection = $guard.active
                throw 'Etkileşim öncesi Start durumu değişti; test başlatılmadı.'
            }
            if ((Read-CanRatStableState $checkbox) -ne $record.initial) { throw 'Kutunun başlangıç durumu dışarıdan değişti.' }
            $record.mutation_attempted = $true
            $record.phase = 'toggle_attempt'
            Save-Journal
            Invoke-CanRatCheckboxToggle $checkbox
            $record.changed = Wait-CanRatState $checkbox $record.expected_changed
            $record.changed_verified = ($record.changed -eq $record.expected_changed)
            $record.phase = 'change_observed'
            Save-Journal
        }
    }
} catch {
    $record.error = $_.Exception.Message
} finally {
    if ($locked -and $null -ne $checkbox -and $record.initial -in @('Off','On') -and
        ($record.mutation_attempted -or $Mode -eq 'Recover')) {
        $record.cleanup_attempted = $true
        $record.phase = 'restoring'
        try {
            try { Save-Journal } catch { $record.cleanup_journal_error = $_.Exception.Message }
            $now = Read-CanRatStableState $checkbox
            if ($now -ne $record.initial) { Invoke-CanRatCheckboxToggle $checkbox }
            $record.final = Wait-CanRatState $checkbox $record.initial
            $record.restored = ($record.final -eq $record.initial)
            if (-not $record.restored) { throw 'Başlangıç durumuna dönüş doğrulanamadı.' }
        } catch { $record.cleanup_error = $_.Exception.Message }
    }
    if ($locked -and $null -ne $connection) {
        try { $record.guard_after = Read-CanRatGuard $connection }
        catch { if (-not $record.error) { $record.error = 'Son Start durumu okunamadı: ' + $_.Exception.Message } }
    }
    $record.phase = 'completed'
    try { Save-Journal }
    finally { if ($locked) { $mutex.ReleaseMutex() }; if ($null -ne $mutex) { $mutex.Dispose() } }
}
$record | ConvertTo-Json -Depth 10 -Compress
if ($record.error -or $record.cleanup_error) { exit 2 }
exit 0
