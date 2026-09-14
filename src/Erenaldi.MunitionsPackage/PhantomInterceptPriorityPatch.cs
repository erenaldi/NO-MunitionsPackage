using HarmonyLib;

namespace Erenaldi.MunitionsPackage
{
    [HarmonyPatch(typeof(Missile), nameof(Missile.InterceptPriority))]
    internal static class PhantomInterceptPriorityPatch
    {
        private static void Postfix(Missile __instance, ref float __result)
        {
            if (__result <= 0f && PhantomCloner.IsPhantom(__instance))
            {
                __result = 1f;
            }
        }
    }

    [HarmonyPatch(typeof(Missile), nameof(Missile.Arm))]
    internal static class PhantomArmPatch
    {
        private static bool Prefix(Missile __instance)
        {
            return !PhantomCloner.IsPhantom(__instance);
        }
    }
}
