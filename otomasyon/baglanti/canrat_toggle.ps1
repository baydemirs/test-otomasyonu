$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes

function Connect-CanRat([string]$Exe) {
    $resolved = (Resolve-Path -LiteralPath $Exe).ProviderPath
    $matches = @(Get-Process -Name CANRat -ErrorAction SilentlyContinue | Where-Object { $_.Path -eq $resolved -and $_.MainWindowHandle -ne 0 })
    if ($matches.Count -ne 1) { throw 'Hedef EXE için tam bir açık pencere gerekli.' }
    $p = $matches[0]
    $root = [System.Windows.Automation.AutomationElement]::FromHandle($p.MainWindowHandle)
    if ($null -eq $root) { throw 'UIA ana penceresi okunamadı.' }
    return @{ Process = $p; Root = $root; Path = $resolved }
}

function Find-CanRatControl($Connection, [string]$Id) {
    $condition = New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::AutomationIdProperty, $Id)
    $matches = $Connection.Root.FindAll([System.Windows.Automation.TreeScope]::Descendants, $condition)
    if ($matches.Count -ne 1) { throw "Kontrol benzersiz değil veya bulunamadı: $Id" }
    $element = $matches[0]
    if ($element.Current.ProcessId -ne $Connection.Process.Id) { throw 'Kontrol PID uyuşmazlığı.' }
    return $element
}

function Read-CanRatToggle($Element) {
    $pattern = $Element.GetCurrentPattern([System.Windows.Automation.TogglePattern]::Pattern)
    return $pattern.Current.ToggleState.ToString()
}

function Read-CanRatGuard($Connection) {
    $start = Find-CanRatControl $Connection 'MainWindow.centralwidget.btnStart'
    $state = Read-CanRatToggle $start
    $name = $start.Current.Name
    $active = ($state -eq 'On' -or $name -eq 'Stop')
    return [ordered]@{ toggle_state = $state; name = $name; active = $active; idle = ($state -eq 'Off' -and $name -eq 'Start') }
}

function Read-CanRatStableState($Element) {
    $first = Read-CanRatToggle $Element
    if ($first -notin @('Off', 'On')) { throw "Belirsiz ToggleState: $first" }
    Start-Sleep -Milliseconds 150
    $second = Read-CanRatToggle $Element
    if ($first -ne $second) { throw "Kararsız ToggleState: $first -> $second" }
    return $second
}

function Wait-CanRatState($Element, [string]$Expected) {
    $timer = [Diagnostics.Stopwatch]::StartNew()
    $last = $null
    $consecutive = 0
    do {
        $last = Read-CanRatToggle $Element
        if ($last -notin @('Off', 'On')) { throw "Belirsiz ara ToggleState: $last" }
        if ($last -eq $Expected) { $consecutive++ } else { $consecutive = 0 }
        if ($consecutive -ge 2) { return $last }
        Start-Sleep -Milliseconds 100
    } while ($timer.ElapsedMilliseconds -lt 2000)
    if ($last -eq $Expected) { throw 'Beklenen ara durumun kararlılığı süre sınırında doğrulanamadı.' }
    return (Read-CanRatStableState $Element)
}

function Invoke-CanRatCheckboxToggle($Element) {
    # Sole UI mutation: exact checkbox identity. Never invoke Start or other controls.
    if ($Element.Current.AutomationId -ne 'MainWindow.centralwidget.cboxAppendRecieved' -or
        $Element.Current.ClassName -ne 'QCheckBox' -or
        $Element.Current.ControlType -ne [System.Windows.Automation.ControlType]::CheckBox -or
        -not $Element.Current.IsEnabled -or $Element.Current.IsOffscreen) {
        throw 'Etkileşim hedefi izin verilen etkin/görünür kutu değil.'
    }
    $Element.GetCurrentPattern([System.Windows.Automation.TogglePattern]::Pattern).Toggle()
}
