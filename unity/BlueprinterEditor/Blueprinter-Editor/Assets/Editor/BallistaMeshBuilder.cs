using System.Collections.Generic;
using Erenaldi.Munitions;
using UnityEditor;
using UnityEngine;

namespace Erenaldi.Ballista
{
    public static class BallistaMeshBuilder
    {
        internal const float TotalLength = 2.594424f;
        internal const float BodyHalfWidth = 0.12f;
        internal const float RailTopUnity = 0.130946f;
        internal const float WingPivotZ = 0.395f;
        internal const float WingPivotXRight = 0.0636526f;
        internal const float WingPivotY = -0.1191965f;
        internal const float DeployedSpan = 1.576114f;
        internal const float StowedSpan = 0.322805f;
        internal const float RackMissileOffsetY = -0.232946f;
        private const int ExpectedTriangleCount = 35786;

        internal const string OutputRoot = "Assets/Blueprinter/Mods/BallistaMod";
        private const string ModelsRoot = OutputRoot + "/Models";
        internal const string MissilePrefabName = "Erenaldi.AGM110";
        internal const string RackPrefabName = "Erenaldi.AGM110_single";

        [MenuItem("Blueprinter/Ballista/Build Geometry")]
        public static void Build()
        {
            EnsureFolder("Assets/Blueprinter/Mods", "BallistaMod");
            EnsureFolder(OutputRoot, "Models");

            var shader = Shader.Find("Universal Render Pipeline/Lit");
            var clearcoatShader = Shader.Find("Universal Render Pipeline/Complex Lit");
            if (shader == null || clearcoatShader == null)
            {
                throw new System.InvalidOperationException("Required URP shaders are unavailable");
            }

            var hardware = new MaterialClass("MatBallistaHardware", shader,
                new Color(0.029557f, 0.043735f, 0.05448f), 0.35f, 0.45f);
            var edge = new MaterialClass("MatBallistaEdge", shader,
                new Color(0.266356f, 0.304987f, 0.318547f), 0.6f, 0.62f);
            var glass = new MaterialClass("MatBallistaGlass", clearcoatShader,
                new Color(0.024158f, 0.064803f, 0.097587f), 0.08f, 0.9f, true);
            var nozzle = new MaterialClass("MatBallistaNozzle", shader,
                new Color(0.132868f, 0.090842f, 0.072272f), 0.55f, 0.54f);
            var recess = new MaterialClass("MatBallistaRecess", shader,
                new Color(0.009721f, 0.016807f, 0.022174f), 0f, 0.1f);
            var accent = new MaterialClass("MatBallistaAccent", shader,
                new Color(0.508881f, 0.246201f, 0.040915f), 0.12f, 0.38f);
            var pylonMaterial = new Material(shader) { name = "MatBallistaPylon" };
            pylonMaterial.color = new Color(0.45f, 0.47f, 0.5f);

            var materials = new Dictionary<string, Material>
            {
                { "body", BallistaTexturedMaterialBuilder.CreateBodyMaterial(OutputRoot, "MatBallistaBody") },
                { "panel", BallistaTexturedMaterialBuilder.CreatePanelMaterial(OutputRoot, "MatBallistaPanel") },
                { "wing", BallistaTexturedMaterialBuilder.CreateWingMaterial(OutputRoot, "MatBallistaWing") },
                { "hardware", hardware.Create() },
                { "edge", edge.Create() },
                { "glass", glass.Create() },
                { "nozzle", nozzle.Create() },
                { "recess", recess.Create() },
                { "accent", accent.Create() },
            };

            var meshes = new Dictionary<string, Mesh>();
            int totalTriangles = 0;
            foreach (var pair in GroupFiles)
            {
                // One stowed OBJ set serves both prefabs: the flying missile
                // deploys its wings via child rotation, the rack display keeps
                // them folded at identity.
                var mesh = LoadCadMesh($"{ModelsRoot}/BallistaRack_{pair}.obj", $"MeshBallista_{pair}");
                meshes[pair] = mesh;
                totalTriangles += GetTriangleCount(mesh);
            }
            if (totalTriangles != ExpectedTriangleCount)
            {
                throw new System.InvalidOperationException(
                    $"Ballista mesh totals are {totalTriangles} triangles; expected {ExpectedTriangleCount}");
            }
            ValidateAssembly(meshes);

            var pylonMesh = BuildPylonMesh();
            foreach (var material in materials.Values)
            {
                // Textured body/panel/wing materials are saved by
                // BallistaTexturedMaterialBuilder; re-saving would destroy them.
                if (material.name != "MatBallistaBody" &&
                    material.name != "MatBallistaPanel" &&
                    material.name != "MatBallistaWing")
                {
                    SaveAsset(material, material.name + ".mat");
                }
            }
            SaveAsset(pylonMesh, "MeshBallistaPylon.asset");
            foreach (var pair in meshes.Keys)
            {
                SaveAsset(meshes[pair], $"MeshBallista_{pair}.asset");
            }

            var missile = BuildMissilePrefab(meshes, materials);
            SaveAsPrefab(missile, MissilePrefabName + ".prefab");
            Object.DestroyImmediate(missile);

            var rack = BuildRackPrefab(pylonMesh, pylonMaterial, meshes, materials);
            SaveAsPrefab(rack, RackPrefabName + ".prefab");
            Object.DestroyImmediate(rack);

            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();
            Debug.Log("[Ballista] CAD geometry built: " + OutputRoot);
        }

        [MenuItem("Blueprinter/Ballista/Build Geometry Bundle")]
        public static void BuildBundle()
        {
            MunitionsGeometryBundleBuilder.BuildBundle();
        }

        private static readonly string[] GroupFiles =
        {
            "body_body",
            "fixed_hardware_accent", "fixed_hardware_edge", "fixed_hardware_hardware", "fixed_hardware_panel",
            "intakes_hardware", "intakes_panel",
            "mounting_edge", "mounting_hardware", "mounting_panel",
            "propulsion_edge", "propulsion_hardware", "propulsion_nozzle", "propulsion_recess",
            "seeker_bezel_hardware", "seeker_bezel_recess",
            "seeker_glass_glass",
            "tail_1_wing", "tail_2_wing", "tail_3_wing", "tail_4_wing",
            "wing_left_hardware", "wing_left_wing",
            "wing_right_hardware", "wing_right_wing",
        };

        private static void ValidateAssembly(Dictionary<string, Mesh> meshes)
        {
            var body = meshes["body_body"];
            float nose = TotalLength * 0.5f;
            float aft = -nose;
            if (Mathf.Abs(body.bounds.max.z - nose) > 0.001f)
            {
                throw new System.InvalidOperationException($"Ballista nose is at z={body.bounds.max.z:F3}; expected {nose:F3}");
            }
            if (Mathf.Abs(body.bounds.min.z - aft) > 0.001f)
            {
                throw new System.InvalidOperationException($"Ballista aft is at z={body.bounds.min.z:F3}; expected {aft:F3}");
            }
            var wingLeft = meshes["wing_left_wing"];
            var wingRight = meshes["wing_right_wing"];
            ValidatePivotLocal(wingLeft, "wing left", -WingPivotXRight);
            ValidatePivotLocal(wingRight, "wing right", WingPivotXRight);
            foreach (var pair in meshes.Keys)
            {
                var mesh = meshes[pair];
                float span = Mathf.Max(mesh.bounds.size.x, mesh.bounds.size.y);
                if (pair.StartsWith("tail") && span > StowedSpan)
                {
                    throw new System.InvalidOperationException($"Ballista {pair} span {span:F3} exceeds stowed envelope");
                }
            }
        }

        private static void ValidatePivotLocal(Mesh mesh, string label, float pivotX)
        {
            // Wing meshes are the stowed panels in pivot-local Unity space:
            // axial (CAD +X) is Unity Z, lateral chord is Unity X.
            if (Mathf.Abs(mesh.bounds.min.z - (-0.975f)) > 0.003f ||
                Mathf.Abs(mesh.bounds.max.z - 0.03f) > 0.003f)
            {
                throw new System.InvalidOperationException(
                    $"Ballista {label} pivot-local axial bounds {mesh.bounds.min.z:F3}..{mesh.bounds.max.z:F3} are unexpected");
            }
            if (Mathf.Abs(mesh.bounds.center.x - pivotX) < 0.0001f)
            {
                throw new System.InvalidOperationException($"Ballista {label} mesh was not exported pivot-local");
            }
        }

        private static Mesh LoadCadMesh(string path, string meshName)
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
            // Body/panel/hardware groups get the seam-deduplicated full-2pi
            // cylindrical unwrap (z-axis, v 0 tail .. 1 nose) so the textured
            // materials can paint panel lines over the whole airframe. The flat
            // wing/fin panels get a planar unwrap instead: cylindrical mapping
            // degenerates on a flat panel (u = atan2(y,x) is nearly constant
            // per face and mirrors across the chord centerline).
            var unwrapped = meshName.EndsWith("_wing")
                ? GeneratePlanarUvs(mesh)
                : Erenaldi.Kris.KrisMeshBuilder.GenerateCylindricalUVs(mesh);
            Object.DestroyImmediate(mesh);
            unwrapped.RecalculateBounds();
            Debug.Log($"[Ballista] Imported {path}: {unwrapped.vertices.Length} vertices, bounds {unwrapped.bounds}");
            return unwrapped;
        }

        /// <summary>
        /// Planar unwrap onto the mesh's XZ plane (u along local x, v along
        /// local z), matching the flat stowed wing/fin panels. No seam
        /// duplication is needed: u spans 0..1 continuously.
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

        private static int GetTriangleCount(Mesh mesh)
        {
            int count = 0;
            for (int subMesh = 0; subMesh < mesh.subMeshCount; subMesh++)
            {
                count += mesh.GetTriangles(subMesh).Length / 3;
            }
            return count;
        }

        private class MaterialClass
        {
            private readonly string name;
            private readonly Shader shader;
            private readonly Color color;
            private readonly float metallic;
            private readonly float smoothness;
            private readonly bool clearcoat;

            public MaterialClass(string name, Shader shader, Color color, float metallic, float smoothness, bool clearcoat = false)
            {
                this.name = name;
                this.shader = shader;
                this.color = color;
                this.metallic = metallic;
                this.smoothness = smoothness;
                this.clearcoat = clearcoat;
            }

            public Material Create()
            {
                var material = new Material(shader) { name = name };
                material.color = color;
                material.SetFloat("_Metallic", metallic);
                material.SetFloat("_Smoothness", smoothness);
                if (clearcoat)
                {
                    material.SetFloat("_ClearCoat", 1f);
                    material.SetFloat("_ClearCoatMask", 1f);
                    material.SetFloat("_ClearCoatSmoothness", 0.975f);
                    material.EnableKeyword("_CLEARCOAT");
                }
                var measured = material.color;
                if (Mathf.Abs(measured.r - color.r) > 0.001f ||
                    Mathf.Abs(measured.g - color.g) > 0.001f ||
                    Mathf.Abs(measured.b - color.b) > 0.001f ||
                    Mathf.Abs(material.GetFloat("_Metallic") - metallic) > 0.001f ||
                    Mathf.Abs(material.GetFloat("_Smoothness") - smoothness) > 0.001f)
                {
                    throw new System.InvalidOperationException($"Ballista material {name} was not configured");
                }
                return material;
            }
        }

        private static Mesh BuildPylonMesh()
        {
            var mesh = new Mesh { name = "MeshBallistaPylon" };
            float width = 0.12f;
            float height = 0.1f;
            float depth = 0.4f;
            var c = new Vector3(0f, -height * 0.5f, 0f);
            var hx = new Vector3(width * 0.5f, 0f, 0f);
            var hy = new Vector3(0f, height * 0.5f, 0f);
            var hz = new Vector3(0f, 0f, depth * 0.5f);
            var quads = new[]
            {
                (c + hx + hy + hz, c + hx + hy - hz, c + hx - hy - hz, c + hx - hy + hz, new Vector3(1f, 0f, 0f)),
                (c - hx + hy - hz, c - hx + hy + hz, c - hx - hy + hz, c - hx - hy - hz, new Vector3(-1f, 0f, 0f)),
                (c - hx + hy + hz, c + hx + hy + hz, c + hx - hy + hz, c - hx - hy + hz, new Vector3(0f, 0f, 1f)),
                (c + hx + hy - hz, c - hx + hy - hz, c - hx - hy - hz, c + hx - hy - hz, new Vector3(0f, 0f, -1f)),
                (c - hx + hy + hz, c - hx + hy - hz, c + hx + hy - hz, c + hx + hy + hz, new Vector3(0f, 1f, 0f)),
                (c + hx - hy + hz, c + hx - hy - hz, c - hx - hy - hz, c - hx - hy + hz, new Vector3(0f, -1f, 0f)),
            };
            var vertices = new List<Vector3>();
            var normals = new List<Vector3>();
            var triangles = new List<int>();
            foreach (var quad in quads)
            {
                int s = vertices.Count;
                vertices.AddRange(new[] { quad.Item1, quad.Item2, quad.Item3, quad.Item4 });
                normals.AddRange(new[] { quad.Item5, quad.Item5, quad.Item5, quad.Item5 });
                triangles.AddRange(new[] { s, s + 1, s + 2, s, s + 2, s + 3 });
                triangles.AddRange(new[] { s + 3, s + 2, s + 1, s, s + 1, s + 2 });
            }
            mesh.SetVertices(vertices);
            mesh.SetNormals(normals);
            mesh.SetTriangles(triangles, 0);
            mesh.RecalculateBounds();
            return mesh;
        }

        private static readonly string[] ChildNames =
        {
            "SeekerGlass", "SeekerBezel", "SeekerSeal",
            "WingLeft", "WingLeftPivotCap", "WingRight", "WingRightPivotCap",
            "TailControl1", "TailControl2", "TailControl3", "TailControl4",
            "Propulsion_Nozzle", "Propulsion_Edge", "Propulsion_Hardware", "Propulsion_Recess",
            "Intakes_Hardware", "Intakes_Panel",
            "Mounting_Edge", "Mounting_Hardware", "Mounting_Panel",
            "FixedHardware_Accent", "FixedHardware_Edge", "FixedHardware_Hardware", "FixedHardware_Panel",
        };

        private static void AddAllChildren(GameObject parent, Dictionary<string, Mesh> meshes, Dictionary<string, Material> materials, bool deployed)
        {
            foreach (var childName in ChildNames)
            {
                AddChild(parent, childName, meshes, materials, deployed);
            }
        }

        private static GameObject BuildMissilePrefab(Dictionary<string, Mesh> meshes, Dictionary<string, Material> materials)
        {
            var root = new GameObject(MissilePrefabName);
            root.AddComponent<MeshFilter>().sharedMesh = meshes["body_body"];
            root.AddComponent<MeshRenderer>().sharedMaterial = materials["body"];

            var capsule = root.AddComponent<CapsuleCollider>();
            capsule.center = Vector3.zero;
            capsule.height = TotalLength;
            capsule.radius = BodyHalfWidth;
            capsule.direction = 2;

            AddAllChildren(root, meshes, materials, deployed: true);

            return root;
        }

        private static readonly Dictionary<string, string> ChildMeshKeys = new Dictionary<string, string>
        {
            { "SeekerGlass", "seeker_glass_glass" },
            { "SeekerBezel", "seeker_bezel_hardware" },
            { "SeekerSeal", "seeker_bezel_recess" },
            { "WingLeft", "wing_left_wing" },
            { "WingLeftPivotCap", "wing_left_hardware" },
            { "WingRight", "wing_right_wing" },
            { "WingRightPivotCap", "wing_right_hardware" },
            { "TailControl1", "tail_1_wing" },
            { "TailControl2", "tail_2_wing" },
            { "TailControl3", "tail_3_wing" },
            { "TailControl4", "tail_4_wing" },
            { "Propulsion_Nozzle", "propulsion_nozzle" },
            { "Propulsion_Edge", "propulsion_edge" },
            { "Propulsion_Hardware", "propulsion_hardware" },
            { "Propulsion_Recess", "propulsion_recess" },
            { "Intakes_Hardware", "intakes_hardware" },
            { "Intakes_Panel", "intakes_panel" },
            { "Mounting_Edge", "mounting_edge" },
            { "Mounting_Hardware", "mounting_hardware" },
            { "Mounting_Panel", "mounting_panel" },
            { "FixedHardware_Accent", "fixed_hardware_accent" },
            { "FixedHardware_Edge", "fixed_hardware_edge" },
            { "FixedHardware_Hardware", "fixed_hardware_hardware" },
            { "FixedHardware_Panel", "fixed_hardware_panel" },
        };

        private static void AddChild(GameObject parent, string childName, Dictionary<string, Mesh> meshes, Dictionary<string, Material> materials, bool deployed)
        {
            string meshKey = ChildMeshKeys[childName];
            string materialKey = meshKey.Substring(meshKey.LastIndexOf('_') + 1);
            var child = new GameObject(childName);
            child.transform.SetParent(parent.transform, false);
            if (childName.StartsWith("WingLeft") || childName.StartsWith("WingRight"))
            {
                float side = childName.StartsWith("WingLeft") ? -1f : 1f;
                child.transform.localPosition = new Vector3(side * WingPivotXRight, WingPivotY, WingPivotZ);
                // CAD sweep about +Z maps to Unity rotation about +Y with the
                // same sign; the deployed missile sweeps its wings out-and-aft
                // at 45 degrees from the body axis.
                child.transform.localRotation = Quaternion.Euler(0f, -side * (deployed ? 45f : 0f), 0f);
            }
            child.AddComponent<MeshFilter>().sharedMesh = meshes[meshKey];
            child.AddComponent<MeshRenderer>().sharedMaterial = materials[materialKey];
        }

        private static GameObject BuildRackPrefab(Mesh pylonMesh, Material pylonMaterial, Dictionary<string, Mesh> meshes, Dictionary<string, Material> materials)
        {
            var root = new GameObject(RackPrefabName);
            var pylon = new GameObject("pylon");
            pylon.transform.SetParent(root.transform, false);
            pylon.AddComponent<MeshFilter>().sharedMesh = pylonMesh;
            pylon.AddComponent<MeshRenderer>().sharedMaterial = pylonMaterial;

            var box = pylon.AddComponent<BoxCollider>();
            box.center = new Vector3(0f, -0.05f, 0f);
            box.size = new Vector3(0.12f, 0.1f, 0.4f);

            var mountedMissile = new GameObject("agm1");
            mountedMissile.transform.SetParent(pylon.transform, false);
            mountedMissile.transform.localPosition = new Vector3(0f, RackMissileOffsetY, 0f);
            mountedMissile.AddComponent<MeshFilter>().sharedMesh = meshes["body_body"];
            mountedMissile.AddComponent<MeshRenderer>().sharedMaterial = materials["body"];
            var capsule = mountedMissile.AddComponent<CapsuleCollider>();
            capsule.center = Vector3.zero;
            capsule.height = TotalLength;
            capsule.radius = BodyHalfWidth;
            capsule.direction = 2;

            AddAllChildren(mountedMissile, meshes, materials, deployed: false);

            ValidateRackSeat();

            return root;
        }

        private static void ValidateRackSeat()
        {
            float railTopUnderPylon = RackMissileOffsetY + RailTopUnity;
            float pylonBottom = -0.1f;
            float seat = pylonBottom - railTopUnderPylon;
            if (seat < 0.001f || seat > 0.003f)
            {
                throw new System.InvalidOperationException(
                    $"Ballista rack seat is {seat:F4} m; expected 0.002 m between rail top and pylon underside");
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
