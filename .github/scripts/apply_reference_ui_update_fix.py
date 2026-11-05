#!/usr/bin/env python3
"""Apply the reference-style home screen and signature-aware APK update selection."""
from pathlib import Path
import re
import sys

project = Path(sys.argv[1])
main_path = project / "app/src/main/java/ru/dislive/yandexhomewidgets/MainActivity.kt"
updates_path = project / "app/src/main/java/ru/dislive/yandexhomewidgets/data/AppUpdates.kt"

main = main_path.read_text(encoding="utf-8")

def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count == 0 and new in source:
        return source
    if count != 1:
        raise SystemExit(f"Expected one {label}; found {count}")
    return source.replace(old, new, 1)

# Home header and consistent bold headings.
main = main.replace('AppPage.HOME -> "Мой дом"', 'AppPage.HOME -> "Дом"')
main = main.replace("FontWeight.SemiBold", "FontWeight.Bold")

# Neutral charcoal palette closer to the supplied Yandex Home / Sber references.
main = main.replace("background = Color(0xFF070A12)", "background = Color(0xFF1C1D25)")
main = main.replace("surface = Color(0xFF111827).copy(alpha = glassOpacity)", "surface = Color(0xFF2D3039).copy(alpha = glassOpacity)")
main = main.replace("surfaceVariant = Color(0xFF172033).copy(alpha = glassOpacity * 0.94f)", "surfaceVariant = Color(0xFF363943).copy(alpha = glassOpacity * 0.94f)")
main = main.replace(
    "colors = listOf(Color(0xFF070A12), Color(0xFF0C1728), Color(0xFF0B1E29), Color(0xFF070A12))",
    "colors = listOf(Color(0xFF1C1D25), Color(0xFF20212A), Color(0xFF191A22), Color(0xFF1C1D25))"
)
main = main.replace("Color(0xFF2563EB).copy(alpha = 0.24f)", "Color(0xFF8C83B8).copy(alpha = 0.055f)")
main = main.replace("Color(0xFF14B8A6).copy(alpha = 0.17f)", "Color(0xFF8A8D9B).copy(alpha = 0.035f)")

# Replace the oversized statistics panel with compact, horizontally-scrolling status cards.
summary_start = '        item(span = { GridItemSpan(maxLineSpan) }, key = "dashboard_summary") {\n'
summary_end = '        item(span = { GridItemSpan(maxLineSpan) }, key = "location_weather") {\n'
start = main.find(summary_start)
end = main.find(summary_end, start)
if start >= 0 and end > start:
    status_strip = '''        item(span = { GridItemSpan(maxLineSpan) }, key = "home_status_strip") {
            val lightingDevices = devices.filter { dashboardDeviceCategory(it) == "Освещение" }
            val socketDevices = devices.filter { dashboardDeviceCategory(it) == "Розетки" }
            val mediaDevices = devices.filter { dashboardDeviceCategory(it) == "Медиа" }
            Row(
                Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                HomeStatusChip(
                    "⌁",
                    if (offlineCount > 0) "Нет связи" else "Всё онлайн",
                    if (offlineCount > 0) "$offlineCount устройств" else "$onlineCount из ${devices.size} устройств",
                    if (offlineCount > 0) Color(0xFFFF5D70) else Color(0xFF54C99A)
                )
                HomeStatusChip(
                    "☼", "Свет",
                    "${lightingDevices.count { it.onOff == true }} из ${lightingDevices.size} включено",
                    Color(0xFF9A79FF)
                )
                HomeStatusChip(
                    "▣", "Розетки",
                    "${socketDevices.count { it.onOff == true }} из ${socketDevices.size} включено",
                    Color(0xFF9A79FF)
                )
                if (mediaDevices.isNotEmpty()) {
                    HomeStatusChip("◉", "Медиа", "${mediaDevices.size} устройств", Color(0xFF84B9F5))
                }
            }
        }
'''
    main = main[:start] + status_strip + main[end:]
elif 'key = "home_status_strip"' not in main:
    raise SystemExit("Could not locate dashboard summary section")

# Make device cards flatter and closer to the reference apps while preserving the offline warning.
main = replace_once(
    main,
    '''    val tileColor = when {
        offline -> Color(0xFF101820).copy(alpha = 0.96f)
        else -> Color(0xFF111C2B).copy(alpha = 0.92f)
    }''',
    '''    val tileColor = if (offline) Color(0xFF2B2D35).copy(alpha = 0.92f) else Color(0xFF30323B).copy(alpha = 0.98f)''',
    "device tile color"
)
main = main.replace(
    "if (offline) Color(0xFFF43F5E).copy(alpha = 0.42f) else Color.White.copy(alpha = 0.10f)",
    "if (offline) Color(0xFFFF5D70).copy(alpha = 0.35f) else Color.White.copy(alpha = 0.035f)"
)
main = main.replace(
    "if (offline) Color(0xFF34343A) else if (on) Color(0xFF25B56A) else Color(0xFFE34D59)",
    "if (offline) Color(0xFF4B4D57) else if (on) Color(0xFF7546E8) else Color(0xFF555965)"
)
main = main.replace(
    "Brush.horizontalGradient(listOf(Color(0xFF2563EB).copy(alpha = 0.15f), Color(0xFF14B8A6).copy(alpha = 0.09f)))",
    "Brush.horizontalGradient(listOf(Color(0xFF7658BA).copy(alpha = 0.16f), Color(0xFF555A6C).copy(alpha = 0.10f)))"
)

# Add the compact status-card composable once.
if "private fun HomeStatusChip(" not in main:
    marker = "\n@Composable\nprivate fun HomeQuickButton("
    helper = '''
@Composable
private fun HomeStatusChip(
    icon: String,
    title: String,
    detail: String,
    tint: Color
) {
    Row(
        modifier = Modifier
            .height(60.dp)
            .clip(RoundedCornerShape(19.dp))
            .background(Color(0xFF30323B))
            .padding(horizontal = 12.dp, vertical = 8.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(9.dp)
    ) {
        Box(
            Modifier.size(36.dp).clip(CircleShape).background(tint.copy(alpha = 0.16f)),
            contentAlignment = Alignment.Center
        ) {
            Text(icon, color = tint, fontSize = 19.sp, fontWeight = FontWeight.Bold)
        }
        Column(verticalArrangement = Arrangement.spacedBy(2.dp)) {
            Text(title, color = Color.White, fontSize = 12.sp, fontWeight = FontWeight.Bold, maxLines = 1)
            Text(detail, color = Color.White.copy(alpha = 0.64f), fontSize = 10.sp, maxLines = 1)
        }
    }
}
'''
    if main.count(marker) != 1:
        raise SystemExit("Could not locate HomeQuickButton insertion point")
    main = main.replace(marker, "\n" + helper + marker, 1)

main_path.write_text(main, encoding="utf-8")

# Select the APK signed with the same certificate as the installed application.
updates = updates_path.read_text(encoding="utf-8")
if "LEGACY_SIGNING_SHA256" not in updates:
    updates = replace_once(
        updates,
        "import kotlinx.coroutines.Dispatchers",
        "import android.content.Context\nimport android.content.pm.PackageManager\nimport android.os.Build\nimport java.security.MessageDigest\nimport kotlinx.coroutines.Dispatchers",
        "Android signature imports"
    )
    updates = replace_once(
        updates,
        "    val notes: String\n)",
        "    val notes: String,\n    val apkVariant: String = \"Standard\"\n)",
        "update info variant field"
    )
    signature_pattern = re.compile(
        r"    suspend fun check\([^)]*\)(?:\s*:\s*[^=\n]+)?\s*=\s*withContext\(Dispatchers\.IO\) \{"
    )
    updates, signature_count = signature_pattern.subn(
        "    private const val LEGACY_SIGNING_SHA256 = \"380579e149bd610f4c5aa48691bd7d7ea872c113075d0c8fcb99845b0603351c\"\\n\\n"
        "    suspend fun check(context: Context, installedVersion: String, installedBuildCode: Int) = withContext(Dispatchers.IO) {\\n"
        "        val legacyInstall = isLegacySignedInstall(context)",
        updates,
        count=1
    )
    if signature_count != 1:
        raise SystemExit("Could not safely locate AppUpdateChecker.check signature")
    old_asset = '''                    val apkUrl = release.optJSONArray("assets")?.let { assets ->
                        (0 until assets.length()).mapNotNull { assets.optJSONObject(it) }
                            .firstOrNull {
                                it.optString("name").endsWith(".apk", ignoreCase = true) &&
                                    it.optLong("size", 0L) > 1_000_000L
                            }
                            ?.optString("browser_download_url")
                            ?.takeIf { it.startsWith("https://", ignoreCase = true) }
                    }'''
    new_asset = '''                    val apkUrl = release.optJSONArray("assets")?.let { assets ->
                        val apks = (0 until assets.length()).mapNotNull { assets.optJSONObject(it) }
                            .filter {
                                it.optString("name").endsWith(".apk", ignoreCase = true) &&
                                    it.optLong("size", 0L) > 1_000_000L
                            }
                        apks.firstOrNull { asset ->
                            asset.optString("name").endsWith("-legacy.apk", ignoreCase = true) == legacyInstall
                        }?.optString("browser_download_url")
                            ?.takeIf { it.startsWith("https://", ignoreCase = true) }
                    }'''
    updates = replace_once(updates, old_asset, new_asset, "APK asset selector")
    updates = replace_once(
        updates,
        "                notes = release.optString(\"body\").take(1200)\n",
        "                notes = release.optString(\"body\").take(1200),\n                apkVariant = if (legacyInstall) \"Legacy (совместимая подпись)\" else \"Standard\"\n",
        "update info build variant"
    )
    helper_marker = "\n    private fun compareVersions("
    helper = '''
    private fun isLegacySignedInstall(context: Context): Boolean = runCatching {
        val packageManager = context.packageManager
        @Suppress("DEPRECATION")
        val packageInfo = if (Build.VERSION.SDK_INT >= 28) {
            packageManager.getPackageInfo(context.packageName, PackageManager.GET_SIGNING_CERTIFICATES)
        } else {
            packageManager.getPackageInfo(context.packageName, PackageManager.GET_SIGNATURES)
        }
        val signatures = if (Build.VERSION.SDK_INT >= 28) {
            packageInfo.signingInfo?.apkContentsSigners?.toList().orEmpty()
        } else {
            @Suppress("DEPRECATION")
            packageInfo.signatures?.toList().orEmpty()
        }
        signatures.any { signature ->
            MessageDigest.getInstance("SHA-256").digest(signature.toByteArray())
                .joinToString("") { byte -> "%02x".format(byte) } == LEGACY_SIGNING_SHA256
        }
    }.getOrDefault(false)
'''
    if updates.count(helper_marker) != 1:
        raise SystemExit("Could not locate AppUpdateChecker helper insertion point")
    updates = updates.replace(helper_marker, "\n" + helper + helper_marker, 1)

updates_path.write_text(updates, encoding="utf-8")

# Pass application context so the updater can inspect the installed signing certificate.
main = main_path.read_text(encoding="utf-8")
main = replace_once(
    main,
    "AppUpdateChecker.check(BuildConfig.VERSION_NAME, BuildConfig.VERSION_CODE)",
    "AppUpdateChecker.check(context, BuildConfig.VERSION_NAME, BuildConfig.VERSION_CODE)",
    "updater call site"
)
main = main.replace(
    'updateMessage = if (found == null) "Установлена последняя доступная версия (${BuildConfig.VERSION_NAME})." else "Доступна версия ${found.version} (сборка ${found.buildCode})."',
    'updateMessage = if (found == null) "Установлена последняя доступная версия (${BuildConfig.VERSION_NAME})." else "Доступна версия ${found.version} · ${found.apkVariant} (сборка ${found.buildCode})."'
)
main = main.replace(
    'Text("Скачать APK ${updateInfo.version}")',
    'Text("Скачать APK ${updateInfo.version} · ${updateInfo.apkVariant}")'
)
main = main.replace(
    "Обновление скачивается через браузер. После загрузки открой APK из загрузок и подтверди установку в Android. Приложение не устанавливает собственные обновления и не запрашивает разрешение на установку других приложений.",
    "Подбирается APK с подписью, совместимой с установленной версией приложения. После загрузки открой файл из загрузок и подтверди установку в Android."
)
main_path.write_text(main, encoding="utf-8")

print("Applied reference-style home screen, bold headings, and signature-aware update selection.")
