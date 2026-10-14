param([Parameter(Mandatory=$true)][string]$TargetExe)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
try {
    Add-Type -AssemblyName UIAutomationClient
    Add-Type -AssemblyName UIAutomationTypes
    $resolvedTarget = (Resolve-Path -LiteralPath $TargetExe).ProviderPath
    $canRatCandidates = @(Get-Process -Name CANRat -ErrorAction SilentlyContinue | Where-Object {
        $_.Path -eq $resolvedTarget -and $_.MainWindowHandle -ne 0
    })
    if ($canRatCandidates.Count -eq 0) {
        throw 'Open the specified CANRat.exe first, in this Windows session. Check path and privilege level.'
    }
    if ($canRatCandidates.Count -ne 1) {
        throw 'Multiple matching CanRat windows found. Leave exactly one instance open.'
    }
    $targetProcess = $canRatCandidates[0]
    $root = [System.Windows.Automation.AutomationElement]::FromHandle($targetProcess.MainWindowHandle)
    if ($null -eq $root) { throw 'Main window is not accessible through UI Automation.' }
    function Read-Element($element) {
        $current = $element.Current
        $patterns = @($element.GetSupportedPatterns() | ForEach-Object { $_.ProgrammaticName })
        return [ordered]@{
            name = $current.Name
            automation_id = $current.AutomationId
            control_type = $current.ControlType.ProgrammaticName
            class_name = $current.ClassName
            framework_id = $current.FrameworkId
            enabled = $current.IsEnabled
            offscreen = $current.IsOffscreen
            password = $current.IsPassword
            patterns = $patterns
        }
    }
    # Search only inside the verified target window, never the whole desktop tree.
    $elements = $root.FindAll([System.Windows.Automation.TreeScope]::Descendants,
                            [System.Windows.Automation.Condition]::TrueCondition)
    $controls = @()
    $readErrors = @()
    $limit = [Math]::Min($elements.Count, 1000)
    for ($index = 0; $index -lt $limit; $index++) {
        try { $controls += (Read-Element $elements[$index]) }
        catch { $readErrors += "Element ${index}: $($_.Exception.Message)" }
    }
    $record = [ordered]@{
        schema_version = 1
        process_id = $targetProcess.Id
        executable_path = $resolvedTarget
        window = (Read-Element $root)
        controls = @($controls)
        total_found = $elements.Count
        truncated = ($elements.Count -gt 1000)
        read_errors = @($readErrors)
    }
    $record | ConvertTo-Json -Depth 8 -Compress
    exit 0
} catch {
    [Console]::Error.WriteLine($_.Exception.Message)
    exit 2
}
