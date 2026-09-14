[CmdletBinding()]
param(
    [string]$MissionDirectory = (Join-Path $PSScriptRoot "..\missions\Erenaldi.ProvingGround"),
    [string]$MissionsRoot = (Join-Path (Split-Path $env:LOCALAPPDATA -Parent) "LocalLow\Shockfront\NuclearOption\Missions"),
    [switch]$Force,
    [switch]$SkipRuntimeSchema
)

$ErrorActionPreference = "Stop"

if (Get-Process -Name "NuclearOption" -ErrorAction SilentlyContinue) {
    throw "Nuclear Option is running. Close it before installing the test mission."
}
if (-not (Test-Path -LiteralPath $MissionDirectory -PathType Container)) {
    throw "Mission source directory not found at '$MissionDirectory'."
}
if (-not (Test-Path -LiteralPath $MissionsRoot -PathType Container)) {
    $profileRoot = Split-Path $MissionsRoot -Parent
    if (-not (Test-Path -LiteralPath $profileRoot -PathType Container)) {
        throw "Nuclear Option profile directory not found at '$profileRoot'. Launch the game once before installing the test mission."
    }
    New-Item -ItemType Directory -Path $MissionsRoot | Out-Null
}

$validator = Join-Path $PSScriptRoot "validate_test_mission.ps1"
& $validator -MissionDirectory $MissionDirectory -SkipRuntimeSchema:$SkipRuntimeSchema

$destination = Join-Path $MissionsRoot "Erenaldi.ProvingGround"
if (Test-Path -LiteralPath $destination -PathType Leaf) {
    throw "Mission destination '$destination' is a file; expected a directory."
}
if ((Test-Path -LiteralPath $destination) -and -not $Force) {
    throw "Mission already exists at '$destination'. Re-run with -Force to update only the source-controlled mission files."
}
if (-not (Test-Path -LiteralPath $destination)) {
    New-Item -ItemType Directory -Path $destination | Out-Null
}

foreach ($name in @("Erenaldi.ProvingGround.json", "meta.json", "lane-manifest.json")) {
    Copy-Item -LiteralPath (Join-Path $MissionDirectory $name) -Destination (Join-Path $destination $name) -Force
}

Write-Warning "Existing preview.png and workshop.json files, if any, were preserved."

$sourceHash = (Get-FileHash -LiteralPath (Join-Path $MissionDirectory "Erenaldi.ProvingGround.json") -Algorithm SHA256).Hash
$installedHash = (Get-FileHash -LiteralPath (Join-Path $destination "Erenaldi.ProvingGround.json") -Algorithm SHA256).Hash
if ($sourceHash -ne $installedHash) {
    throw "Installed mission hash does not match the source mission."
}

Write-Output "Installed mission: $destination"
Write-Output "SHA-256: $($installedHash.ToLowerInvariant())"
