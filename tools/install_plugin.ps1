[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$PluginPath,

    [string]$GamePath = "C:\Program Files (x86)\Steam\steamapps\common\Nuclear Option"
)

$ErrorActionPreference = "Stop"

$plugin = Get-Item -LiteralPath $PluginPath
if ($plugin.Extension -ne ".dll") {
    throw "Expected a .dll plugin, received '$($plugin.Name)'."
}
if ($plugin.Name -ne "Erenaldi.MunitionsPackage.dll") {
    throw "Expected Erenaldi.MunitionsPackage.dll, received '$($plugin.Name)'."
}
$assemblyName = [System.Reflection.AssemblyName]::GetAssemblyName($plugin.FullName).Name
if ($assemblyName -ne "Erenaldi.MunitionsPackage") {
    throw "Expected assembly name Erenaldi.MunitionsPackage, received '$assemblyName'."
}

if (Get-Process -Name "NuclearOption" -ErrorAction SilentlyContinue) {
    throw "Nuclear Option is running. Close it before replacing the plugin DLL."
}

$pluginsPath = Join-Path $GamePath "BepInEx\plugins"
if (-not (Test-Path -LiteralPath $pluginsPath -PathType Container)) {
    throw "BepInEx plugins directory not found at '$pluginsPath'."
}

$destinationDirectory = Join-Path $pluginsPath "Erenaldi.MunitionsPackage"
if (-not (Test-Path -LiteralPath $destinationDirectory)) {
    New-Item -ItemType Directory -Path $destinationDirectory | Out-Null
}

$destination = Join-Path $destinationDirectory $plugin.Name
Copy-Item -LiteralPath $plugin.FullName -Destination $destination -Force
$hash = (Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash.ToLowerInvariant()

Write-Output "Installed: $destination"
Write-Output "SHA-256:  $hash"
