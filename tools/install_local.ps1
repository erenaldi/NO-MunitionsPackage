[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$BundlePath,

    [string]$GamePath = "C:\Program Files (x86)\Steam\steamapps\common\Nuclear Option"
)

$ErrorActionPreference = "Stop"

$bundle = Get-Item -LiteralPath $BundlePath
if ($bundle.Extension -ne ".nobp") {
    throw "Expected a .nobp bundle, received '$($bundle.Name)'."
}

$pluginsPath = Join-Path $GamePath "BepInEx\plugins"
$blueprinterPath = Join-Path $pluginsPath "com.nikkorap.blueprinter"
if (-not (Test-Path -LiteralPath $pluginsPath -PathType Container)) {
    throw "BepInEx plugins directory not found at '$pluginsPath'."
}
if (-not (Get-ChildItem -LiteralPath $blueprinterPath -Filter "Blueprinter_*.dll" -File -ErrorAction SilentlyContinue)) {
    throw "Blueprinter is not installed under '$blueprinterPath'."
}

$addonPath = Join-Path $blueprinterPath "addons\Erenaldi.MunitionsPackage"
if (-not (Test-Path -LiteralPath $addonPath)) {
    New-Item -ItemType Directory -Path $addonPath | Out-Null
}

$destination = Join-Path $addonPath $bundle.Name
$otherBundles = @(Get-ChildItem -LiteralPath $addonPath -Filter "*.nobp" -File | Where-Object { $_.FullName -ne $destination })
if ($otherBundles.Count -gt 0) {
    $names = ($otherBundles.Name -join ", ")
    throw "Another bundle is already installed in the addon directory: $names. Remove or disable it explicitly before installing a different version."
}

Copy-Item -LiteralPath $bundle.FullName -Destination $destination -Force
$hash = (Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash.ToLowerInvariant()

Write-Output "Installed: $destination"
Write-Output "SHA-256:  $hash"
