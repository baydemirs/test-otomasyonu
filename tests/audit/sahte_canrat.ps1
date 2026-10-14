# DENETIM FIXTURE: real UIA/process access is deliberately absent.
$ErrorActionPreference = 'Stop'
$script:FixtureRoot = Split-Path $PSScriptRoot -Parent
$script:FixtureFile = Join-Path $script:FixtureRoot 'fixture.json'
$script:TraceFile = Join-Path $script:FixtureRoot 'fixture-trace.jsonl'
function Get-Fixture { return (Get-Content -LiteralPath $script:FixtureFile -Raw -Encoding UTF8 | ConvertFrom-Json) }
function Save-Fixture($value) { [IO.File]::WriteAllText($script:FixtureFile, ($value | ConvertTo-Json), (New-Object Text.UTF8Encoding($false))) }
function Trace-Fixture([string]$action, $detail) {
    $event = @{ action=$action; detail=$detail; helper_pid=$PID; time_utc=[DateTime]::UtcNow.ToString('o') }
    [IO.File]::AppendAllText($script:TraceFile, (($event | ConvertTo-Json -Compress) + "`n"), (New-Object Text.UTF8Encoding($false)))
}
function Connect-CanRat([string]$Exe) {
    $f = Get-Fixture
    Trace-Fixture 'connect' $f.scenario
    if ($f.scenario -eq 'absent') { throw 'FIXTURE: no matching open application' }
    return @{ Process=[pscustomobject]@{Id=424242;StartTime=[DateTime]::Parse('2026-10-13T00:00:00Z').ToUniversalTime()}; Root='FAKE'; Path=$Exe }
}
function Find-CanRatControl($Connection, [string]$Id) {
    Trace-Fixture 'find' $Id
    if ((Get-Fixture).scenario -eq 'missing') { throw 'FIXTURE: required control missing' }
    return 'FAKE_CHECKBOX'
}
function Read-CanRatGuard($Connection) {
    if ((Get-Fixture).scenario -eq 'active') {
        return @{toggle_state='On';name='Stop';active=$true;idle=$false}
    }
    return @{toggle_state='Off';name='Start';active=$false;idle=$true}
}
function Read-CanRatStableState($Element) {
    $state = (Get-Fixture).state
    Trace-Fixture 'read_state' $state
    if ($state -notin @('Off','On')) { throw 'FIXTURE: Indeterminate state' }
    return $state
}
function Wait-CanRatState($Element, [string]$Expected) { return (Read-CanRatStableState $Element) }
function Invoke-CanRatCheckboxToggle($Element) {
    $f = Get-Fixture
    $f.toggle_calls++
    Save-Fixture $f
    Trace-Fixture 'toggle' $f.toggle_calls
    if ($f.scenario -eq 'nochange') { return }
    if ($f.scenario -eq 'cleanupfail' -and $f.toggle_calls -ge 2) { throw 'FIXTURE: restore Toggle failed' }
    $f.state = if ($f.state -eq 'Off') { 'On' } else { 'Off' }
    Save-Fixture $f
    if ($f.scenario -eq 'timeout' -and $f.toggle_calls -eq 1) { Start-Sleep -Seconds 45 }
}
