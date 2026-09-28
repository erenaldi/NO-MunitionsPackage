using BepInEx.Logging;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using System;
using System.Collections;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Runtime.CompilerServices;
using System.Text;
using System.Text.RegularExpressions;
using UnityEngine;

namespace Erenaldi.MunitionsPackage
{
    internal sealed class WeaponSchemaDumper
    {
        private const int DumpSchemaVersion = 1;

        private static readonly string[] AnalogNames =
        {
            "AAM-36 Scimitar",
            "AAM-29 Scythe",
            "MMR-S3",
            "AGM-68",
            "AGM-99",
            "ARAD-116",
            "AGM-48",
            "GPO-2P Auger",
            "Demolition Bomb",
            "AGR-18 Lynchpin",
            "ALND-4",
            "ALM-C450",
            "Tusko-B",
            "AShM3",
            "Piledriver TBM",
            "AShM-200",
            "AShM-300"
        };

        private readonly ManualLogSource log;
        private readonly int maxDepth;
        private readonly int maxCollectionItems;

        public WeaponSchemaDumper(ManualLogSource log, int maxDepth, int maxCollectionItems)
        {
            this.log = log;
            this.maxDepth = maxDepth;
            this.maxCollectionItems = maxCollectionItems;
        }

        public void Dump(string outputDirectory)
        {
            var weapons = Encyclopedia.WeaponLookup
                .OrderBy(pair => pair.Key, StringComparer.Ordinal)
                .Select(pair => new WeaponRecord(pair.Key, pair.Value))
                .ToList();

            var schema = new JObject
            {
                ["schemaVersion"] = DumpSchemaVersion,
                ["generatedUtc"] = DateTime.UtcNow.ToString("O", CultureInfo.InvariantCulture),
                ["gameVersion"] = Application.version,
                ["pluginVersion"] = Plugin.PluginVersion,
                ["determinismNote"] = "Deterministic apart from generatedUtc, instanceId runtime IDs, runtime active/enabled state and runtime-computed bounds; the dump reads game assets without mutating them.",
                ["weaponCount"] = weapons.Count,
                ["unitCount"] = Encyclopedia.Lookup.Count,
                ["types"] = DumpTypeSchemas(weapons),
                ["weapons"] = new JArray(weapons.Select(DumpWeapon)),
                ["cargoMissiles"] = DumpCargoMissiles(weapons),
                ["aircraftHardpoints"] = DumpAircraftHardpoints()
            };

            var mappings = new JArray(AnalogNames.Select(name => ResolveAnalog(name, weapons)));
            var validation = new JObject
            {
                ["schemaVersion"] = DumpSchemaVersion,
                ["generatedUtc"] = DateTime.UtcNow.ToString("O", CultureInfo.InvariantCulture),
                ["gameVersion"] = Application.version,
                ["analogs"] = mappings,
                ["capabilityChecks"] = BuildCapabilityChecks(weapons, mappings)
            };

            var schemaPath = Path.Combine(outputDirectory, "weapon-schema.json");
            var validationPath = Path.Combine(outputDirectory, "analog-validation.json");
            WriteJson(schemaPath, schema);
            WriteJson(validationPath, validation);

            var missing = mappings.Count(item => string.Equals((string)item["status"], "missing", StringComparison.Ordinal));
            var ambiguous = mappings.Count(item => string.Equals((string)item["status"], "ambiguous", StringComparison.Ordinal));
            log.LogInfo($"Phase 1 weapon schema written to {schemaPath}");
            log.LogInfo($"Phase 1 analog validation written to {validationPath}");
            if (missing > 0 || ambiguous > 0)
            {
                log.LogWarning($"Phase 1 analog validation requires review: {missing} missing, {ambiguous} ambiguous.");
            }
            else
            {
                log.LogInfo("Phase 1 analog validation resolved every requested vanilla analog uniquely.");
            }
        }

        private JArray DumpTypeSchemas(IReadOnlyCollection<WeaponRecord> weapons)
        {
            var types = new HashSet<Type>
            {
                typeof(WeaponMount),
                typeof(WeaponInfo),
                typeof(UnitDefinition),
                typeof(MissileDefinition),
                typeof(Missile),
                typeof(MissileSeeker),
                typeof(MissileLauncher),
                typeof(MountedCargo),
                typeof(WeaponManager),
                typeof(HardpointSet),
                typeof(JammingPod),
                typeof(RadarJammer),
                typeof(PowerSupply)
            };

            foreach (var weapon in weapons)
            {
                AddComponentTypes(types, weapon.Mount?.prefab);
                AddComponentTypes(types, weapon.Mount?.info?.weaponPrefab);
            }

            // Deployed-cargo turrets (RAM45, LCV25 SAM, Hexhound) carry their
            // launchers on the cargo unit prefab, not the mount prefab.
            foreach (var cargoPrefab in CollectCargoUnitPrefabs(weapons))
            {
                AddComponentTypes(types, cargoPrefab);
            }

            return new JArray(types
                .OrderBy(type => type.FullName, StringComparer.Ordinal)
                .Select(DumpTypeSchema));
        }

        private static void AddComponentTypes(ISet<Type> types, GameObject prefab)
        {
            if (prefab == null)
            {
                return;
            }

            foreach (var component in prefab.GetComponentsInChildren<Component>(true))
            {
                if (component != null)
                {
                    types.Add(component.GetType());
                }
            }
        }

        private JObject DumpTypeSchema(Type type)
        {
            var fields = new JArray(GetInstanceFields(type).Select(field => new JObject
            {
                ["declaringType"] = field.DeclaringType?.FullName,
                ["name"] = field.Name,
                ["fieldType"] = FriendlyTypeName(field.FieldType),
                ["public"] = field.IsPublic,
                ["serialized"] = IsUnitySerialized(field),
                ["nonSerialized"] = field.IsNotSerialized
            }));

            var properties = new JArray(type
                .GetProperties(BindingFlags.Instance | BindingFlags.Public)
                .Where(property => property.GetIndexParameters().Length == 0)
                .OrderBy(property => property.Name, StringComparer.Ordinal)
                .Select(property => new JObject
                {
                    ["name"] = property.Name,
                    ["propertyType"] = FriendlyTypeName(property.PropertyType),
                    ["readable"] = property.CanRead,
                    ["writable"] = property.CanWrite
                }));

            return new JObject
            {
                ["type"] = type.FullName,
                ["assembly"] = type.Assembly.GetName().Name,
                ["baseType"] = type.BaseType?.FullName,
                ["fields"] = fields,
                ["properties"] = properties
            };
        }

        private JObject DumpWeapon(WeaponRecord weapon)
        {
            var mount = weapon.Mount;
            return new JObject
            {
                ["lookupKey"] = weapon.Key,
                ["mountObjectName"] = mount != null ? mount.name : null,
                ["mount"] = DumpSerializedObject(mount),
                ["weaponInfo"] = DumpSerializedObject(mount?.info),
                ["mountPrefab"] = DumpMountPrefab(mount?.prefab),
                ["projectilePrefab"] = DumpPrefab(mount?.info?.weaponPrefab)
            };
        }

        private JArray DumpAircraftHardpoints()
        {
            var result = new JArray();
            foreach (var pair in Encyclopedia.Lookup.OrderBy(pair => pair.Key, StringComparer.Ordinal))
            {
                if (!(pair.Value is AircraftDefinition aircraft) || aircraft.unitPrefab == null)
                {
                    continue;
                }

                var manager = aircraft.unitPrefab.GetComponentInChildren<WeaponManager>(true);
                var hardpoints = new JArray();
                if (manager?.hardpointSets != null)
                {
                    for (var index = 0; index < manager.hardpointSets.Length; index++)
                    {
                        var set = manager.hardpointSets[index];
                        hardpoints.Add(set == null ? JValue.CreateNull() : new JObject
                        {
                            ["index"] = index,
                            ["name"] = set.name,
                            ["symmetryWithPrevious"] = set.SymmetryWithPrev,
                            ["symmetryName"] = set.SymmetryName,
                            ["precludingHardpointSets"] = new JArray((set.precludingHardpointSets ?? new List<byte>()).Select(value => (int)value)),
                            ["physicalHardpointCount"] = set.hardpoints?.Count ?? 0,
                            ["weaponOptions"] = new JArray((set.weaponOptions ?? new List<WeaponMount>())
                                .Where(option => option != null)
                                .Select(option => option.jsonKey)),
                            ["physicalHardpoints"] = DumpPhysicalHardpoints(aircraft.unitPrefab.transform, set.hardpoints)
                        });
                    }
                }

                var doorBayGearCandidates = DumpDoorBayGearCandidates(aircraft.unitPrefab);
                result.Add(new JObject
                {
                    ["lookupKey"] = pair.Key,
                    ["unitName"] = aircraft.unitName,
                    ["prefabName"] = aircraft.unitPrefab.name,
                    ["hardpoints"] = hardpoints,
                    ["contextBounds"] = DumpAircraftContextBounds(aircraft.unitPrefab),
                    ["doorBayGearCandidates"] = doorBayGearCandidates,
                    ["namedGaps"] = BuildNamedGaps(doorBayGearCandidates)
                });
            }

            return result;
        }

        private JArray DumpPhysicalHardpoints(Transform root, List<Hardpoint> hardpoints)
        {
            var result = new JArray();
            if (hardpoints == null)
            {
                return result;
            }
            for (var index = 0; index < hardpoints.Count; index++)
            {
                var hardpoint = hardpoints[index];
                if (hardpoint == null)
                {
                    result.Add(JValue.CreateNull());
                    continue;
                }
                string componentType = null;
                try
                {
                    componentType = hardpoint.GetType().FullName;
                }
                catch
                {
                }
                try
                {
                    var transform = hardpoint.transform;
                    if (transform == null)
                    {
                        result.Add(new JObject
                        {
                            ["physicalIndex"] = index,
                            ["componentType"] = componentType,
                            ["$error"] = "Hardpoint has no transform."
                        });
                        continue;
                    }
                    var gameObject = transform.gameObject;
                    result.Add(new JObject
                    {
                        ["physicalIndex"] = index,
                        ["hierarchyPath"] = GetHierarchyPath(root, transform),
                        ["activeSelf"] = gameObject != null && gameObject.activeSelf,
                        ["activeInHierarchy"] = gameObject != null && gameObject.activeInHierarchy,
                        ["componentType"] = componentType,
                        ["instanceId"] = gameObject != null ? gameObject.GetInstanceID() : 0,
                        ["localTransform"] = DumpLocalPose(transform),
                        ["rootRelativeTransform"] = DumpRootRelativePose(root, transform)
                    });
                }
                catch (Exception exception)
                {
                    result.Add(new JObject
                    {
                        ["physicalIndex"] = index,
                        ["componentType"] = componentType,
                        ["$error"] = exception.GetType().Name,
                        ["message"] = exception.Message
                    });
                }
            }
            return result;
        }

        private JObject DumpAircraftContextBounds(GameObject aircraft)
        {
            var matrix = aircraft.transform.worldToLocalMatrix;
            return new JObject
            {
                ["coordinateSpace"] = "aircraft-root-local space",
                ["renderers"] = MergeBounds<Renderer>(aircraft, matrix, renderer => renderer.bounds),
                ["colliders"] = MergeBounds<Collider>(aircraft, matrix, collider => collider.bounds)
            };
        }

        private static JObject MergeBounds<T>(GameObject root, Matrix4x4 matrix, Func<T, Bounds> selector) where T : Component
        {
            var min = new Vector3(float.PositiveInfinity, float.PositiveInfinity, float.PositiveInfinity);
            var max = new Vector3(float.NegativeInfinity, float.NegativeInfinity, float.NegativeInfinity);
            var count = 0;
            foreach (var component in root.GetComponentsInChildren<T>(true))
            {
                if (component == null)
                {
                    continue;
                }
                var bounds = selector(component);
                if (!IsFiniteBounds(bounds) || IsDegenerateBounds(bounds))
                {
                    continue;
                }
                foreach (var corner in BoundsCorners(bounds))
                {
                    var point = matrix.MultiplyPoint3x4(corner);
                    min = Vector3.Min(min, point);
                    max = Vector3.Max(max, point);
                }
                count++;
            }
            if (count == 0)
            {
                return new JObject { ["count"] = 0, ["min"] = null, ["max"] = null, ["size"] = null };
            }
            return new JObject
            {
                ["count"] = count,
                ["min"] = Vector3ToObject(min),
                ["max"] = Vector3ToObject(max),
                ["size"] = Vector3ToObject(max - min)
            };
        }

        private static readonly string[] DoorBayGearPatterns =
        {
            "door", "bay", "gear", "wheel", "hatch", "landing"
        };

        private JArray DumpDoorBayGearCandidates(GameObject aircraft)
        {
            var candidates = new List<JObject>();
            foreach (var transform in aircraft.GetComponentsInChildren<Transform>(true))
            {
                if (transform == null || transform == aircraft.transform)
                {
                    continue;
                }
                var lower = (transform.name ?? string.Empty).ToLowerInvariant();
                var matched = DoorBayGearPatterns.FirstOrDefault(pattern => lower.IndexOf(pattern, StringComparison.Ordinal) >= 0);
                if (matched == null)
                {
                    continue;
                }
                candidates.Add(new JObject
                {
                    ["hierarchyPath"] = GetHierarchyPath(aircraft.transform, transform),
                    ["matchedPattern"] = matched,
                    ["identification"] = "name-heuristic",
                    ["certainty"] = "candidate",
                    ["activeSelf"] = transform.gameObject != null && transform.gameObject.activeSelf
                });
            }
            return new JArray(candidates.OrderBy(candidate => (string)candidate["hierarchyPath"], StringComparer.Ordinal));
        }

        private static JArray BuildNamedGaps(JArray doorBayGearCandidates)
        {
            var gaps = new JArray(
                "Door/bay/gear transforms are name-heuristic candidates only; their relationship to specific hardpoints is not asserted.",
                "Door sweep, bay opening animation and landing-gear travel are not measured in this dump.");
            if (doorBayGearCandidates == null || doorBayGearCandidates.Count == 0)
            {
                gaps.Add("No door/bay/gear transforms matched the name heuristics for this aircraft.");
            }
            return gaps;
        }

        private static IEnumerable<GameObject> CollectCargoUnitPrefabs(IReadOnlyCollection<WeaponRecord> weapons)
        {
            var seen = new HashSet<int>();
            foreach (var weapon in weapons)
            {
                var prefab = weapon.Mount?.prefab;
                if (prefab == null)
                {
                    continue;
                }
                foreach (var cargo in prefab.GetComponentsInChildren<MountedCargo>(true))
                {
                    var unitPrefab = cargo != null && cargo.cargo != null ? cargo.cargo.unitPrefab : null;
                    if (unitPrefab != null && seen.Add(unitPrefab.GetInstanceID()))
                    {
                        yield return unitPrefab;
                    }
                }
            }
        }

        private JArray DumpCargoMissiles(IReadOnlyCollection<WeaponRecord> weapons)
        {
            var records = new Dictionary<int, JObject>();
            var order = new List<JObject>();
            foreach (var weapon in weapons)
            {
                var prefab = weapon.Mount?.prefab;
                if (prefab == null)
                {
                    continue;
                }
                foreach (var cargo in prefab.GetComponentsInChildren<MountedCargo>(true))
                {
                    var definition = cargo != null ? cargo.cargo : null;
                    if (definition == null)
                    {
                        continue;
                    }
                    int definitionId = definition.GetInstanceID();
                    if (records.TryGetValue(definitionId, out var existing))
                    {
                        var sources = (JArray)existing["sourceMounts"];
                        if (sources.All(token => !string.Equals((string)token, weapon.Key, StringComparison.Ordinal)))
                        {
                            sources.Add(weapon.Key);
                        }
                        continue;
                    }

                    var launchers = definition.unitPrefab != null
                        ? definition.unitPrefab.GetComponentsInChildren<MissileLauncher>(true)
                        : Array.Empty<MissileLauncher>();
                    var missileDefinitions = new JArray();
                    var seenMissiles = new HashSet<int>();
                    foreach (var launcher in launchers)
                    {
                        var missile = launcher != null ? launcher.missile : null;
                        if (missile == null || !seenMissiles.Add(missile.GetInstanceID()))
                        {
                            continue;
                        }
                        missileDefinitions.Add(new JObject
                        {
                            ["jsonKey"] = missile.jsonKey,
                            ["unitName"] = missile.unitName,
                            ["definition"] = DumpSerializedObject(missile),
                            ["unitPrefab"] = DumpPrefab(missile.unitPrefab)
                        });
                    }

                    var record = new JObject
                    {
                        ["sourceMounts"] = new JArray(weapon.Key),
                        ["cargo"] = new JObject
                        {
                            ["jsonKey"] = definition.jsonKey,
                            ["unitName"] = definition.unitName,
                            ["prefabName"] = definition.unitPrefab != null ? definition.unitPrefab.name : null
                        },
                        ["missileLaunchers"] = new JArray(launchers.Select(launcher => new JObject
                        {
                            ["hierarchyPath"] = launcher != null && definition.unitPrefab != null
                                ? GetHierarchyPath(definition.unitPrefab.transform, launcher.transform)
                                : launcher != null ? launcher.name : null,
                            ["serialized"] = DumpSerializedObject(launcher)
                        })),
                        ["missileDefinitions"] = missileDefinitions
                    };
                    records[definitionId] = record;
                    order.Add(record);
                }
            }

            if (order.Count > 0)
            {
                log.LogInfo($"Phase 1 dumped {order.Count} deployed-cargo missile payload(s) for turret mounts.");
            }
            return new JArray(order);
        }

        private JObject ResolveAnalog(string analogName, IReadOnlyCollection<WeaponRecord> weapons)
        {
            var normalizedAnalog = Normalize(analogName);
            var matches = weapons
                .Where(weapon => weapon.SearchValues.Any(value => Normalize(value) == normalizedAnalog))
                .ToList();

            if (matches.Count == 0)
            {
                var designation = analogName.Split(' ')[0];
                matches = weapons
                    .Where(weapon => Normalize(designation).Length >= 4 && weapon.SearchValues.Any(value => StartsWithDesignation(value, designation)))
                    .ToList();
            }

            matches = matches
                .OrderBy(MatchPenalty)
                .ThenBy(weapon => weapon.Key, StringComparer.Ordinal)
                .ToList();
            var definitionVariantCount = matches
                .Select(weapon => weapon.Mount?.info?.weaponPrefab != null
                    ? weapon.Mount.info.weaponPrefab.GetInstanceID()
                    : weapon.Mount?.info != null ? weapon.Mount.info.GetInstanceID() : 0)
                .Distinct()
                .Count();
            var status = matches.Count == 0
                ? "missing"
                : definitionVariantCount <= 1 ? "resolved" : "ambiguous";

            return new JObject
            {
                ["requestedAnalog"] = analogName,
                ["status"] = status,
                ["mountVariantCount"] = matches.Count,
                ["definitionVariantCount"] = definitionVariantCount,
                ["preferredMatch"] = matches.Count > 0 ? DumpMatchSummary(matches[0]) : null,
                ["matches"] = new JArray(matches.Select(DumpMatchSummary))
            };
        }

        private static int MatchPenalty(WeaponRecord weapon)
        {
            var score = 0;
            if (weapon.Key.StartsWith("P_", StringComparison.OrdinalIgnoreCase))
            {
                score += 100;
            }
            if (weapon.Key.IndexOf("cluster", StringComparison.OrdinalIgnoreCase) >= 0 ||
                weapon.Key.IndexOf("mini", StringComparison.OrdinalIgnoreCase) >= 0 ||
                weapon.Key.IndexOf("mirv", StringComparison.OrdinalIgnoreCase) >= 0 ||
                weapon.Key.IndexOf("nuke", StringComparison.OrdinalIgnoreCase) >= 0)
            {
                score += 50;
            }
            if (!weapon.Key.EndsWith("_single", StringComparison.OrdinalIgnoreCase))
            {
                score += 10;
            }
            return score;
        }

        private JObject DumpMatchSummary(WeaponRecord weapon)
        {
            var info = weapon.Mount?.info;
            return new JObject
            {
                ["lookupKey"] = weapon.Key,
                ["mountName"] = weapon.Mount?.mountName,
                ["weaponName"] = info?.weaponName,
                ["shortName"] = info?.shortName,
                ["projectilePrefab"] = info?.weaponPrefab != null ? info.weaponPrefab.name : null,
                ["componentTypes"] = ComponentTypeNames(info?.weaponPrefab)
            };
        }

        private JObject BuildCapabilityChecks(IReadOnlyCollection<WeaponRecord> weapons, JArray mappings)
        {
            var scythe = FindPreferredMatch("AAM-29 Scythe", weapons, mappings);
            var phantom = FindPreferredMatch("AGM-48", weapons, mappings);
            var hailstorm = FindPreferredMatch("AGR-18 Lynchpin", weapons, mappings);

            return new JObject
            {
                ["dualSeekerOnScythe"] = SeekerCapability(scythe, MappingStatus("AAM-29 Scythe", mappings)),
                ["signatureFieldsForPhantom"] = FindRelevantFields(phantom, "rcs", "radar", "signature"),
                ["accuracyFieldsForHailstorm"] = FindRelevantFields(hailstorm, "accuracy", "dispersion", "error", "scatter", "spread"),
                ["waterRelatedFields"] = FindFieldsAcrossTypes(weapons, "water", "buoy", "underwater", "ocean"),
                ["notes"] = new JArray(
                    "Field presence does not prove runtime behavior; targeted spikes remain required.",
                    "Multiple seeker components do not prove that the launch and network paths support simultaneous seekers.",
                    "Water-phase support requires a physics and networking spike even if water-related fields are present.")
            };
        }

        private static WeaponRecord FindPreferredMatch(string name, IReadOnlyCollection<WeaponRecord> weapons, JArray mappings)
        {
            var mapping = mappings
                .OfType<JObject>()
                .FirstOrDefault(item => string.Equals((string)item["requestedAnalog"], name, StringComparison.Ordinal));
            var key = (string)mapping?["preferredMatch"]?["lookupKey"];
            return key == null ? null : weapons.FirstOrDefault(weapon => string.Equals(weapon.Key, key, StringComparison.Ordinal));
        }

        private static string MappingStatus(string name, JArray mappings)
        {
            return (string)mappings
                .OfType<JObject>()
                .FirstOrDefault(item => string.Equals((string)item["requestedAnalog"], name, StringComparison.Ordinal))?["status"];
        }

        private JObject SeekerCapability(WeaponRecord weapon, string mappingStatus)
        {
            var seekers = weapon?.Mount?.info?.weaponPrefab == null
                ? Array.Empty<MissileSeeker>()
                : weapon.Mount.info.weaponPrefab.GetComponentsInChildren<MissileSeeker>(true);

            return new JObject
            {
                ["analogFound"] = weapon != null,
                ["mappingStatus"] = mappingStatus,
                ["seekerCount"] = seekers.Length,
                ["seekerTypes"] = new JArray(seekers.Where(seeker => seeker != null).Select(seeker => seeker.GetType().FullName)),
                ["dualSeekerDefinitionObserved"] = seekers.Select(seeker => seeker?.GetType()).Where(type => type != null).Distinct().Count() > 1
            };
        }

        private JArray FindRelevantFields(WeaponRecord weapon, params string[] terms)
        {
            if (weapon == null)
            {
                return new JArray();
            }

            var types = new HashSet<Type> { typeof(WeaponMount), typeof(WeaponInfo) };
            AddComponentTypes(types, weapon.Mount?.prefab);
            AddComponentTypes(types, weapon.Mount?.info?.weaponPrefab);
            return FieldMatches(types, terms);
        }

        private JArray FindFieldsAcrossTypes(IEnumerable<WeaponRecord> weapons, params string[] terms)
        {
            var types = new HashSet<Type>();
            foreach (var weapon in weapons)
            {
                AddComponentTypes(types, weapon.Mount?.prefab);
                AddComponentTypes(types, weapon.Mount?.info?.weaponPrefab);
            }
            return FieldMatches(types, terms);
        }

        private static JArray FieldMatches(IEnumerable<Type> types, IEnumerable<string> terms)
        {
            var normalizedTerms = terms.Select(term => term.ToLowerInvariant()).ToArray();
            var matches = types
                .SelectMany(type => GetInstanceFields(type))
                .Where(IsUnitySerialized)
                .Where(field => normalizedTerms.Any(term => field.Name.ToLowerInvariant().Contains(term)))
                .Select(field => $"{field.DeclaringType?.FullName}.{field.Name}: {FriendlyTypeName(field.FieldType)}")
                .Distinct(StringComparer.Ordinal)
                .OrderBy(value => value, StringComparer.Ordinal);
            return new JArray(matches);
        }

        private JObject DumpPrefab(GameObject prefab)
        {
            if (prefab == null)
            {
                return null;
            }

            var components = new JArray();
            foreach (var component in prefab.GetComponentsInChildren<Component>(true))
            {
                if (component == null)
                {
                    components.Add(new JObject { ["missingScript"] = true });
                    continue;
                }

                components.Add(new JObject
                {
                    ["hierarchyPath"] = GetHierarchyPath(prefab.transform, component.transform),
                    ["type"] = component.GetType().FullName,
                    ["serializedFields"] = DumpSerializedObject(component)
                });
            }

            return new JObject
            {
                ["name"] = prefab.name,
                ["layer"] = prefab.layer,
                ["componentCount"] = components.Count,
                ["components"] = components
            };
        }

        private JObject DumpMountPrefab(GameObject prefab)
        {
            if (prefab == null)
            {
                return null;
            }
            var result = DumpPrefab(prefab);
            result["transforms"] = DumpTransformHierarchy(prefab);
            result["renderers"] = DumpRendererBounds(prefab);
            result["colliders"] = DumpColliderBounds(prefab);
            result["mountedMissiles"] = DumpMountedMissiles(prefab);
            return result;
        }

        private JArray DumpTransformHierarchy(GameObject prefab)
        {
            var result = new JArray();
            foreach (var transform in prefab.GetComponentsInChildren<Transform>(true))
            {
                if (transform == null)
                {
                    continue;
                }
                var isRoot = transform == prefab.transform;
                result.Add(new JObject
                {
                    ["hierarchyPath"] = GetHierarchyPath(prefab.transform, transform),
                    ["isRoot"] = isRoot,
                    ["poseCoordinateSpace"] = isRoot ? "prefab-root parent space" : "parent transform space",
                    ["activeSelf"] = transform.gameObject != null && transform.gameObject.activeSelf,
                    ["localPosition"] = Vector3ToObject(transform.localPosition),
                    ["localRotation"] = QuaternionToObject(transform.localRotation),
                    ["localScale"] = Vector3ToObject(transform.localScale)
                });
            }
            return result;
        }

        private JArray DumpRendererBounds(GameObject prefab)
        {
            var result = new JArray();
            var matrix = prefab.transform.worldToLocalMatrix;
            foreach (var renderer in prefab.GetComponentsInChildren<Renderer>(true))
            {
                if (renderer == null)
                {
                    continue;
                }
                result.Add(new JObject
                {
                    ["hierarchyPath"] = GetHierarchyPath(prefab.transform, renderer.transform),
                    ["type"] = renderer.GetType().FullName,
                    ["enabled"] = renderer.enabled,
                    ["bounds"] = BoundsToObject(renderer.bounds, matrix, "prefab-root-local space"),
                    ["worldBounds"] = BoundsToObject(renderer.bounds, Matrix4x4.identity, "world space")
                });
            }
            return result;
        }

        private JArray DumpColliderBounds(GameObject prefab)
        {
            var result = new JArray();
            var matrix = prefab.transform.worldToLocalMatrix;
            foreach (var collider in prefab.GetComponentsInChildren<Collider>(true))
            {
                if (collider == null)
                {
                    continue;
                }
                var entry = new JObject
                {
                    ["hierarchyPath"] = GetHierarchyPath(prefab.transform, collider.transform),
                    ["type"] = collider.GetType().FullName,
                    ["enabled"] = collider.enabled,
                    ["bounds"] = BoundsToObject(collider.bounds, matrix, "prefab-root-local space"),
                    ["worldBounds"] = BoundsToObject(collider.bounds, Matrix4x4.identity, "world space")
                };
                if (collider is BoxCollider box)
                {
                    entry["shapeCoordinateSpace"] = "collider-local space";
                    entry["center"] = Vector3ToObject(box.center);
                    entry["size"] = Vector3ToObject(box.size);
                }
                else if (collider is SphereCollider sphere)
                {
                    entry["shapeCoordinateSpace"] = "collider-local space";
                    entry["center"] = Vector3ToObject(sphere.center);
                    entry["radius"] = sphere.radius;
                }
                else if (collider is CapsuleCollider capsule)
                {
                    entry["shapeCoordinateSpace"] = "collider-local space";
                    entry["center"] = Vector3ToObject(capsule.center);
                    entry["radius"] = capsule.radius;
                    entry["height"] = capsule.height;
                    entry["direction"] = capsule.direction;
                    entry["directionAxis"] = CapsuleDirectionName(capsule.direction);
                }
                else if (collider is MeshCollider meshCollider)
                {
                    entry["sharedMesh"] = meshCollider.sharedMesh != null ? meshCollider.sharedMesh.name : null;
                    entry["convex"] = meshCollider.convex;
                }
                result.Add(entry);
            }
            return result;
        }

        private JArray DumpMountedMissiles(GameObject prefab)
        {
            var result = new JArray();
            foreach (var mounted in prefab.GetComponentsInChildren<MountedMissile>(true))
            {
                if (mounted == null)
                {
                    continue;
                }
                var entry = new JObject
                {
                    ["hierarchyPath"] = GetHierarchyPath(prefab.transform, mounted.transform),
                    ["localPose"] = DumpLocalPose(mounted.transform)
                };
                TryAddMountedMissileField(entry, "railDirection", mounted, "railDirection");
                TryAddMountedMissileField(entry, "railLength", mounted, "railLength");
                TryAddMountedMissileField(entry, "railSpeed", mounted, "railSpeed");
                TryAddMountedMissileField(entry, "railDelay", mounted, "railDelay");
                TryAddMountedMissileField(entry, "mountedPosition", mounted, "mountedPosition");
                TryAddMountedMissileField(entry, "railVector", mounted, "railVector");
                result.Add(entry);
            }
            return result;
        }

        private static void TryAddMountedMissileField(JObject target, string name, MountedMissile mounted, string fieldName)
        {
            try
            {
                var value = HalberdCloner.GetField(mounted, fieldName);
                if (value is Vector3 vector)
                {
                    target[name] = Vector3ToObject(vector);
                }
                else if (value is Enum enumValue)
                {
                    target[name] = DumpEnum(enumValue);
                }
                else if (value is float number)
                {
                    target[name] = number;
                }
                else if (value != null)
                {
                    target[name] = new JValue(value.ToString());
                }
            }
            catch (Exception exception)
            {
                target[name] = new JObject { ["$error"] = exception.GetType().Name };
            }
        }

        private JObject DumpSerializedObject(object value)
        {
            if (value == null)
            {
                return null;
            }

            var result = new JObject { ["$type"] = value.GetType().FullName };
            var visited = new HashSet<object>(ReferenceComparer.Instance);
            foreach (var field in GetInstanceFields(value.GetType()).Where(IsUnitySerialized))
            {
                try
                {
                    result[field.Name] = SerializeValue(field.GetValue(value), 0, visited);
                }
                catch (Exception exception)
                {
                    result[field.Name] = new JObject
                    {
                        ["$error"] = exception.GetType().Name,
                        ["message"] = exception.Message
                    };
                }
            }
            return result;
        }

        private JToken SerializeValue(object value, int depth, ISet<object> visited)
        {
            if (value == null)
            {
                return JValue.CreateNull();
            }

            var type = value.GetType();
            if (type.IsEnum)
            {
                return new JObject
                {
                    ["name"] = value.ToString(),
                    ["value"] = Convert.ToInt64(value, CultureInfo.InvariantCulture)
                };
            }
            if (value is string || value is char || value is bool || IsNumber(type))
            {
                return new JValue(value);
            }
            if (value is UnityEngine.Object unityObject)
            {
                return DescribeUnityReference(unityObject);
            }
            if (depth >= maxDepth)
            {
                return new JObject { ["$truncatedType"] = type.FullName };
            }
            if (!type.IsValueType && !visited.Add(value))
            {
                return new JObject { ["$cycleType"] = type.FullName };
            }

            try
            {
                if (value is IDictionary dictionary)
                {
                    var dictionaryValues = new JArray();
                    var count = 0;
                    foreach (DictionaryEntry entry in dictionary)
                    {
                        if (count++ >= maxCollectionItems)
                        {
                            dictionaryValues.Add(new JObject { ["$truncated"] = true });
                            break;
                        }
                        dictionaryValues.Add(new JObject
                        {
                            ["key"] = SerializeValue(entry.Key, depth + 1, visited),
                            ["value"] = SerializeValue(entry.Value, depth + 1, visited)
                        });
                    }
                    return dictionaryValues;
                }
                if (value is IEnumerable enumerable)
                {
                    var array = new JArray();
                    var count = 0;
                    foreach (var item in enumerable)
                    {
                        if (count++ >= maxCollectionItems)
                        {
                            array.Add(new JObject { ["$truncated"] = true });
                            break;
                        }
                        array.Add(SerializeValue(item, depth + 1, visited));
                    }
                    return array;
                }

                var result = new JObject { ["$type"] = type.FullName };
                foreach (var field in GetInstanceFields(type).Where(IsUnitySerialized))
                {
                    try
                    {
                        result[field.Name] = SerializeValue(field.GetValue(value), depth + 1, visited);
                    }
                    catch (Exception exception)
                    {
                        result[field.Name] = new JObject { ["$error"] = exception.GetType().Name };
                    }
                }
                return result;
            }
            finally
            {
                if (!type.IsValueType)
                {
                    visited.Remove(value);
                }
            }
        }

        private static JObject DescribeUnityReference(UnityEngine.Object value)
        {
            if (value == null)
            {
                return null;
            }

            return new JObject
            {
                ["$unityReference"] = true,
                ["type"] = value.GetType().FullName,
                ["name"] = value.name,
                ["instanceId"] = value.GetInstanceID()
            };
        }

        private static JArray ComponentTypeNames(GameObject prefab)
        {
            if (prefab == null)
            {
                return new JArray();
            }

            return new JArray(prefab.GetComponentsInChildren<Component>(true)
                .Where(component => component != null)
                .Select(component => component.GetType().FullName)
                .Distinct(StringComparer.Ordinal)
                .OrderBy(name => name, StringComparer.Ordinal));
        }

        private static IEnumerable<FieldInfo> GetInstanceFields(Type type)
        {
            var hierarchy = new Stack<Type>();
            for (var current = type; current != null && current != typeof(object); current = current.BaseType)
            {
                hierarchy.Push(current);
            }

            while (hierarchy.Count > 0)
            {
                foreach (var field in hierarchy.Pop()
                    .GetFields(BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.DeclaredOnly)
                    .OrderBy(field => field.MetadataToken))
                {
                    yield return field;
                }
            }
        }

        private static bool IsUnitySerialized(FieldInfo field)
        {
            return !field.IsStatic && !field.IsLiteral && !field.IsInitOnly && !field.IsNotSerialized &&
                (field.IsPublic || field.IsDefined(typeof(SerializeField), true));
        }

        private static bool IsNumber(Type type)
        {
            return type == typeof(byte) || type == typeof(sbyte) ||
                type == typeof(short) || type == typeof(ushort) ||
                type == typeof(int) || type == typeof(uint) ||
                type == typeof(long) || type == typeof(ulong) ||
                type == typeof(float) || type == typeof(double) ||
                type == typeof(decimal);
        }

        private static string FriendlyTypeName(Type type)
        {
            if (!type.IsGenericType)
            {
                return type.FullName ?? type.Name;
            }

            var baseName = type.GetGenericTypeDefinition().FullName;
            var tick = baseName?.IndexOf('`') ?? -1;
            if (tick >= 0)
            {
                baseName = baseName.Substring(0, tick);
            }
            return $"{baseName}<{string.Join(", ", type.GetGenericArguments().Select(FriendlyTypeName))}>";
        }

        private static string GetHierarchyPath(Transform root, Transform current)
        {
            var names = new Stack<string>();
            while (current != null)
            {
                names.Push(current.name);
                if (current == root)
                {
                    break;
                }
                current = current.parent;
            }
            return string.Join("/", names);
        }

        private static JObject DumpLocalPose(Transform transform)
        {
            return new JObject
            {
                ["coordinateSpace"] = "local (parent) space",
                ["position"] = Vector3ToObject(transform.localPosition),
                ["rotation"] = QuaternionToObject(transform.localRotation),
                ["scale"] = Vector3ToObject(transform.localScale)
            };
        }

        private static JObject DumpRootRelativePose(Transform root, Transform transform)
        {
            var rootScale = root.lossyScale;
            var scale = transform.lossyScale;
            return new JObject
            {
                ["coordinateSpace"] = "aircraft-root space",
                ["position"] = Vector3ToObject(root.InverseTransformPoint(transform.position)),
                ["rotation"] = QuaternionToObject(Quaternion.Inverse(root.rotation) * transform.rotation),
                ["scale"] = Vector3ToObject(new Vector3(
                    rootScale.x != 0f ? scale.x / rootScale.x : 0f,
                    rootScale.y != 0f ? scale.y / rootScale.y : 0f,
                    rootScale.z != 0f ? scale.z / rootScale.z : 0f)),
                ["scaleNote"] = "lossy-scale ratio; approximate under nonuniform or rotated ancestry"
            };
        }

        private static JObject BoundsToObject(Bounds bounds, Matrix4x4 matrix, string coordinateSpace)
        {
            if (!IsFiniteBounds(bounds))
            {
                return new JObject
                {
                    ["coordinateSpace"] = coordinateSpace,
                    ["finite"] = false
                };
            }
            var min = new Vector3(float.PositiveInfinity, float.PositiveInfinity, float.PositiveInfinity);
            var max = new Vector3(float.NegativeInfinity, float.NegativeInfinity, float.NegativeInfinity);
            foreach (var corner in BoundsCorners(bounds))
            {
                var point = matrix.MultiplyPoint3x4(corner);
                min = Vector3.Min(min, point);
                max = Vector3.Max(max, point);
            }
            return new JObject
            {
                ["coordinateSpace"] = coordinateSpace,
                ["min"] = Vector3ToObject(min),
                ["max"] = Vector3ToObject(max),
                ["size"] = Vector3ToObject(max - min)
            };
        }

        private static IEnumerable<Vector3> BoundsCorners(Bounds bounds)
        {
            var min = bounds.min;
            var max = bounds.max;
            yield return new Vector3(min.x, min.y, min.z);
            yield return new Vector3(max.x, min.y, min.z);
            yield return new Vector3(min.x, max.y, min.z);
            yield return new Vector3(max.x, max.y, min.z);
            yield return new Vector3(min.x, min.y, max.z);
            yield return new Vector3(max.x, min.y, max.z);
            yield return new Vector3(min.x, max.y, max.z);
            yield return new Vector3(max.x, max.y, max.z);
        }

        private static bool IsFiniteBounds(Bounds bounds)
        {
            return IsFinite(bounds.min) && IsFinite(bounds.max);
        }

        private static bool IsDegenerateBounds(Bounds bounds)
        {
            var size = bounds.size;
            return size.x == 0f && size.y == 0f && size.z == 0f;
        }

        private static bool IsFinite(Vector3 value)
        {
            return float.IsFinite(value.x) && float.IsFinite(value.y) && float.IsFinite(value.z);
        }

        private static JObject Vector3ToObject(Vector3 value)
        {
            return new JObject { ["x"] = value.x, ["y"] = value.y, ["z"] = value.z };
        }

        private static JObject QuaternionToObject(Quaternion value)
        {
            return new JObject { ["x"] = value.x, ["y"] = value.y, ["z"] = value.z, ["w"] = value.w };
        }

        private static JObject DumpEnum(Enum value)
        {
            return new JObject
            {
                ["name"] = value.ToString(),
                ["value"] = Convert.ToInt64(value, CultureInfo.InvariantCulture)
            };
        }

        private static string CapsuleDirectionName(int direction)
        {
            switch (direction)
            {
                case 0:
                    return "x";
                case 1:
                    return "y";
                case 2:
                    return "z";
                default:
                    return "unknown";
            }
        }

        private static string Normalize(string value)
        {
            if (string.IsNullOrEmpty(value))
            {
                return string.Empty;
            }

            var builder = new StringBuilder(value.Length);
            foreach (var character in value)
            {
                if (char.IsLetterOrDigit(character))
                {
                    builder.Append(char.ToLowerInvariant(character));
                }
            }
            return builder.ToString();
        }

        private static bool StartsWithDesignation(string value, string designation)
        {
            var valueTokens = Regex.Matches(value ?? string.Empty, "[A-Za-z]+|[0-9]+")
                .Cast<Match>()
                .Select(match => match.Value.ToLowerInvariant())
                .ToArray();
            var designationTokens = Regex.Matches(designation ?? string.Empty, "[A-Za-z]+|[0-9]+")
                .Cast<Match>()
                .Select(match => match.Value.ToLowerInvariant())
                .ToArray();

            return designationTokens.Length > 0 && valueTokens.Length >= designationTokens.Length &&
                designationTokens.SequenceEqual(valueTokens.Take(designationTokens.Length));
        }

        private static void WriteJson(string path, JToken document)
        {
            var json = document.ToString(Formatting.Indented) + Environment.NewLine;
            File.WriteAllText(path, json, new UTF8Encoding(false));
        }

        private sealed class WeaponRecord
        {
            public WeaponRecord(string key, WeaponMount mount)
            {
                Key = key;
                Mount = mount;
                SearchValues = new[]
                {
                    key,
                    mount != null ? mount.name : null,
                    mount?.jsonKey,
                    mount?.mountName,
                    mount?.info != null ? mount.info.name : null,
                    mount?.info?.weaponName,
                    mount?.info?.shortName,
                    mount?.prefab != null ? mount.prefab.name : null,
                    mount?.info?.weaponPrefab != null ? mount.info.weaponPrefab.name : null
                }.Where(value => !string.IsNullOrWhiteSpace(value)).ToArray();
            }

            public string Key { get; }
            public WeaponMount Mount { get; }
            public string[] SearchValues { get; }
        }

        private sealed class ReferenceComparer : IEqualityComparer<object>
        {
            public static readonly ReferenceComparer Instance = new ReferenceComparer();

            public new bool Equals(object x, object y)
            {
                return ReferenceEquals(x, y);
            }

            public int GetHashCode(object value)
            {
                return RuntimeHelpers.GetHashCode(value);
            }
        }
    }
}
