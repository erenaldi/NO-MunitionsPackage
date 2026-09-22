using System.Collections.Generic;
using Erenaldi.Munitions;
using UnityEditor;
using UnityEngine;

namespace Erenaldi.Phantom
{
    public static class PhantomMeshBuilder
    {
        internal const float TotalLength = 2.8f;
        internal const float BodyRadius = 0.1002f;
        internal const float DeployedSpan = 1.3987f;
        // The retracted state must fit the 250 mm carriage envelope.
        internal const float RetractedSpan = 0.247f;
        private const float PylonTargetClearance = 0.009f;
        // Derived-engine-mesh nozzle recess (export_phantom_unity_mesh.py):
        // the approved R5 CAD has the nozzle lip coplanar with the body aft
        // cap; the exporter recesses the lip forward by this amount so the
        // nozzle reads visibly recessed without a proud lip.
        private const float NozzleRecessMeters = 0.003f;
        // Total across the four exported groups (Phantom_Export_Report.json);
        // the cylindrical unwrap adds seam-duplicate vertices, so only the
        // triangle count is fixed here.
        private const int ExpectedTriangleCount = 18846;
        private const int ExpectedRetractedTriangleCount = 25192;

        internal const string OutputRoot = "Assets/Blueprinter/Mods/PhantomMod";
        private const string ModelsRoot = OutputRoot + "/Models";
        internal const string MissilePrefabName = "Erenaldi.RDM9";
        internal const string RackPrefabName = "Erenaldi.RDM9_single";

        [MenuItem("Blueprinter/Phantom/Build Geometry")]
        public static void Build()
        {
            EnsureFolder("Assets/Blueprinter/Mods", "PhantomMod");
            EnsureFolder(OutputRoot, "Models");

            var shader = Shader.Find("Universal Render Pipeline/Lit");
            if (shader == null)
            {
                throw new System.InvalidOperationException("Required URP Lit shader is unavailable");
            }

            var bodyMaterial = PhantomTexturedMaterialBuilder.CreateBodyMaterial(OutputRoot, "MatPhantomBody");
            var wingMaterial = PhantomTexturedMaterialBuilder.CreateWingMaterial(OutputRoot, "MatPhantomWing");
            var finsMaterial = CreateFlatMaterial(shader, "MatPhantomFins", new Color(0.44f, 0.48f, 0.49f), 0.06f, 0.42f);
            var nozzleMaterial = CreateFlatMaterial(shader, "MatPhantomNozzle", new Color(0.25f, 0.28f, 0.29f), 0.12f, 0.50f);

            var bodyMesh = LoadCadMesh(ModelsRoot + "/Phantom_Body.obj", "MeshPhantomBody", true);
            var wingsMesh = LoadCadMesh(ModelsRoot + "/Phantom_Wings.obj", "MeshPhantomWings", false);
            var finsMesh = LoadCadMesh(ModelsRoot + "/Phantom_Fins.obj", "MeshPhantomFins", false);
            var nozzleMesh = LoadCadMesh(ModelsRoot + "/Phantom_Nozzle.obj", "MeshPhantomNozzle", true);
            ValidateAssembly(bodyMesh, wingsMesh, finsMesh, nozzleMesh);
            ValidateTexturedMaterials(bodyMaterial, wingMaterial);

            var retractedBodyMesh = LoadCadMesh(ModelsRoot + "/Phantom_Retracted_Body.obj", "MeshPhantomRetractedBody", true);
            var retractedWingsMesh = LoadCadMesh(ModelsRoot + "/Phantom_Retracted_Wings.obj", "MeshPhantomRetractedWings", false);
            var retractedFinsMesh = LoadCadMesh(ModelsRoot + "/Phantom_Retracted_Fins.obj", "MeshPhantomRetractedFins", false);
            var retractedNozzleMesh = LoadCadMesh(ModelsRoot + "/Phantom_Retracted_Nozzle.obj", "MeshPhantomRetractedNozzle", true);
            var retractedFairingMesh = LoadCadMesh(ModelsRoot + "/Phantom_Retracted_Fairing.obj", "MeshPhantomRetractedFairing", false);
            ValidateRetractedAssembly(retractedBodyMesh, retractedWingsMesh, retractedFinsMesh, retractedNozzleMesh, retractedFairingMesh);

            SaveAsset(bodyMesh, "MeshPhantomBody.asset");
            SaveAsset(wingsMesh, "MeshPhantomWings.asset");
            SaveAsset(finsMesh, "MeshPhantomFins.asset");
            SaveAsset(nozzleMesh, "MeshPhantomNozzle.asset");
            SaveAsset(retractedBodyMesh, "MeshPhantomRetractedBody.asset");
            SaveAsset(retractedWingsMesh, "MeshPhantomRetractedWings.asset");
            SaveAsset(retractedFinsMesh, "MeshPhantomRetractedFins.asset");
            SaveAsset(retractedNozzleMesh, "MeshPhantomRetractedNozzle.asset");
            SaveAsset(retractedFairingMesh, "MeshPhantomRetractedFairing.asset");
            SaveAsset(finsMaterial, "MatPhantomFins.mat");
            SaveAsset(nozzleMaterial, "MatPhantomNozzle.mat");

            var pylonMesh = BuildPylonMesh();
            var pylonMaterial = CreateFlatMaterial(shader, "MatPhantomPylon", new Color(0.45f, 0.47f, 0.5f), 0.06f, 0.42f);
            SaveAsset(pylonMesh, "MeshPhantomPylon.asset");
            SaveAsset(pylonMaterial, "MatPhantomPylon.mat");

            var missile = BuildMissilePrefab(bodyMesh, wingsMesh, finsMesh, nozzleMesh, bodyMaterial, wingMaterial, finsMaterial, nozzleMaterial);
            SaveAsPrefab(missile, MissilePrefabName + ".prefab");
            Object.DestroyImmediate(missile);

            var rack = BuildRackPrefab(pylonMesh, pylonMaterial, retractedBodyMesh, retractedWingsMesh, retractedFinsMesh, retractedNozzleMesh, retractedFairingMesh, bodyMaterial, wingMaterial, finsMaterial, nozzleMaterial);
            SaveAsPrefab(rack, RackPrefabName + ".prefab");
            Object.DestroyImmediate(rack);

            ValidateCandidates();

            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();
            Debug.Log("[Phantom] CAD geometry built: " + OutputRoot);
        }

        [MenuItem("Blueprinter/Phantom/Validate Candidates")]
        public static void ValidateCandidates()
        {
            var deployed = LoadPrefab(MissilePrefabName);
            var rack = LoadPrefab(RackPrefabName);
            ValidatePrefabIdentity(deployed, MissilePrefabName);
            ValidatePrefabIdentity(rack, RackPrefabName);
            ValidateDeployedHierarchy(deployed);
            ValidateRackHierarchy(rack);
            ValidateCandidateBounds(deployed, rack);
            ValidateCandidateUvs(deployed, rack);
            ValidateCandidateColliders(deployed, rack);
            ValidateMaterialConsistency(deployed, rack);
            ValidateNoReferenceAssets(OutputRoot + "/" + MissilePrefabName + ".prefab");
            ValidateNoReferenceAssets(OutputRoot + "/" + RackPrefabName + ".prefab");
            Debug.Log("[Phantom] Candidate validation passed for " + MissilePrefabName + " and " + RackPrefabName);
        }

        private static GameObject LoadPrefab(string prefabName)
        {
            var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(OutputRoot + "/" + prefabName + ".prefab");
            if (prefab == null)
            {
                throw new System.InvalidOperationException("Phantom prefab has not been built: " + prefabName);
            }
            return prefab;
        }

        private static void ValidatePrefabIdentity(GameObject prefab, string expectedName)
        {
            if (prefab.name != expectedName)
            {
                throw new System.InvalidOperationException(
                    "Phantom prefab identity is " + prefab.name + "; expected " + expectedName);
            }
        }

        private static void ValidateDeployedHierarchy(GameObject deployed)
        {
            var children = GetChildNames(deployed);
            if (!children.Contains("Wings") || !children.Contains("Fins") || !children.Contains("Nozzle") || children.Count != 3)
            {
                throw new System.InvalidOperationException(
                    "Phantom deployed prefab children are " + children + "; expected Wings/Fins/Nozzle");
            }
        }

        private static void ValidateRackHierarchy(GameObject rack)
        {
            var children = GetChildNames(rack);
            if (!children.Contains("pylon") || children.Count != 1)
            {
                throw new System.InvalidOperationException(
                    "Phantom rack prefab children are " + children + "; expected pylon");
            }
            var pylon = rack.transform.Find("pylon").gameObject;
            var pylonChildren = GetChildNames(pylon);
            if (!pylonChildren.Contains("rdm9") || pylonChildren.Count != 1)
            {
                throw new System.InvalidOperationException(
                    "Phantom rack pylon children are " + pylonChildren + "; expected rdm9");
            }
            var missile = pylon.transform.Find("rdm9").gameObject;
            var missileChildren = GetChildNames(missile);
            if (!missileChildren.Contains("Wings") || !missileChildren.Contains("Fins") ||
                !missileChildren.Contains("Nozzle") || !missileChildren.Contains("Fairing") ||
                missileChildren.Count != 4)
            {
                throw new System.InvalidOperationException(
                    "Phantom rack missile children are " + missileChildren + "; expected Wings/Fins/Nozzle/Fairing");
            }
        }

        private static List<string> GetChildNames(GameObject parent)
        {
            var names = new List<string>();
            for (int i = 0; i < parent.transform.childCount; i++)
            {
                names.Add(parent.transform.GetChild(i).name);
            }
            return names;
        }

        private static void ValidateCandidateBounds(GameObject deployed, GameObject rack)
        {
            var deployedBody = GetMeshFilter(deployed).sharedMesh;
            float deployedSpan = GetMaximumSpan(deployed);
            if (Mathf.Abs(deployedSpan - DeployedSpan) > 0.002f)
            {
                throw new System.InvalidOperationException(
                    "Phantom deployed span is " + deployedSpan.ToString("F3") + " m; expected " + DeployedSpan.ToString("F3") + " m");
            }
            ValidateLength(deployedBody, "deployed");

            var missile = rack.transform.Find("pylon").transform.Find("rdm9").gameObject;
            var retractedBody = GetMeshFilter(missile).sharedMesh;
            ValidateLength(retractedBody, "retracted");
            float retractedSpan = GetMaximumSpan(missile);
            if (Mathf.Abs(retractedSpan - RetractedSpan) > 0.002f)
            {
                throw new System.InvalidOperationException(
                    "Phantom retracted span is " + retractedSpan.ToString("F3") + " m; expected " + RetractedSpan.ToString("F3") + " m");
            }
        }

        private static void ValidateLength(Mesh bodyMesh, string state)
        {
            float nose = TotalLength * 0.5f;
            float aft = -nose;
            if (Mathf.Abs(bodyMesh.bounds.max.z - nose) > 0.001f ||
                Mathf.Abs(bodyMesh.bounds.min.z - aft) > 0.001f)
            {
                throw new System.InvalidOperationException(
                    "Phantom " + state + " body is not centered at the " + TotalLength.ToString("F3") + " m length");
            }
        }

        private static void ValidateCandidateUvs(GameObject deployed, GameObject rack)
        {
            foreach (var filter in deployed.GetComponentsInChildren<MeshFilter>(true))
            {
                if (!filter.sharedMesh.HasVertexAttribute(UnityEngine.Rendering.VertexAttribute.TexCoord0))
                {
                    throw new System.InvalidOperationException("Phantom deployed mesh has no UVs: " + filter.sharedMesh.name);
                }
            }
            foreach (var filter in rack.GetComponentsInChildren<MeshFilter>(true))
            {
                if (!filter.sharedMesh.HasVertexAttribute(UnityEngine.Rendering.VertexAttribute.TexCoord0))
                {
                    throw new System.InvalidOperationException("Phantom rack mesh has no UVs: " + filter.sharedMesh.name);
                }
            }
        }

        private static void ValidateCandidateColliders(GameObject deployed, GameObject rack)
        {
            if (deployed.GetComponent<CapsuleCollider>() == null)
            {
                throw new System.InvalidOperationException("Phantom deployed prefab has no body capsule collider");
            }
            var pylon = rack.transform.Find("pylon").gameObject;
            if (pylon.GetComponent<BoxCollider>() == null)
            {
                throw new System.InvalidOperationException("Phantom rack pylon has no box collider");
            }
            var missile = pylon.transform.Find("rdm9").gameObject;
            if (missile.GetComponent<CapsuleCollider>() == null)
            {
                throw new System.InvalidOperationException("Phantom rack missile has no body capsule collider");
            }
        }

        /// <summary>
        /// The retracted rack display must share the deployed candidate's
        /// material assets: body material on the body and hinge fairing, wing
        /// material on the stowed stack, fins/nozzle materials on their groups.
        /// </summary>
        private static void ValidateMaterialConsistency(GameObject deployed, GameObject rack)
        {
            var deployedBodyMaterial = GetMeshRenderer(deployed).sharedMaterial;
            var deployedWingsMaterial = GetMeshRenderer(deployed.transform.Find("Wings").gameObject).sharedMaterial;
            var deployedFinsMaterial = GetMeshRenderer(deployed.transform.Find("Fins").gameObject).sharedMaterial;
            var deployedNozzleMaterial = GetMeshRenderer(deployed.transform.Find("Nozzle").gameObject).sharedMaterial;

            var missile = rack.transform.Find("pylon").transform.Find("rdm9").gameObject;
            var rackBodyMaterial = GetMeshRenderer(missile).sharedMaterial;
            var rackWingsMaterial = GetMeshRenderer(missile.transform.Find("Wings").gameObject).sharedMaterial;
            var rackFinsMaterial = GetMeshRenderer(missile.transform.Find("Fins").gameObject).sharedMaterial;
            var rackNozzleMaterial = GetMeshRenderer(missile.transform.Find("Nozzle").gameObject).sharedMaterial;
            var rackFairingMaterial = GetMeshRenderer(missile.transform.Find("Fairing").gameObject).sharedMaterial;

            AssertSameMaterial(rackBodyMaterial, deployedBodyMaterial, "body");
            AssertSameMaterial(rackWingsMaterial, deployedWingsMaterial, "wings");
            AssertSameMaterial(rackFinsMaterial, deployedFinsMaterial, "fins");
            AssertSameMaterial(rackNozzleMaterial, deployedNozzleMaterial, "nozzle");
            AssertSameMaterial(rackFairingMaterial, deployedBodyMaterial, "fairing");
        }

        private static void AssertSameMaterial(Material actual, Material expected, string label)
        {
            string actualPath = AssetDatabase.GetAssetPath(actual);
            string expectedPath = AssetDatabase.GetAssetPath(expected);
            if (actualPath != expectedPath)
            {
                throw new System.InvalidOperationException(
                    "Phantom rack " + label + " material " + actualPath + " does not match deployed " + expectedPath);
            }
        }

        private static MeshFilter GetMeshFilter(GameObject target)
        {
            var filter = target.GetComponent<MeshFilter>();
            if (filter == null)
            {
                throw new System.InvalidOperationException("Phantom prefab node has no mesh filter: " + target.name);
            }
            return filter;
        }

        private static MeshRenderer GetMeshRenderer(GameObject target)
        {
            var renderer = target.GetComponent<MeshRenderer>();
            if (renderer == null)
            {
                throw new System.InvalidOperationException("Phantom prefab node has no mesh renderer: " + target.name);
            }
            return renderer;
        }

        private static float GetMaximumSpan(GameObject root)
        {
            float maximum = 0f;
            foreach (var filter in root.GetComponentsInChildren<MeshFilter>(true))
            {
                var bounds = filter.sharedMesh.bounds;
                maximum = Mathf.Max(maximum, Mathf.Max(bounds.size.x, bounds.size.y));
            }
            return maximum;
        }

        private static Mesh LoadCadMesh(string path, string meshName, bool cylindrical)
        {
            Mesh source = null;
            foreach (var asset in AssetDatabase.LoadAllAssetsAtPath(path))
            {
                source = asset as Mesh;
                if (source != null)
                {
                    break;
                }
            }
            if (source == null)
            {
                throw new System.InvalidOperationException("No mesh found in CAD model: " + path);
            }

            var mesh = Object.Instantiate(source);
            mesh.name = meshName;
            mesh.RecalculateNormals();
            // Recalculate bounds BEFORE the unwrap so v is normalized against
            // the imported bounds (the Kris body unwrap convention).
            mesh.RecalculateBounds();
            // Body/nozzle groups get the seam-deduplicated full-2pi cylindrical
            // unwrap (z-axis, v 0 tail .. 1 nose); the flat wing/fin panels get
            // a planar unwrap instead (cylindrical mapping degenerates on a
            // flat panel).
            var unwrapped = cylindrical
                ? Erenaldi.Kris.KrisMeshBuilder.GenerateCylindricalUVs(mesh)
                : GeneratePlanarUvs(mesh);
            Object.DestroyImmediate(mesh);
            unwrapped.RecalculateBounds();
            Debug.Log($"[Phantom] Imported {path}: {unwrapped.vertices.Length} vertices, bounds {unwrapped.bounds}");
            return unwrapped;
        }

        /// <summary>
        /// Planar unwrap onto the mesh's XZ plane (u along local x, v along
        /// local z), matching the flat wing/fin panels. No seam duplication is
        /// needed: u spans 0..1 continuously.
        /// </summary>
        private static Mesh GeneratePlanarUvs(Mesh source)
        {
            var sourceVertices = source.vertices;
            var sourceNormals = source.normals;
            var bounds = source.bounds;
            var sizeX = Mathf.Max(bounds.size.x, 0.001f);
            var sizeZ = Mathf.Max(bounds.size.z, 0.001f);
            var uvs = new List<Vector2>(sourceVertices.Length);
            for (int i = 0; i < sourceVertices.Length; i++)
            {
                uvs.Add(new Vector2((sourceVertices[i].x - bounds.min.x) / sizeX, (sourceVertices[i].z - bounds.min.z) / sizeZ));
            }
            var mesh = new Mesh { name = source.name, indexFormat = source.indexFormat };
            mesh.SetVertices(sourceVertices);
            mesh.SetNormals(sourceNormals);
            mesh.SetUVs(0, uvs);
            mesh.subMeshCount = source.subMeshCount;
            for (int subMesh = 0; subMesh < source.subMeshCount; subMesh++)
            {
                mesh.SetTriangles(source.GetTriangles(subMesh), subMesh);
            }
            mesh.RecalculateBounds();
            return mesh;
        }

        private static void ValidateAssembly(Mesh bodyMesh, Mesh wingsMesh, Mesh finsMesh, Mesh nozzleMesh)
        {
            float nose = TotalLength * 0.5f;
            float aft = -nose;
            if (Mathf.Abs(bodyMesh.bounds.max.z - nose) > 0.001f)
            {
                throw new System.InvalidOperationException($"Phantom nose is at z={bodyMesh.bounds.max.z:F3}; expected {nose:F3}");
            }
            if (Mathf.Abs(bodyMesh.bounds.min.z - aft) > 0.001f)
            {
                throw new System.InvalidOperationException($"Phantom aft is at z={bodyMesh.bounds.min.z:F3}; expected {aft:F3}");
            }
            float measuredLength = bodyMesh.bounds.max.z - bodyMesh.bounds.min.z;
            if (Mathf.Abs(measuredLength - TotalLength) > 0.001f)
            {
                throw new System.InvalidOperationException($"Phantom total length is {measuredLength:F3} m; expected {TotalLength:F3} m");
            }
            float bodyRadius = GetMaximumRadialDistance(bodyMesh);
            if (Mathf.Abs(bodyRadius - BodyRadius) > 0.001f)
            {
                throw new System.InvalidOperationException($"Phantom body radius is {bodyRadius:F3} m; expected {BodyRadius:F3} m");
            }
            var meshes = new Mesh[] { bodyMesh, wingsMesh, finsMesh, nozzleMesh };
            float maximumSpan = 0f;
            for (int i = 0; i < meshes.Length; i++)
            {
                maximumSpan = Mathf.Max(maximumSpan, Mathf.Max(meshes[i].bounds.size.x, meshes[i].bounds.size.y));
            }
            if (Mathf.Abs(maximumSpan - DeployedSpan) > 0.002f)
            {
                throw new System.InvalidOperationException($"Phantom maximum X/Y span is {maximumSpan:F3} m; expected {DeployedSpan:F3} m");
            }
            ValidateCenteredOnAxis(bodyMesh, "body");
            ValidateCenteredOnAxis(nozzleMesh, "nozzle");
            ValidateNozzleRecess(bodyMesh, nozzleMesh, "deployed");
            int triangleCount = 0;
            for (int i = 0; i < meshes.Length; i++)
            {
                if (!meshes[i].HasVertexAttribute(UnityEngine.Rendering.VertexAttribute.TexCoord0))
                {
                    throw new System.InvalidOperationException("Phantom mesh has no UVs: " + meshes[i].name);
                }
                triangleCount += GetTriangleCount(meshes[i]);
            }
            if (triangleCount != ExpectedTriangleCount)
            {
                throw new System.InvalidOperationException(
                    $"Phantom mesh totals are {triangleCount} triangles; expected {ExpectedTriangleCount}");
            }
            Debug.Log($"[Phantom] Assembly verified: length={TotalLength:F3} m, body radius={bodyRadius:F3} m, span={maximumSpan:F3} m, {triangleCount} triangles.");
        }

        private static void ValidateRetractedAssembly(Mesh bodyMesh, Mesh wingsMesh, Mesh finsMesh, Mesh nozzleMesh, Mesh fairingMesh)
        {
            float nose = TotalLength * 0.5f;
            float aft = -nose;
            if (Mathf.Abs(bodyMesh.bounds.max.z - nose) > 0.001f ||
                Mathf.Abs(bodyMesh.bounds.min.z - aft) > 0.001f)
            {
                throw new System.InvalidOperationException($"Phantom retracted body is not centered at the {TotalLength:F3} m length");
            }
            float bodyRadius = GetMaximumRadialDistance(bodyMesh);
            if (Mathf.Abs(bodyRadius - BodyRadius) > 0.001f)
            {
                throw new System.InvalidOperationException($"Phantom retracted body radius is {bodyRadius:F3} m; expected {BodyRadius:F3} m");
            }
            var meshes = new Mesh[] { bodyMesh, wingsMesh, finsMesh, nozzleMesh, fairingMesh };
            float maximumSpan = 0f;
            float maximumRadius = 0f;
            int triangleCount = 0;
            for (int i = 0; i < meshes.Length; i++)
            {
                maximumSpan = Mathf.Max(maximumSpan, Mathf.Max(meshes[i].bounds.size.x, meshes[i].bounds.size.y));
                maximumRadius = Mathf.Max(maximumRadius, GetMaximumRadialDistance(meshes[i]));
                if (!meshes[i].HasVertexAttribute(UnityEngine.Rendering.VertexAttribute.TexCoord0))
                {
                    throw new System.InvalidOperationException("Phantom retracted mesh has no UVs: " + meshes[i].name);
                }
                triangleCount += GetTriangleCount(meshes[i]);
            }
            if (Mathf.Abs(maximumSpan - RetractedSpan) > 0.002f)
            {
                throw new System.InvalidOperationException($"Phantom retracted maximum X/Y span is {maximumSpan:F3} m; expected {RetractedSpan:F3} m");
            }
            if (maximumRadius > 0.125f + 0.001f)
            {
                throw new System.InvalidOperationException($"Phantom retracted maximum radius is {maximumRadius:F3} m; exceeds the 0.125 m carriage envelope");
            }
            if (triangleCount != ExpectedRetractedTriangleCount)
            {
                throw new System.InvalidOperationException(
                    $"Phantom retracted mesh totals are {triangleCount} triangles; expected {ExpectedRetractedTriangleCount}");
            }
            ValidateCenteredOnAxis(bodyMesh, "retracted body");
            ValidateCenteredOnAxis(nozzleMesh, "retracted nozzle");
            ValidateNozzleRecess(bodyMesh, nozzleMesh, "retracted");
            Debug.Log($"[Phantom] Retracted assembly verified: length={TotalLength:F3} m, span={maximumSpan:F3} m, radius={maximumRadius:F3} m, {triangleCount} triangles.");
        }

        private static void ValidateTexturedMaterials(Material bodyMaterial, Material wingMaterial)
        {
            ValidateTexturedMaterial(bodyMaterial, "body");
            ValidateTexturedMaterial(wingMaterial, "wing");
            ValidateMicrosurfaceRange(bodyMaterial, "body");
            ValidateMicrosurfaceRange(wingMaterial, "wing");
            ValidateTextureMirrorSymmetry(bodyMaterial, "Phantom body");
            ValidateTextureMirrorSymmetry(wingMaterial, "Phantom wing");
        }

        private static void ValidateTexturedMaterial(Material material, string label)
        {
            var albedo = material.GetTexture("_BaseMap") as Texture2D;
            var packed = material.GetTexture("_MetallicGlossMap") as Texture2D;
            if (albedo == null || packed == null)
            {
                throw new System.InvalidOperationException("Phantom textured material at " + label + " is missing albedo or packed MS");
            }
            if (Mathf.Abs(material.color.r - 1f) > 0.001f ||
                Mathf.Abs(material.color.g - 1f) > 0.001f ||
                Mathf.Abs(material.color.b - 1f) > 0.001f ||
                Mathf.Abs(material.GetFloat("_Metallic") - 1f) > 0.001f ||
                Mathf.Abs(material.GetFloat("_Smoothness") - 1f) > 0.001f ||
                !material.IsKeywordEnabled("_METALLICSPECGLOSSMAP"))
            {
                throw new System.InvalidOperationException("Phantom textured material at " + label + " is not texture-driven");
            }
            if (!UnityEngine.Experimental.Rendering.GraphicsFormatUtility.IsSRGBFormat(albedo.graphicsFormat))
            {
                throw new System.InvalidOperationException(
                    "Phantom albedo at " + label + " is not sRGB (format=" + albedo.graphicsFormat + "); expected sRGB");
            }
            if (UnityEngine.Experimental.Rendering.GraphicsFormatUtility.IsSRGBFormat(packed.graphicsFormat))
            {
                throw new System.InvalidOperationException(
                    "Phantom packed MS at " + label + " is sRGB (format=" + packed.graphicsFormat + "); expected linear");
            }
        }

        /// <summary>
        /// Painted-composite microsurface: metallic 0.05-0.10 and smoothness
        /// 0.40-0.50 per the PRD, with higher values limited to charcoal
        /// hardware. Reject anything outside the measured vanilla family range.
        /// </summary>
        private static void ValidateMicrosurfaceRange(Material material, string label)
        {
            var packed = material.GetTexture("_MetallicGlossMap") as Texture2D;
            if (packed == null || !packed.isReadable)
            {
                throw new System.InvalidOperationException("Phantom packed MS at " + label + " is not readable");
            }
            var pixels = packed.GetPixels();
            for (int i = 0; i < pixels.Length; i++)
            {
                float metal = pixels[i].r;
                float smooth = pixels[i].a;
                if (metal < 0.03f || metal > 0.12f || smooth < 0.35f || smooth > 0.55f)
                {
                    throw new System.InvalidOperationException(
                        "Phantom packed MS at " + label + " has out-of-range microsurface values: metal=" +
                        metal.ToString("F3") + ", smooth=" + smooth.ToString("F3"));
                }
            }
        }

        /// <summary>
        /// Pixel-based symmetry check on the albedo texture for all three
        /// cylindrical-unwrap transformations (y-mirror u -> 1-u, x-mirror
        /// u -> (1.5-u) mod 1, 180 roll u -> u+0.5 mod 1). Tolerance matches
        /// the bundle validator: 0.12 max-channel difference with a +/-1 pixel
        /// tolerance, at most 0.05% mismatched pixels per transform.
        /// </summary>
        private static void ValidateTextureMirrorSymmetry(Material material, string label)
        {
            const float diffThreshold = 0.12f;
            const float maxMismatchFraction = 0.0005f;
            var albedo = material.GetTexture("_BaseMap") as Texture2D;
            if (albedo == null || !albedo.isReadable)
            {
                throw new System.InvalidOperationException("Phantom albedo at " + label + " is not readable for symmetry validation");
            }
            var pixels = albedo.GetPixels();
            int width = albedo.width;
            int height = albedo.height;
            int mismatchedY = 0;
            int mismatchedX = 0;
            int mismatchedRoll = 0;
            for (int y = 0; y < height; y++)
            {
                for (int x = 0; x < width; x++)
                {
                    float u = x / (float)(width - 1);
                    if (BestMirrorDiff(pixels, width, y, x, (1f - u) * (width - 1)) > diffThreshold)
                    {
                        mismatchedY++;
                    }
                    if (BestMirrorDiff(pixels, width, y, x, Mathf.Repeat(1.5f - u, 1f) * (width - 1)) > diffThreshold)
                    {
                        mismatchedX++;
                    }
                    if (BestMirrorDiff(pixels, width, y, x, Mathf.Repeat(u + 0.5f, 1f) * (width - 1)) > diffThreshold)
                    {
                        mismatchedRoll++;
                    }
                }
            }
            int total = width * height;
            float fractionY = (float)mismatchedY / total;
            float fractionX = (float)mismatchedX / total;
            float fractionRoll = (float)mismatchedRoll / total;
            if (fractionY > maxMismatchFraction || fractionX > maxMismatchFraction || fractionRoll > maxMismatchFraction)
            {
                throw new System.InvalidOperationException(
                    "Phantom texture at " + label + " is not symmetric under the cylindrical transforms: " +
                    "y-mirror " + fractionY.ToString("P3") + ", x-mirror " + fractionX.ToString("P3") +
                    ", 180 roll " + fractionRoll.ToString("P3") +
                    " of pixels differ from their transformed mirror by more than " + diffThreshold +
                    "; expected <= " + maxMismatchFraction.ToString("P3") + " each");
            }
        }

        private static float BestMirrorDiff(Color[] pixels, int width, int y, int x, float mirrorXf)
        {
            int baseX = Mathf.FloorToInt(mirrorXf);
            var color = pixels[y * width + x];
            float best = float.MaxValue;
            for (int d = -1; d <= 1; d++)
            {
                int mx = baseX + d;
                if (mx < 0 || mx >= width)
                {
                    continue;
                }
                var mirror = pixels[y * width + mx];
                float diff = Mathf.Max(
                    Mathf.Abs(color.r - mirror.r),
                    Mathf.Abs(color.g - mirror.g),
                    Mathf.Abs(color.b - mirror.b));
                best = Mathf.Min(best, diff);
            }
            return best;
        }

        /// <summary>
        /// The candidate prefabs must never depend on vanilla reference assets
        /// (extracted atlases or preview-only reference materials/meshes), and
        /// the candidate root must never contain reference/preview assets
        /// outside the preview-only TexturePreviews directory.
        /// </summary>
        private static void ValidateNoReferenceAssets(string prefabPath)
        {
            foreach (var dependency in AssetDatabase.GetDependencies(prefabPath, true))
            {
                var lower = dependency.ToLowerInvariant();
                if (lower.Contains("/reference/") || lower.Contains("/texturepreviews/"))
                {
                    throw new System.InvalidOperationException("Phantom prefab depends on a reference/preview asset: " + dependency);
                }
            }
            var rootPrefix = OutputRoot.ToLowerInvariant() + "/";
            foreach (var assetPath in AssetDatabase.GetAllAssetPaths())
            {
                var lower = assetPath.ToLowerInvariant();
                if (lower.StartsWith(rootPrefix) &&
                    !lower.Contains("/texturepreviews/") &&
                    lower.Contains("reference"))
                {
                    throw new System.InvalidOperationException(
                        "Phantom candidate root contains a reference asset outside TexturePreviews: " + assetPath);
                }
            }
        }

        private static GameObject BuildMissilePrefab(Mesh bodyMesh, Mesh wingsMesh, Mesh finsMesh, Mesh nozzleMesh, Material bodyMaterial, Material wingMaterial, Material finsMaterial, Material nozzleMaterial)
        {
            var root = new GameObject(MissilePrefabName);
            root.AddComponent<MeshFilter>().sharedMesh = bodyMesh;
            root.AddComponent<MeshRenderer>().sharedMaterial = bodyMaterial;

            var bodyCapsule = root.AddComponent<CapsuleCollider>();
            bodyCapsule.center = Vector3.zero;
            bodyCapsule.height = TotalLength;
            bodyCapsule.radius = BodyRadius;
            bodyCapsule.direction = 2;

            AddChildRenderer(root, "Wings", wingsMesh, wingMaterial);
            AddChildRenderer(root, "Fins", finsMesh, finsMaterial);
            AddChildRenderer(root, "Nozzle", nozzleMesh, nozzleMaterial);

            return root;
        }

        private static GameObject BuildRackPrefab(Mesh pylonMesh, Material pylonMaterial, Mesh bodyMesh, Mesh wingsMesh, Mesh finsMesh, Mesh nozzleMesh, Mesh fairingMesh, Material bodyMaterial, Material wingMaterial, Material finsMaterial, Material nozzleMaterial)
        {
            var root = new GameObject(RackPrefabName);
            var pylon = new GameObject("pylon");
            pylon.transform.SetParent(root.transform, false);
            pylon.AddComponent<MeshFilter>().sharedMesh = pylonMesh;
            pylon.AddComponent<MeshRenderer>().sharedMaterial = pylonMaterial;

            var box = pylon.AddComponent<BoxCollider>();
            box.center = new Vector3(0f, -0.08f, 0f);
            box.size = new Vector3(0.18f, 0.16f, 0.6f);

            var missile = new GameObject("rdm9");
            missile.transform.SetParent(pylon.transform, false);
            missile.transform.localPosition = new Vector3(0f, GetRackMissileOffsetY(bodyMesh), 0f);
            missile.AddComponent<MeshFilter>().sharedMesh = bodyMesh;
            missile.AddComponent<MeshRenderer>().sharedMaterial = bodyMaterial;
            var missileCapsule = missile.AddComponent<CapsuleCollider>();
            missileCapsule.center = Vector3.zero;
            missileCapsule.height = TotalLength;
            missileCapsule.radius = BodyRadius;
            missileCapsule.direction = 2;

            AddChildRenderer(missile, "Wings", wingsMesh, wingMaterial);
            AddChildRenderer(missile, "Fins", finsMesh, finsMaterial);
            AddChildRenderer(missile, "Nozzle", nozzleMesh, nozzleMaterial);
            AddChildRenderer(missile, "Fairing", fairingMesh, bodyMaterial);

            return root;
        }

        /// <summary>
        /// The retracted missile rides directly under the pylon (no roll: the
        /// whole state fits the 250 mm carriage envelope). Solve the mount
        /// offset that restores the authored pylon-to-body clearance.
        /// </summary>
        private static float GetRackMissileOffsetY(Mesh bodyMesh)
        {
            const float pylonHalfWidth = 0.09f;
            const float pylonHalfLength = 0.3f;
            const float pylonBottom = -0.16f;
            float highestMissilePoint = float.NegativeInfinity;
            foreach (var vertex in bodyMesh.vertices)
            {
                if (Mathf.Abs(vertex.x) <= pylonHalfWidth + 0.0001f &&
                    Mathf.Abs(vertex.z) <= pylonHalfLength + 0.0001f)
                {
                    highestMissilePoint = Mathf.Max(highestMissilePoint, vertex.y);
                }
            }
            if (float.IsNegativeInfinity(highestMissilePoint))
            {
                throw new System.InvalidOperationException("No Phantom retracted vertices fall inside the pylon footprint");
            }
            float offset = pylonBottom - PylonTargetClearance - highestMissilePoint;
            float clearance = pylonBottom - (offset + highestMissilePoint);
            if (clearance < 0.008f || clearance > 0.010f)
            {
                throw new System.InvalidOperationException(
                    $"Phantom pylon clearance is {clearance:F4} m; expected {PylonTargetClearance:F4} m");
            }
            Debug.Log($"[Phantom] Rack alignment verified: {clearance:F4} m pylon clearance, missile offset y={offset:F5} m.");
            return offset;
        }

        private static void AddChildRenderer(GameObject parent, string name, Mesh mesh, Material material)
        {
            var child = new GameObject(name);
            child.transform.SetParent(parent.transform, false);
            child.AddComponent<MeshFilter>().sharedMesh = mesh;
            child.AddComponent<MeshRenderer>().sharedMaterial = material;
        }

        private static Material CreateFlatMaterial(Shader shader, string name, Color color, float metallic, float smoothness)
        {
            var material = new Material(shader) { name = name };
            material.color = color;
            material.SetFloat("_Metallic", metallic);
            material.SetFloat("_Smoothness", smoothness);
            var measured = material.color;
            if (Mathf.Abs(measured.r - color.r) > 0.001f ||
                Mathf.Abs(measured.g - color.g) > 0.001f ||
                Mathf.Abs(measured.b - color.b) > 0.001f ||
                Mathf.Abs(material.GetFloat("_Metallic") - metallic) > 0.001f ||
                Mathf.Abs(material.GetFloat("_Smoothness") - smoothness) > 0.001f)
            {
                throw new System.InvalidOperationException($"Phantom material {name} was not configured");
            }
            return material;
        }

        private class SurfaceData
        {
            public readonly List<Vector3> vertices = new List<Vector3>();
            public readonly List<Vector3> normals = new List<Vector3>();
            public readonly List<Vector2> uvs = new List<Vector2>();
            public readonly List<int> triangles = new List<int>();

            public Mesh ToMesh(string name)
            {
                var mesh = new Mesh { name = name };
                mesh.SetVertices(vertices);
                mesh.SetTriangles(triangles, 0);
                if (normals.Count == vertices.Count)
                {
                    mesh.SetNormals(normals);
                }
                if (uvs.Count == vertices.Count)
                {
                    mesh.SetUVs(0, uvs);
                }
                mesh.RecalculateBounds();
                return mesh;
            }
        }

        private static Mesh BuildPylonMesh()
        {
            var surface = new SurfaceData();
            float width = 0.18f;
            float height = 0.16f;
            float depth = 0.6f;
            Vector3 c = new Vector3(0f, -height * 0.5f, 0f);
            Vector3 hx = new Vector3(width * 0.5f, 0f, 0f);
            Vector3 hy = new Vector3(0f, height * 0.5f, 0f);
            Vector3 hz = new Vector3(0f, 0f, depth * 0.5f);
            AddDoubleSidedQuad(surface, c + hx + hy + hz, c + hx + hy - hz, c + hx - hy - hz, c + hx - hy + hz, new Vector3(1f, 0f, 0f));
            AddDoubleSidedQuad(surface, c - hx + hy - hz, c - hx + hy + hz, c - hx - hy + hz, c - hx - hy - hz, new Vector3(-1f, 0f, 0f));
            AddDoubleSidedQuad(surface, c - hx + hy + hz, c + hx + hy + hz, c + hx - hy + hz, c - hx - hy + hz, new Vector3(0f, 0f, 1f));
            AddDoubleSidedQuad(surface, c + hx + hy - hz, c - hx + hy - hz, c - hx - hy - hz, c + hx - hy - hz, new Vector3(0f, 0f, -1f));
            AddDoubleSidedQuad(surface, c - hx + hy + hz, c - hx + hy - hz, c + hx + hy - hz, c + hx + hy + hz, new Vector3(0f, 1f, 0f));
            AddDoubleSidedQuad(surface, c + hx - hy + hz, c + hx - hy - hz, c - hx - hy - hz, c - hx - hy + hz, new Vector3(0f, -1f, 0f));
            return surface.ToMesh("MeshPhantomPylon");
        }

        private static void AddDoubleSidedQuad(SurfaceData surface, Vector3 a, Vector3 b, Vector3 c, Vector3 d, Vector3 normal)
        {
            AddSingleQuad(surface, a, b, c, d, normal);
            AddSingleQuad(surface, d, c, b, a, normal);
        }

        private static void AddSingleQuad(SurfaceData surface, Vector3 a, Vector3 b, Vector3 c, Vector3 d, Vector3 normal)
        {
            int s = surface.vertices.Count;
            surface.vertices.Add(a);
            surface.vertices.Add(b);
            surface.vertices.Add(c);
            surface.vertices.Add(d);
            surface.normals.Add(normal);
            surface.normals.Add(normal);
            surface.normals.Add(normal);
            surface.normals.Add(normal);
            surface.uvs.Add(new Vector2(0f, 1f));
            surface.uvs.Add(new Vector2(1f, 1f));
            surface.uvs.Add(new Vector2(1f, 0f));
            surface.uvs.Add(new Vector2(0f, 0f));
            surface.triangles.Add(s);
            surface.triangles.Add(s + 1);
            surface.triangles.Add(s + 2);
            surface.triangles.Add(s);
            surface.triangles.Add(s + 2);
            surface.triangles.Add(s + 3);
        }

        private static int GetTriangleCount(Mesh mesh)
        {
            int count = 0;
            for (int subMesh = 0; subMesh < mesh.subMeshCount; subMesh++)
            {
                count += mesh.GetTriangles(subMesh).Length / 3;
            }
            return count;
        }

        private static float GetMaximumRadialDistance(Mesh mesh)
        {
            float maximum = 0f;
            var vertices = mesh.vertices;
            for (int i = 0; i < vertices.Length; i++)
            {
                float radial = Mathf.Sqrt(vertices[i].x * vertices[i].x + vertices[i].y * vertices[i].y);
                maximum = Mathf.Max(maximum, radial);
            }
            return maximum;
        }

        private static void ValidateCenteredOnAxis(Mesh mesh, string partName)
        {
            if (Mathf.Abs(mesh.bounds.min.x + mesh.bounds.max.x) > 0.001f ||
                Mathf.Abs(mesh.bounds.min.y + mesh.bounds.max.y) > 0.001f)
            {
                throw new System.InvalidOperationException($"Phantom {partName} is not centered on the z-axis");
            }
        }

        /// <summary>
        /// Regression gate for the issue-005 aft-face z-fighting defect: the
        /// derived nozzle lip must sit recessed inside the body aft face
        /// (never coplanar with it, never proud of it).
        /// </summary>
        private static void ValidateNozzleRecess(Mesh bodyMesh, Mesh nozzleMesh, string state)
        {
            float bodyAft = bodyMesh.bounds.min.z;
            float nozzleAft = nozzleMesh.bounds.min.z;
            if (nozzleAft < bodyAft - 0.0005f)
            {
                throw new System.InvalidOperationException(
                    $"Phantom {state} nozzle lip stands proud of the body aft face: {nozzleAft:F4} m");
            }
            if (nozzleAft - bodyAft < NozzleRecessMeters - 0.0005f)
            {
                throw new System.InvalidOperationException(
                    $"Phantom {state} nozzle lip is not recessed from the body aft face: " +
                    $"lip aft {nozzleAft:F4} m vs body aft {bodyAft:F4} m");
            }
        }

        private static void SaveAsset(Object asset, string fileName)
        {
            string path = OutputRoot + "/" + fileName;
            AssetDatabase.DeleteAsset(path);
            AssetDatabase.CreateAsset(asset, path);
        }

        private static void SaveAsPrefab(GameObject gameObject, string fileName)
        {
            string path = OutputRoot + "/" + fileName;
            AssetDatabase.DeleteAsset(path);
            PrefabUtility.SaveAsPrefabAsset(gameObject, path);
        }

        private static void EnsureFolder(string parent, string folder)
        {
            if (!AssetDatabase.IsValidFolder(parent + "/" + folder))
            {
                AssetDatabase.CreateFolder(parent, folder);
            }
        }
    }
}