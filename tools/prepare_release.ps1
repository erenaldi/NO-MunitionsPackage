[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$BundlePath,

    [Parameter(Mandatory = $true)]
    [string]$Version,

    [string]$OutputDirectory = (Join-Path $PSScriptRoot "..\dist")
)

$ErrorActionPreference = "Stop"

if ($Version -notmatch "^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$") {
    throw "Version '$Version' must use the numeric major.minor.patch format."
}

$bundle = Get-Item -LiteralPath $BundlePath
if ($bundle.Extension -ne ".nobp") {
    throw "Expected a .nobp bundle, received '$($bundle.Name)'."
}

$expectedName = "MunitionsPackage_$Version.nobp"
if ($bundle.Name -ne $expectedName) {
    throw "Expected bundle name '$expectedName', received '$($bundle.Name)'. Rebuild it with the matching Blueprinter display name and version."
}

if (-not (Test-Path -LiteralPath $OutputDirectory)) {
    New-Item -ItemType Directory -Path $OutputDirectory | Out-Null
}

$destination = Join-Path $OutputDirectory $expectedName
Copy-Item -LiteralPath $bundle.FullName -Destination $destination -Force
$hash = (Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash.ToLowerInvariant()
$downloadUrl = "https://github.com/Erenaldi/NO-MunitionsPackage/releases/download/$Version/$expectedName"

$release = [ordered]@{
    id = "Erenaldi.MunitionsPackage"
    version = $Version
    fileName = $expectedName
    downloadUrl = $downloadUrl
    hash = "sha256:$hash"
    extends = [ordered]@{
        id = "com.nikkorap.blueprinter"
        version = "2.0.1"
    }
}

$metadataPath = Join-Path $OutputDirectory "release.json"
$releaseJson = ($release | ConvertTo-Json -Depth 4) + [Environment]::NewLine
[System.IO.File]::WriteAllText($metadataPath, $releaseJson, [System.Text.UTF8Encoding]::new($false))

Write-Output "Bundle:   $destination"
Write-Output "Metadata: $metadataPath"
Write-Output "SHA-256:  $hash"
