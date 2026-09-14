using BepInEx.Logging;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using UnityEngine;
using UnityEngine.Rendering;

namespace Erenaldi.MunitionsPackage
{
    internal sealed class MissileGeometryDumper
    {
        private const int DumpSchemaVersion = 1;

        private static readonly string[] TargetMountKeys =
        {
            "AGM1_single",
            "AAM2_single",
            "AAM4_single",
            "AGM_heavy_single",
            "P_KEM1_single",
            "AShM2_single",
            "Erenaldi.AAM44_single"
        };

        private readonly ManualLogSource log;

        public MissileGeometryDumper(ManualLogSource log)
        {
            this.log = log;
        }

        public void Dump(string outputDirectory)
        {
            var targets = new JArray();
            foreach (var mountKey in TargetMountKeys)
            {
                try
                {
                    targets.Add(DumpTarget(outputDirectory, mountKey));
                }
                catch (Exception exception)
                {
                    log.LogWarning($"[Phase 3] Geometry dump failed for target '{mountKey}': {exception.GetType().Name}: {exception.Message}");
                    targets.Add(new JObject
                    {
                        ["mountKey"] = mountKey,
                        ["error"] = $"{exception.GetType().Name}: {exception.Message}"
                    });
                }
            }

            var document = new JObject
            {
                ["schemaVersion"] = DumpSchemaVersion,
                ["generatedUtc"] = DateTime.UtcNow.ToString("O", CultureInfo.InvariantCulture),
                ["targets"] = targets
            };

            var jsonPath = Path.Combine(outputDirectory, "missile-geometry.json");
            WriteJson(jsonPath, document);
            log.LogInfo($"[Phase 3] Missile geometry written to {jsonPath}");
        }

        private JObject DumpTarget(string outputDirectory, string mountKey)
        {
            if (Encyclopedia.WeaponLookup == null ||
                !Encyclopedia.WeaponLookup.TryGetValue(mountKey, out var mount) || mount == null)
            {
                log.LogWarning($"[Phase 3] Geometry target '{mountKey}' was not found in Encyclopedia.WeaponLookup.");
                return new JObject
                {
                    ["mountKey"] = mountKey,
                    ["error"] = "Mount not found in Encyclopedia.WeaponLookup."
                };
            }

            var prefab = mount.info?.weaponPrefab;
            if (prefab == null)
            {
                log.LogWarning($"[Phase 3] Geometry target '{mountKey}' has no projectile prefab.");
                return new JObject
                {
                    ["mountKey"] = mountKey,
                    ["prefabName"] = null,
                    ["error"] = "Mount has no weapon info or weapon prefab."
                };
            }

            var meshes = new JArray();
            var objFileName = ObjFileName(mountKey);
            var objPath = Path.Combine(outputDirectory, objFileName);
            var mergedMin = new Vector3(float.PositiveInfinity, float.PositiveInfinity, float.PositiveInfinity);
            var mergedMax = new Vector3(float.NegativeInfinity, float.NegativeInfinity, float.NegativeInfinity);
            var vertexOffset = 0;
            var exportedVertexCount = 0;
            var exportedTriangleCount = 0;

            using (var writer = new StreamWriter(objPath, false, new UTF8Encoding(false)))
            {
                foreach (var renderer in SelectRenderers(prefab))
                {
                    var hierarchyPath = GetHierarchyPath(prefab.transform, renderer.transform);
                    var filter = renderer.GetComponent<MeshFilter>();
                    var mesh = filter != null ? filter.sharedMesh : null;
                    if (mesh == null)
                    {
                        log.LogWarning($"[Phase 3] Renderer '{hierarchyPath}' on '{mountKey}' has no MeshFilter or shared mesh.");
                        meshes.Add(new JObject
                        {
                            ["hierarchyPath"] = hierarchyPath,
                            ["meshName"] = null,
                            ["readable"] = false,
                            ["exported"] = false,
                            ["error"] = "Renderer has no MeshFilter or shared mesh."
                        });
                        continue;
                    }

                    try
                    {
                        var matrix = prefab.transform.worldToLocalMatrix * renderer.transform.localToWorldMatrix;
                        if (!TryReadMeshGeometry(mesh, out var vertices, out var submeshTriangles, out var triangleCount, out var readMethod, out var readError))
                        {
                            log.LogWarning($"[Phase 3] Failed to read mesh '{mesh.name}' on '{mountKey}': {readError}");
                            meshes.Add(new JObject
                            {
                                ["hierarchyPath"] = hierarchyPath,
                                ["meshName"] = mesh.name,
                                ["readable"] = mesh.isReadable,
                                ["exported"] = false,
                                ["error"] = readError
                            });
                            continue;
                        }

                        var transformedVertices = new List<Vector3>(vertices.Length);
                        var min = new Vector3(float.PositiveInfinity, float.PositiveInfinity, float.PositiveInfinity);
                        var max = new Vector3(float.NegativeInfinity, float.NegativeInfinity, float.NegativeInfinity);
                        foreach (var vertex in vertices)
                        {
                            var transformed = matrix.MultiplyPoint3x4(vertex);
                            if (!IsFinite(transformed))
                            {
                                throw new InvalidOperationException("Mesh contains non-finite vertex positions.");
                            }
                            min = Vector3.Min(min, transformed);
                            max = Vector3.Max(max, transformed);
                            transformedVertices.Add(transformed);
                        }

                        foreach (var transformed in transformedVertices)
                        {
                            writer.WriteLine(FormatVector(transformed));
                        }
                        foreach (var triangles in submeshTriangles)
                        {
                            for (var index = 0; index + 2 < triangles.Length; index += 3)
                            {
                                writer.WriteLine(string.Format(CultureInfo.InvariantCulture, "f {0} {1} {2}",
                                    triangles[index] + 1 + vertexOffset,
                                    triangles[index + 1] + 1 + vertexOffset,
                                    triangles[index + 2] + 1 + vertexOffset));
                            }
                        }

                        vertexOffset += vertices.Length;
                        exportedVertexCount += vertices.Length;
                        exportedTriangleCount += triangleCount;
                        mergedMin = Vector3.Min(mergedMin, min);
                        mergedMax = Vector3.Max(mergedMax, max);
                        meshes.Add(new JObject
                        {
                            ["hierarchyPath"] = hierarchyPath,
                            ["meshName"] = mesh.name,
                            ["readable"] = mesh.isReadable,
                            ["exported"] = true,
                            ["readMethod"] = readMethod,
                            ["vertexCount"] = vertices.Length,
                            ["triangleCount"] = triangleCount,
                            ["min"] = VectorToArray(min),
                            ["max"] = VectorToArray(max),
                            ["size"] = VectorToArray(max - min)
                        });
                    }
                    catch (Exception exception)
                    {
                        log.LogWarning($"[Phase 3] Failed to read mesh '{mesh.name}' on '{mountKey}': {exception.GetType().Name}: {exception.Message}");
                        meshes.Add(new JObject
                        {
                            ["hierarchyPath"] = hierarchyPath,
                            ["meshName"] = mesh.name,
                            ["readable"] = mesh.isReadable,
                            ["exported"] = false,
                            ["error"] = $"{exception.GetType().Name}: {exception.Message}"
                        });
                    }
                }
            }

            if (exportedVertexCount == 0)
            {
                try
                {
                    File.Delete(objPath);
                }
                catch (Exception exception)
                {
                    log.LogWarning($"[Phase 3] Could not remove empty geometry file '{objPath}': {exception.GetType().Name}: {exception.Message}");
                }
                objFileName = null;
            }
            else
            {
                log.LogInfo($"[Phase 3] Missile geometry written to {objPath} ({exportedVertexCount} vertices, {exportedTriangleCount} triangles).");
            }

            var mergedSize = mergedMax - mergedMin;
            return new JObject
            {
                ["mountKey"] = mountKey,
                ["prefabName"] = prefab.name,
                ["objFileName"] = objFileName,
                ["meshes"] = meshes,
                ["mergedMin"] = exportedVertexCount > 0 ? VectorToArray(mergedMin) : null,
                ["mergedMax"] = exportedVertexCount > 0 ? VectorToArray(mergedMax) : null,
                ["mergedSize"] = exportedVertexCount > 0 ? VectorToArray(mergedSize) : null,
                ["largestDimension"] = exportedVertexCount > 0 ? MaxComponent(mergedSize) : null,
                ["largestDimensionAxis"] = exportedVertexCount > 0 ? LargestAxisName(mergedSize) : null
            };
        }

        private static IEnumerable<MeshRenderer> SelectRenderers(GameObject root)
        {
            var lod0Renderers = new HashSet<Renderer>();
            var lowerLodRenderers = new HashSet<Renderer>();
            foreach (var lodGroup in root.GetComponentsInChildren<LODGroup>(true))
            {
                var lods = lodGroup.GetLODs();
                for (var index = 0; index < lods.Length; index++)
                {
                    var renderers = lods[index].renderers ?? Array.Empty<Renderer>();
                    if (index == 0)
                    {
                        foreach (var renderer in renderers)
                        {
                            lod0Renderers.Add(renderer);
                        }
                    }
                    else
                    {
                        foreach (var renderer in renderers)
                        {
                            lowerLodRenderers.Add(renderer);
                        }
                    }
                }
            }

            foreach (var renderer in root.GetComponentsInChildren<MeshRenderer>(true))
            {
                if (!renderer.enabled)
                {
                    continue;
                }
                if (lowerLodRenderers.Contains(renderer) && !lod0Renderers.Contains(renderer))
                {
                    continue;
                }
                yield return renderer;
            }
        }

        private static bool TryReadMeshGeometry(Mesh mesh, out Vector3[] vertices, out int[][] submeshTriangles, out int triangleCount, out string readMethod, out string error)
        {
            vertices = null;
            submeshTriangles = null;
            triangleCount = 0;
            readMethod = null;
            error = null;
            try
            {
                if (mesh.isReadable)
                {
                    vertices = mesh.vertices ?? Array.Empty<Vector3>();
                    submeshTriangles = new int[mesh.subMeshCount][];
                    triangleCount = 0;
                    for (var submesh = 0; submesh < mesh.subMeshCount; submesh++)
                    {
                        var triangles = mesh.GetTriangles(submesh) ?? Array.Empty<int>();
                        submeshTriangles[submesh] = triangles;
                        triangleCount += triangles.Length / 3;
                    }
                    readMethod = "cpu";
                    return true;
                }
                return TryReadGpuReadback(mesh, out vertices, out submeshTriangles, out triangleCount, out error);
            }
            catch (Exception exception)
            {
                error = $"{exception.GetType().Name}: {exception.Message}";
                return false;
            }
        }

        private static bool TryReadGpuReadback(Mesh mesh, out Vector3[] vertices, out int[][] submeshTriangles, out int triangleCount, out string error)
        {
            vertices = null;
            submeshTriangles = null;
            triangleCount = 0;
            error = null;
            GraphicsBuffer vertexBuffer = null;
            GraphicsBuffer indexBuffer = null;
            try
            {
                var stream = mesh.GetVertexAttributeStream(VertexAttribute.Position);
                var offset = mesh.GetVertexAttributeOffset(VertexAttribute.Position);
                var format = mesh.GetVertexAttributeFormat(VertexAttribute.Position);
                var dimension = mesh.GetVertexAttributeDimension(VertexAttribute.Position);
                if (stream < 0)
                {
                    error = "Mesh has no position vertex attribute.";
                    return false;
                }
                if (format != VertexAttributeFormat.Float32 || dimension < 3)
                {
                    error = $"Position vertex attribute is not Float32 with dimension >= 3 (format {format}, dimension {dimension}).";
                    return false;
                }
                var stride = mesh.GetVertexBufferStride(stream);
                if (stride <= 0 || offset < 0 || offset + 3 * sizeof(float) > stride)
                {
                    error = $"Invalid vertex buffer layout (stride {stride}, offset {offset}).";
                    return false;
                }
                if (mesh.vertexCount <= 0)
                {
                    error = "Mesh has no vertices.";
                    return false;
                }

                vertexBuffer = mesh.GetVertexBuffer(stream);
                if (vertexBuffer == null)
                {
                    error = "Vertex buffer could not be acquired.";
                    return false;
                }
                var vertexBytes = new byte[vertexBuffer.count * vertexBuffer.stride];
                vertexBuffer.GetData(vertexBytes);
                vertices = new Vector3[mesh.vertexCount];
                for (var index = 0; index < mesh.vertexCount; index++)
                {
                    var byteIndex = index * stride + offset;
                    if (byteIndex < 0 || byteIndex + 3 * sizeof(float) > vertexBytes.Length)
                    {
                        error = "Vertex buffer is smaller than expected.";
                        return false;
                    }
                    vertices[index] = new Vector3(
                        BitConverter.ToSingle(vertexBytes, byteIndex),
                        BitConverter.ToSingle(vertexBytes, byteIndex + sizeof(float)),
                        BitConverter.ToSingle(vertexBytes, byteIndex + 2 * sizeof(float)));
                }

                indexBuffer = mesh.GetIndexBuffer();
                if (indexBuffer == null)
                {
                    error = "Index buffer could not be acquired.";
                    return false;
                }
                var indexSize = mesh.indexFormat == IndexFormat.UInt32 ? sizeof(int) : sizeof(ushort);
                if (indexBuffer.stride != indexSize)
                {
                    error = $"Index buffer stride {indexBuffer.stride} does not match index format {mesh.indexFormat}.";
                    return false;
                }
                var indexBytes = new byte[indexBuffer.count * indexBuffer.stride];
                indexBuffer.GetData(indexBytes);

                submeshTriangles = new int[mesh.subMeshCount][];
                triangleCount = 0;
                for (var submesh = 0; submesh < mesh.subMeshCount; submesh++)
                {
                    var descriptor = mesh.GetSubMesh(submesh);
                    if (descriptor.topology != MeshTopology.Triangles)
                    {
                        error = $"Submesh {submesh} topology is {descriptor.topology}, expected Triangles.";
                        return false;
                    }
                    if (descriptor.indexCount % 3 != 0)
                    {
                        error = $"Submesh {submesh} index count {descriptor.indexCount} is not a multiple of 3.";
                        return false;
                    }
                    var triangles = new int[descriptor.indexCount];
                    for (var index = 0; index < descriptor.indexCount; index++)
                    {
                        var byteIndex = (descriptor.indexStart + index) * indexSize;
                        if (byteIndex < 0 || byteIndex + indexSize > indexBytes.Length)
                        {
                            error = "Index buffer is smaller than expected.";
                            return false;
                        }
                        var rawIndex = indexSize == sizeof(int)
                            ? BitConverter.ToInt32(indexBytes, byteIndex)
                            : BitConverter.ToUInt16(indexBytes, byteIndex);
                        var vertexIndex = rawIndex + descriptor.baseVertex;
                        if (vertexIndex < 0 || vertexIndex >= mesh.vertexCount)
                        {
                            error = $"Index {rawIndex} (+ baseVertex {descriptor.baseVertex}) is out of range for {mesh.vertexCount} vertices.";
                            return false;
                        }
                        triangles[index] = vertexIndex;
                    }
                    submeshTriangles[submesh] = triangles;
                    triangleCount += descriptor.indexCount / 3;
                }
                return true;
            }
            catch (Exception exception)
            {
                error = $"{exception.GetType().Name}: {exception.Message}";
                return false;
            }
            finally
            {
                vertexBuffer?.Dispose();
                indexBuffer?.Dispose();
            }
        }

        private static string ObjFileName(string mountKey)
        {
            var baseName = mountKey.EndsWith("_single", StringComparison.Ordinal)
                ? mountKey.Substring(0, mountKey.Length - "_single".Length)
                : mountKey;
            var invalid = Path.GetInvalidFileNameChars();
            var safe = new string(baseName.Select(character => invalid.Contains(character) ? '_' : character).ToArray());
            return safe + ".geometry.obj";
        }

        private static string FormatVector(Vector3 value)
        {
            return string.Format(CultureInfo.InvariantCulture, "v {0} {1} {2}",
                value.x.ToString("G9", CultureInfo.InvariantCulture),
                value.y.ToString("G9", CultureInfo.InvariantCulture),
                value.z.ToString("G9", CultureInfo.InvariantCulture));
        }

        private static JArray VectorToArray(Vector3 value)
        {
            return new JArray(value.x, value.y, value.z);
        }

        private static bool IsFinite(Vector3 value)
        {
            return float.IsFinite(value.x) && float.IsFinite(value.y) && float.IsFinite(value.z);
        }

        private static float MaxComponent(Vector3 value)
        {
            return Mathf.Max(Mathf.Max(value.x, value.y), value.z);
        }

        private static string LargestAxisName(Vector3 value)
        {
            var max = MaxComponent(value);
            if (value.x == max)
            {
                return "x";
            }
            if (value.y == max)
            {
                return "y";
            }
            return "z";
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

        private static void WriteJson(string path, JToken document)
        {
            var json = document.ToString(Formatting.Indented) + Environment.NewLine;
            File.WriteAllText(path, json, new UTF8Encoding(false));
        }
    }
}
