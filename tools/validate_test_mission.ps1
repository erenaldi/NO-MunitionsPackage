[CmdletBinding()]
param(
    [string]$MissionDirectory = (Join-Path $PSScriptRoot "..\missions\Erenaldi.ProvingGround"),
    [string]$SchemaPath = "C:\Program Files (x86)\Steam\steamapps\common\Nuclear Option\BepInEx\config\Erenaldi.MunitionsPackage\weapon-schema.json",
    [switch]$SkipRuntimeSchema
)

$ErrorActionPreference = "Stop"

function Read-JsonFile {
    param([Parameter(Mandatory = $true)][string]$Path)

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Required JSON file not found at '$Path'."
    }
    return Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json
}

$missionPath = Join-Path $MissionDirectory "Erenaldi.ProvingGround.json"
$manifestPath = Join-Path $MissionDirectory "lane-manifest.json"
$metaPath = Join-Path $MissionDirectory "meta.json"
$mission = Read-JsonFile -Path $missionPath
$manifest = Read-JsonFile -Path $manifestPath
$meta = Read-JsonFile -Path $metaPath

if ($mission.JsonVersion -ne 6) {
    throw "Mission JsonVersion must be 6; found '$($mission.JsonVersion)'."
}
if ($meta.FileName -ne $manifest.mission) {
    throw "meta.json FileName '$($meta.FileName)' does not match manifest mission '$($manifest.mission)'."
}
if ($mission.MapKey.Type -ne $manifest.map.type -or $mission.MapKey.Path -ne $manifest.map.path) {
    throw "Mission MapKey does not match lane-manifest.json."
}
if ($mission.missionSettings.playerMode -ne "SingleAndMultiplayer") {
    throw "Mission playerMode must be 'SingleAndMultiplayer'."
}
foreach ($tag in @($mission.missionSettings.Tags)) {
    if ($tag -is [string] -or $null -eq $tag.Tag -or $null -eq $tag.Color -or $null -eq $tag.SortOrder) {
        throw "Each mission tag must be a version 6 MissionTag object with Tag, Color, and SortOrder fields."
    }
}

$lanes = @($manifest.lanes)
if ($lanes.Count -ne 15) {
    throw "Expected 15 munition lanes; found $($lanes.Count)."
}
$laneIds = @($lanes | ForEach-Object { $_.id })
if (@($laneIds | Sort-Object -Unique).Count -ne $laneIds.Count) {
    throw "Lane IDs must be unique."
}
$expectedLaneIds = 1..15 | ForEach-Object { "L{0:D2}" -f $_ }
if (Compare-Object -ReferenceObject $expectedLaneIds -DifferenceObject $laneIds) {
    throw "Lane IDs must cover L01 through L17 exactly."
}

$zoneIds = @($manifest.zones | ForEach-Object { $_.id })
foreach ($lane in $lanes) {
    if ($lane.zone -notin $zoneIds) {
        throw "Lane '$($lane.id)' references unknown zone '$($lane.zone)'."
    }
    if ($lane.status -eq "live" -and [string]::IsNullOrWhiteSpace($lane.mountKey)) {
        throw "Live lane '$($lane.id)' has no mount key."
    }
}

$liveKeys = @($lanes | Where-Object { $_.status -eq "live" } | ForEach-Object { $_.mountKey })
$declaredLiveKeys = @($manifest.liveMountKeys)
if (Compare-Object -ReferenceObject $declaredLiveKeys -DifferenceObject $liveKeys) {
    throw "Manifest liveMountKeys does not match the live lanes."
}

$allUnits = @($mission.aircraft) + @($mission.vehicles) + @($mission.ships) + @($mission.buildings)
$unitNames = @($allUnits | ForEach-Object { $_.UniqueName })
if ($unitNames -contains $null -or $unitNames -contains "") {
    throw "Every mission unit must have a UniqueName."
}
if (@($unitNames | Sort-Object -Unique).Count -ne $unitNames.Count) {
    throw "Mission unit UniqueName values must be unique."
}

$players = @($mission.aircraft | Where-Object { $_.playerControlled })
if ($players.Count -ne 0) {
    throw "The proving ground must not force a player-controlled aircraft; found $($players.Count)."
}
$spawnAirbase = @($mission.airbases | Where-Object {
    $_.UniqueName -eq "North Boscali Airbase" -and $_.DisplayName -eq "North Boscali Airbase" -and
        $_.IsOverride -and $_.faction -eq "Boscali" -and -not $_.Disabled
})
if ($spawnAirbase.Count -ne 1) {
    throw "North Boscali Airbase must have exactly one enabled Boscali override."
}
foreach ($aircraft in @($mission.aircraft)) {
    if ($aircraft.liveryType -notin @("Builtin", "Workshop")) {
        throw "Aircraft '$($aircraft.UniqueName)' has unsupported liveryType '$($aircraft.liveryType)'."
    }
}
foreach ($objective in @($mission.objectives)) {
    if ($objective.Type -notin @("None", "ReachWaypoints")) {
        throw "Objective '$($objective.UniqueName)' uses unsupported type '$($objective.Type)'."
    }
}
foreach ($zoneId in $zoneIds) {
    if (-not ($unitNames | Where-Object { $_ -like "$zoneId-*" })) {
        throw "Zone '$zoneId' has no named target in the mission."
    }
    $labels = @($mission.objectives | Where-Object {
        $_.Type -eq "ReachWaypoints" -and $_.DisplayName -eq $zoneId -and -not $_.Hidden
    })
    if ($labels.Count -ne 1 -or @($labels[0].waypoints).Count -ne 1) {
        throw "Zone '$zoneId' must have exactly one visible, single-waypoint map label objective."
    }
}

$closeTargets = @($mission.aircraft | Where-Object { $_.UniqueName -like "AIR-CLOSE-IR-TARGET*" })
if ($closeTargets.Count -ne 4) {
    throw "AIR-CLOSE must contain exactly four fighter targets; found $($closeTargets.Count)."
}
foreach ($closeTargetEntry in $closeTargets) {
    $closeWeapons = @($closeTargetEntry.savedLoadout.Selected | ForEach-Object { $_.Key } | Where-Object { -not [string]::IsNullOrEmpty($_) })
    if ($closeWeapons.Count -ne 1 -or $closeWeapons[0] -ne "gun_20mm_internal") {
        throw "Close target '$($closeTargetEntry.UniqueName)' must have a gun-only loadout."
    }
    if ($closeTargetEntry.bravery -ne 1.0) {
        throw "Close target '$($closeTargetEntry.UniqueName)' bravery must remain 1.0 for committed dogfighting."
    }
}
$closeTarget = @($closeTargets | Where-Object { $_.UniqueName -eq "AIR-CLOSE-IR-TARGET" })
if ($closeTarget.Count -ne 1) {
    throw "AIR-CLOSE must retain exactly one AIR-CLOSE-IR-TARGET heading anchor."
}
$startObjective = @($mission.objectives | Where-Object { $_.UniqueName -eq "Mission Start" })
$startLabels = @($mission.outcomes | Where-Object { $_.UniqueName -eq "START-ZONE-LABELS" -and $_.Type -eq "StartObjective" })
if ($startObjective.Count -ne 1 -or "START-ZONE-LABELS" -notin @($startObjective[0].Outcomes) -or $startLabels.Count -ne 1) {
    throw "Mission Start must activate the START-ZONE-LABELS outcome."
}
$closePatrolNames = @("PATROL-AIR-CLOSE", "PATROL-AIR-CLOSE-02", "PATROL-AIR-CLOSE-03", "PATROL-AIR-CLOSE-04")
$expectedStartedObjectives = @($zoneIds | ForEach-Object { "LABEL-$_" }) + $closePatrolNames + @("PATROL-AIR-BVR", "REVEAL-ALL-TARGETS")
if (Compare-Object -ReferenceObject $expectedStartedObjectives -DifferenceObject @($startLabels[0].objectivesToStart)) {
    throw "START-ZONE-LABELS must activate every map label and patrol objective exactly once."
}
$closePatrol = @($mission.objectives | Where-Object {
    $_.UniqueName -in $closePatrolNames -and $_.Faction -eq "Primeva" -and $_.Hidden -and
        $_.Type -eq "ReachWaypoints" -and -not $_.completeOnEnterRange
})
if ($closePatrol.Count -ne 4 -or @($closePatrol | Where-Object { @($_.waypoints).Count -ne 1 }).Count -ne 0) {
    throw "AIR-CLOSE must have four persistent hidden Primevan single-waypoint patrol objectives."
}
$bvrPatrol = @($mission.objectives | Where-Object {
    $_.UniqueName -eq "PATROL-AIR-BVR" -and $_.Faction -eq "Primeva" -and $_.Hidden -and
        $_.Type -eq "ReachWaypoints" -and -not $_.completeOnEnterRange
})
if ($bvrPatrol.Count -ne 1 -or @($bvrPatrol[0].waypoints).Count -ne 1) {
    throw "PATROL-AIR-BVR must be one persistent hidden Primevan waypoint objective."
}
$revealObjective = @($mission.objectives | Where-Object {
    $_.UniqueName -eq "REVEAL-ALL-TARGETS" -and $_.Type -eq "None" -and $_.Faction -eq "Boscali" -and $_.Hidden
})
$revealOutcome = @($mission.outcomes | Where-Object {
    $_.UniqueName -eq "APPLY-REVEAL-ALL-TARGETS" -and $_.Type -eq "RevealUnit"
})
if ($revealObjective.Count -ne 1 -or "APPLY-REVEAL-ALL-TARGETS" -notin @($revealObjective[0].Outcomes) -or $revealOutcome.Count -ne 1) {
    throw "REVEAL-ALL-TARGETS must complete the Boscali RevealUnit outcome."
}
if (Compare-Object -ReferenceObject $unitNames -DifferenceObject @($revealOutcome[0].UnitsToReveal)) {
    throw "APPLY-REVEAL-ALL-TARGETS must reveal every mission target exactly once."
}
$bvrTarget = @($mission.aircraft | Where-Object { $_.UniqueName -eq "AIR-BVR-RADAR-TARGET" })
if ($bvrTarget.Count -ne 1) {
    throw "AIR-BVR-RADAR-TARGET must exist exactly once."
}
foreach ($closeTargetEntry in $closeTargets) {
    $airTargetSeparation = [Math]::Sqrt(
        [Math]::Pow([double]$closeTargetEntry.globalPosition.x - [double]$bvrTarget[0].globalPosition.x, 2) +
        [Math]::Pow([double]$closeTargetEntry.globalPosition.z - [double]$bvrTarget[0].globalPosition.z, 2)
    )
    if ($airTargetSeparation -lt 80000.0) {
        throw "Close target '$($closeTargetEntry.UniqueName)' must remain at least 80 km from AIR-BVR; found $([Math]::Round($airTargetSeparation / 1000.0, 1)) km."
    }
}

$environment = $mission.environment
if ($environment.timeFactor -ne 0 -or $environment.weatherIntensity -ne 0 -or
    $environment.windSpeed -ne 0 -or $environment.windTurbulence -ne 0 -or
    $environment.windRandomHeading -ne 0) {
    throw "The proving-ground environment must remain deterministic."
}
if (-not $mission.missionSettings.allowRespawn) {
    throw "The proving ground must allow player respawn."
}

if (-not $SkipRuntimeSchema) {
    $schema = Read-JsonFile -Path $SchemaPath
    if ($schema.schemaVersion -ne 1) {
        throw "Unsupported runtime weapon schema version '$($schema.schemaVersion)'."
    }
    $schemaMountKeys = @($schema.weapons | ForEach-Object { $_.lookupKey })
    $missingLiveKeys = @($declaredLiveKeys | Where-Object { $_ -notin $schemaMountKeys })
    if ($missingLiveKeys.Count -gt 0) {
        throw "Runtime schema generated '$($schema.generatedUtc)' is missing live mount(s): $($missingLiveKeys -join ', '). Launch the game to regenerate it before validating."
    }
    foreach ($lane in @($lanes | Where-Object { $_.status -eq "live" })) {
        $carrier = @($schema.aircraftHardpoints | Where-Object { $_.lookupKey -eq $lane.carrier })
        if ($carrier.Count -ne 1) {
            throw "Runtime schema must contain exactly one '$($lane.carrier)' carrier for lane '$($lane.id)'; found $($carrier.Count)."
        }
        $index = [int]$lane.hardpointSetIndex
        if ($index -lt 0 -or $index -ge @($carrier[0].hardpoints).Count) {
            throw "Lane '$($lane.id)' hardpoint set $index is outside '$($lane.carrier)' hardpoint bounds."
        }
        $hardpoint = $carrier[0].hardpoints[$index]
        if ($null -eq $hardpoint) {
            throw "Runtime schema has a null $($lane.carrier) hardpoint set at index $index."
        }
        if ($lane.mountKey -notin @($hardpoint.weaponOptions)) {
            throw "Mount '$($lane.mountKey)' is not valid on $($lane.carrier) hardpoint set $index."
        }
    }
}

Write-Output "Validated mission: $missionPath"
Write-Output "Lanes: $($lanes.Count) ($($liveKeys.Count) live, $($lanes.Count - $liveKeys.Count) reserved or blocked)"
Write-Output "Units: $($allUnits.Count) across $($zoneIds.Count) test zones"
Write-Output $(if ($SkipRuntimeSchema) { "Runtime schema: skipped" } else { "Runtime schema: $SchemaPath" })
