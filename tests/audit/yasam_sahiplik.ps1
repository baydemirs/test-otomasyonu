# Synthetic process objects only. Never starts/closes a real application.
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot '../../otomasyon/baglanti/canrat_yasam.ps1')
$script:calls=0
function Fake-Process {
    $p=[pscustomobject]@{Id=123;StartTime=[DateTime]::UtcNow;Path='C:\fake\CANRat.exe';HasExited=$false;MainWindowHandle=12;ExitCode=0}
    $p|Add-Member ScriptMethod Refresh {}
    $p|Add-Member ScriptMethod CloseMainWindow {$script:calls++;return $true}
    $p|Add-Member ScriptMethod WaitForExit {param($ms);return $true}
    return $p
}
function Must-Reject([string]$Name,[scriptblock]$Action) {
    $before=$script:calls
    $rejected=$false
    try {& $Action | Out-Null} catch {$rejected=$true}
    if (-not $rejected -or $script:calls -ne $before) {throw "FAIL: $Name"}
    return @{name=$Name;expected='REJECT_WITHOUT_CLOSE';observed='REJECT_WITHOUT_CLOSE';kind='SYNTHETIC_PROCESS'}
}
$p=Fake-Process
$identity=@{pid=$p.Id;start_ticks=$p.StartTime.ToUniversalTime().Ticks.ToString()}
$results=@()
$results+=Must-Reject 'not-owned' {Close-OwnedCanRat $p $identity $p.Path $false}
$wrong=@{pid=$p.Id;start_ticks='1'}
$results+=Must-Reject 'reused-pid' {Close-OwnedCanRat $p $wrong $p.Path $true}
$results+=Must-Reject 'wrong-exe' {Close-OwnedCanRat $p $identity 'C:\other\CANRat.exe' $true}
$p.HasExited=$true
$results+=Must-Reject 'already-exited' {Close-OwnedCanRat $p $identity $p.Path $true}
$p.HasExited=$false
$p.MainWindowHandle=0
$results+=Must-Reject 'no-window' {Close-OwnedCanRat $p $identity $p.Path $true}
$p.MainWindowHandle=12
$r=Close-OwnedCanRat $p $identity $p.Path $true
if ($r.status -ne 'KAPANDI' -or $script:calls -ne 1) {throw 'Owned close dispatch failed.'}
$results+=@{name='owned-normal-close';expected='ONE_CLOSE';observed='ONE_CLOSE';kind='SYNTHETIC_PROCESS'}
$results|ConvertTo-Json -Depth 5
