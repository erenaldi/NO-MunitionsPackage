[CmdletBinding()]
param(
    [string]$LogPath = "C:\Program Files (x86)\Steam\steamapps\common\Nuclear Option\BepInEx\LogOutput.log",
    [string]$Needle = "Nuclear Option Munitions Package",
    [int]$TailLines = 30000,
    [switch]$RequireHalberd,
    [switch]$RequireHalberdFlight,
    [switch]$RequireKris,
    [switch]$RequireKrisIrccm
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $LogPath -PathType Leaf)) {
    throw "BepInEx log not found at '$LogPath'."
}

$lines = @(Get-Content -LiteralPath $LogPath -Tail $TailLines)
$needlePattern = [regex]::Escape($Needle)
$addonLines = @($lines | Where-Object { $_ -match $needlePattern })
$validationReview = @($addonLines | Where-Object { $_ -match "Phase 1 analog validation requires review" })
$blueprinterProblems = @($lines | Where-Object {
    ($_ -match "(:\s*(Blueprinter|$needlePattern)\]|\[(Ops|EncyclopediaLoader)\])") -and
    ($_ -match "\[(Error|Warning)\s*:|failed|invalid|missing|duplicate|not found") -and
    ($_ -notmatch "Phase 1 analog validation requires review")
})

Write-Output "Log: $LogPath"
Write-Output "Lines inspected: $($lines.Count)"
Write-Output "Lines containing '$Needle': $($addonLines.Count)"

if ($addonLines.Count -gt 0) {
    Write-Output "--- Addon lines ---"
    $addonLines | ForEach-Object { Write-Output $_ }
}

if ($validationReview.Count -gt 0) {
    Write-Output "Phase 1 completed with analog choices requiring review; see analog-validation.json."
}

if ($blueprinterProblems.Count -gt 0) {
    Write-Output "--- Blueprinter warnings/errors ---"
    $blueprinterProblems | ForEach-Object { Write-Output $_ }
    throw "Blueprinter warnings or errors were found in the inspected log window."
}

if ($addonLines.Count -eq 0) {
    throw "No lines containing '$Needle' were found. Confirm the bundle is installed and the game has been launched since installation."
}

if ($RequireHalberd -or $RequireHalberdFlight) {
    $requiredHalberdPatterns = @(
        "\[Phase 2A\] AAM-44 Halberd registered:",
        "\[Phase 2A\] Relative range estimate at 1 km/Mach 1:",
        "\[Phase 3\] Custom geometry applied to 'Erenaldi\.AAM44'/'Erenaldi\.AAM44_single': 2 of 2"
    )
    foreach ($pattern in $requiredHalberdPatterns) {
        if (-not ($addonLines | Where-Object { $_ -match $pattern })) {
            throw "Required Halberd log pattern was not found: $pattern"
        }
    }
    Write-Output "Halberd registration, relative range, and geometry logs found."
}

if ($RequireHalberdFlight) {
    $requiredHalberdFlightPatterns = @(
        "Halberd motor telemetry: booster burnout;",
        "Halberd booster jettisoned at sustainer transition;",
        "Halberd motor telemetry: sustainer ignition; supersonic drag reduced to 0\.25;",
        "Halberd motor telemetry: sustainer burnout; supersonic drag set to 0\.25;",
        "Halberd motor telemetry: Mach 2\.5 benchmark speed reached;",
        "Halberd motor telemetry: Mach 3\.5 benchmark speed reached;"
    )
    foreach ($pattern in $requiredHalberdFlightPatterns) {
        if (-not ($addonLines | Where-Object { $_ -match $pattern })) {
            throw "Required Halberd flight log pattern was not found: $pattern"
        }
    }
    Write-Output "Halberd motor, booster-jettison, and speed telemetry logs found."
}

if ($RequireKris -or $RequireKrisIrccm) {
    $requiredKrisPatterns = @(
        "\[Phase 2C\] Kris IRCCM configured:",
        "\[Phase 2C\] IRM-S4 Kris registered:",
        "\[Phase 3\] Custom geometry applied to 'Erenaldi\.IRMS4'/'Erenaldi\.IRMS4_single': 2 of 2"
    )
    foreach ($pattern in $requiredKrisPatterns) {
        if (-not ($addonLines | Where-Object { $_ -match $pattern })) {
            throw "Required Kris log pattern was not found: $pattern"
        }
    }
    Write-Output "Kris registration and custom geometry logs found."
}

if ($RequireKrisIrccm) {
    $requiredKrisIrccmPatterns = @(
        "Kris IRCCM suspended optical tracking on",
        "Kris IRCCM opened .* optical reacquisition window"
    )
    foreach ($pattern in $requiredKrisIrccmPatterns) {
        if (-not ($addonLines | Where-Object { $_ -match $pattern })) {
            throw "Required Kris IRCCM log pattern was not found: $pattern"
        }
    }
    if (-not ($addonLines | Where-Object {
        $_ -match "Kris IRCCM (reacquired|widened to gimbal search)"
    })) {
        throw "No completed Kris IRCCM reacquisition transition was found."
    }
    Write-Output "Kris IRCCM suspension, optical window, and recovery transition logs found."
}

Write-Output "No Blueprinter warnings or errors found in the inspected log window."
