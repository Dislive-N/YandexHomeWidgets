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


# 1.5.2: a cohesive room-first dashboard and a clearer device-card system.
main = main_path.read_text(encoding="utf-8")
if 'key = "dashboard_hero"' not in main:
    main = main.replace('AppPage.HOME -> "Дом"', 'AppPage.HOME -> "Мой дом"')
    start_marker = '        item(span = { GridItemSpan(maxLineSpan) }, key = "home_status_strip") {\n'
    end_marker = '        item(span = { GridItemSpan(maxLineSpan) }, key = "location_weather") {\n'
    start = main.find(start_marker)
    end = main.find(end_marker, start)
    if start < 0 or end <= start:
        raise SystemExit("Could not locate home status strip for dashboard hero")
    hero = '''        item(span = { GridItemSpan(maxLineSpan) }, key = "dashboard_hero") {
            Column(
                modifier = Modifier.fillMaxWidth()
                    .clip(RoundedCornerShape(26.dp))
                    .background(Brush.linearGradient(listOf(Color(0xFF302B42), Color(0xFF242C3A), Color(0xFF202D35))))
                    .border(1.dp, Color.White.copy(alpha = 0.09f), RoundedCornerShape(26.dp))
                    .padding(horizontal = 17.dp, vertical = 16.dp),
                verticalArrangement = Arrangement.spacedBy(13.dp)
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                        Text("СОСТОЯНИЕ ДОМА", color = Color.White.copy(alpha = 0.66f), fontSize = 9.sp, fontWeight = FontWeight.Bold, letterSpacing = 1.2.sp)
                        Text(
                            when {
                                devices.isEmpty() -> "Подключи свой дом"
                                offlineCount > 0 -> "Есть устройства без связи"
                                else -> "Дома всё спокойно"
                            },
                            color = Color.White, fontSize = 20.sp, fontWeight = FontWeight.Bold,
                            maxLines = 1, overflow = TextOverflow.Ellipsis
                        )
                        Text(activeCount.toString() + " включено · " + onlineCount + " в сети из " + devices.size, color = Color.White.copy(alpha = 0.76f), fontSize = 11.sp, maxLines = 1, overflow = TextOverflow.Ellipsis)
                    }
                    Box(Modifier.size(54.dp).clip(CircleShape).background(Color.White.copy(alpha = 0.10f)), contentAlignment = Alignment.Center) {
                        SmartGlyph("home", Modifier.size(27.dp), Color(0xFFD8C8FF))
                    }
                }
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    DashboardStat("Включено", activeCount.toString(), Modifier.weight(1f))
                    DashboardStat("В сети", onlineCount.toString(), Modifier.weight(1f))
                    DashboardStat(if (offlineCount > 0) "Без связи" else "Стабильно", if (offlineCount > 0) offlineCount.toString() else "OK", Modifier.weight(1f))
                }
            }
        }
'''
    main = main[:start] + hero + main[end:]

    old_filter = '''    val visibleDevices = remember(devices, selectedCategory) {
        when (selectedCategory) {
            "Все" -> devices
            "Проблемы" -> devices.filterNot { it.isOnline }
            "Свет" -> devices.filter { dashboardDeviceCategory(it) == "Освещение" }
            else -> devices.filter { dashboardDeviceCategory(it) == selectedCategory }
        }
    }
'''
    new_filter = '''    val visibleDevices = remember(devices, selectedCategory) {
        when (selectedCategory) {
            "Все" -> devices
            "Не в сети" -> devices.filterNot { it.isOnline }
            "Избранное" -> devices.filter { it.isFavorite }
            "Свет", "Освещение" -> devices.filter { dashboardDeviceCategory(it) == "Освещение" }
            else -> devices.filter { dashboardDeviceCategory(it) == selectedCategory }
        }
    }
'''
    if old_filter in main:
        main = main.replace(old_filter, new_filter, 1)
    elif new_filter not in main:
        raise SystemExit("Could not update dashboard device filters")
    main = main.replace('    val favoriteDevices = visibleDevices.filter { it.isFavorite }',
                        '    val favoriteDevices = remember(devices) { devices.filter { it.isFavorite } }', 1)

    actions_start = '        item(span = { GridItemSpan(maxLineSpan) }, key = "home_actions") {\n'
    actions_end = '        item(span = { GridItemSpan(maxLineSpan) }, key = "device_categories") {\n'
    start = main.find(actions_start)
    end = main.find(actions_end, start)
    if start < 0 or end <= start:
        raise SystemExit("Could not locate dashboard quick actions")
    quick_actions = '''        item(span = { GridItemSpan(maxLineSpan) }, key = "home_actions") {
            val lights = devices.filter { dashboardDeviceCategory(it) == "Освещение" && it.canToggle && it.isOnline }
            val outlets = devices.filter { dashboardDeviceCategory(it) == "Розетки" && it.canToggle && it.isOnline }
            val allLightsOn = lights.isNotEmpty() && lights.all { it.onOff == true }
            val allOutletsOn = outlets.isNotEmpty() && outlets.all { it.onOff == true }
            Row(Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                HomeQuickButton(if (allLightsOn) "Выключить свет" else "Включить свет", Color(0xFF9B7BFA),
                    { onToggleGroup(lights, !allLightsOn) }, Modifier.widthIn(min = 126.dp), enabled = lights.isNotEmpty() && !isBusy)
                HomeQuickButton(if (allOutletsOn) "Выключить розетки" else "Включить розетки", Color(0xFF42BFA5),
                    { onToggleGroup(outlets, !allOutletsOn) }, Modifier.widthIn(min = 142.dp), enabled = outlets.isNotEmpty() && !isBusy)
                HomeQuickButton("Группы", Color(0xFF658EDB), onOpenGroups, Modifier.widthIn(min = 98.dp))
                HomeQuickButton("Аналитика", Color(0xFF8D83BD), onAnalytics, Modifier.widthIn(min = 112.dp))
            }
        }
'''
    main = main[:start] + quick_actions + main[end:]

    old_categories = '''                listOf("Все", "Проблемы", "Свет", "Розетки", "Климат", "Безопасность", "Датчики", "Другое").forEach { category ->
                    val count = when (category) {
                        "Все" -> devices.size
                        "Проблемы" -> offlineCount
                        "Свет" -> devices.count { dashboardDeviceCategory(it) == "Освещение" }
                        else -> devices.count { dashboardDeviceCategory(it) == category }
                    }
'''
    new_categories = '''                listOf("Все", "Не в сети", "Избранное", "Освещение", "Розетки", "Климат", "Безопасность", "Датчики", "Медиа", "Другое").forEach { category ->
                    val count = when (category) {
                        "Все" -> devices.size
                        "Не в сети" -> offlineCount
                        "Избранное" -> favoriteDevices.size
                        else -> devices.count { dashboardDeviceCategory(it) == category }
                    }
'''
    if old_categories in main:
        main = main.replace(old_categories, new_categories, 1)
    elif new_categories not in main:
        raise SystemExit("Could not update dashboard category chips")

    fav_start = '            if (favoriteDevices.isNotEmpty() && selectedCategory == "Все") {\n'
    fav_end = '            item(span = { GridItemSpan(maxLineSpan) }, key = "devices_section_header") {\n'
    start = main.find(fav_start)
    end = main.find(fav_end, start)
    if start < 0 or end <= start:
        raise SystemExit("Could not locate favourites section")
    favorites = '''            if (favoriteDevices.isNotEmpty() && selectedCategory == "Все") {
                item(span = { GridItemSpan(maxLineSpan) }, key = "favorites_shelf") {
                    Column(verticalArrangement = Arrangement.spacedBy(9.dp)) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Text("Избранное", fontSize = 18.sp, fontWeight = FontWeight.Bold, modifier = Modifier.weight(1f))
                            Text(favoriteDevices.size.toString(), color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.58f), fontSize = 12.sp, fontWeight = FontWeight.Medium)
                        }
                        Row(Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                            favoriteDevices.forEach { device ->
                                Box(Modifier.width(cardWidthDp.dp)) {
                                    CompactDeviceTile(
                                        device = device, enabled = !isBusy && device.id !in pendingDeviceIds,
                                        pending = device.id in pendingDeviceIds, cardSize = "small",
                                        cardWidthDp = cardWidthDp, cardHeightDp = cardHeightDp.coerceAtMost(164),
                                        onFavorite = { onFavoriteChange(device, it) }, onOpen = { onOpenDevice(device) },
                                        onToggle = { onToggle(device, it) }
                                    )
                                }
                            }
                        }
                    }
                }
            }
'''
    main = main[:start] + favorites + main[end:]

    # Replace the room title row by locating it relative to its room data binding.
    room_anchor = 'val roomDevices = ungroupedByRoom[roomName].orEmpty()'
    room_at = main.find(room_anchor)
    room_start = main.find('                        Row(modifier = Modifier.fillMaxWidth().padding(top = 7.dp)', room_at)
    room_end = main.find('\n                        }\n', room_start)
    if room_at < 0 or room_start < 0 or room_end < 0:
        raise SystemExit("Could not locate room header")
    room_end += len('\n                        }\n')
    room_header = '''                        val switchableRoomDevices = roomDevices.filter { it.canToggle && it.isOnline }
                        val roomIsOn = switchableRoomDevices.isNotEmpty() && switchableRoomDevices.all { it.onOff == true }
                        val roomHasPending = switchableRoomDevices.any { it.id in pendingDeviceIds }
                        Row(Modifier.fillMaxWidth().padding(top = 9.dp, bottom = 1.dp), verticalAlignment = Alignment.CenterVertically) {
                            Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(2.dp)) {
                                Text(roomName, fontSize = 18.sp, fontWeight = FontWeight.Bold)
                                Text(roomDevices.size.toString() + " устройств", color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.56f), fontSize = 11.sp)
                            }
                            if (switchableRoomDevices.isNotEmpty()) {
                                TextButton(
                                    onClick = { onToggleGroup(switchableRoomDevices, !roomIsOn) },
                                    enabled = !isBusy && !roomHasPending,
                                    contentPadding = PaddingValues(horizontal = 10.dp, vertical = 5.dp)
                                ) {
                                    Text(if (roomIsOn) "Выключить всё" else "Включить всё", fontSize = 11.sp, fontWeight = FontWeight.SemiBold)
                                }
                            }
                        }
'''
    main = main[:room_start] + room_header + main[room_end:]

    quick_start = '@Composable\nprivate fun HomeQuickButton('
    quick_end = '\n@Composable\nprivate fun HistoryQuickButton('
    start = main.find(quick_start)
    end = main.find(quick_end, start)
    if start < 0 or end <= start:
        raise SystemExit("Could not locate HomeQuickButton")
    quick_helper = '''@Composable
private fun HomeQuickButton(
    title: String,
    tint: Color,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    enabled: Boolean = true
) {
    OutlinedButton(
        onClick = onClick, enabled = enabled, modifier = modifier.height(42.dp),
        shape = RoundedCornerShape(15.dp),
        border = androidx.compose.foundation.BorderStroke(1.dp, tint.copy(alpha = if (enabled) 0.42f else 0.15f)),
        contentPadding = PaddingValues(horizontal = 13.dp, vertical = 5.dp),
        colors = ButtonDefaults.outlinedButtonColors(contentColor = tint, disabledContentColor = tint.copy(alpha = 0.42f))
    ) {
        Text(title, fontSize = 11.sp, fontWeight = FontWeight.SemiBold, maxLines = 1, overflow = TextOverflow.Ellipsis)
    }
}
'''
    main = main[:start] + quick_helper + main[end:]

    main = main.replace(
        'Text(label, color = Color.White.copy(alpha = 0.68f), fontSize = 8.sp, fontWeight = FontWeight.Bold, letterSpacing = 0.5.sp, maxLines = 1)',
        'Text(label, color = Color.White.copy(alpha = 0.72f), fontSize = 9.sp, fontWeight = FontWeight.SemiBold, maxLines = 1)',
        1
    )

    tile_start = '@Composable\nprivate fun CompactDeviceTile('
    tile_end = '\nprivate fun deviceIcon(type:'
    start = main.find(tile_start)
    end = main.find(tile_end, start)
    if start < 0 or end <= start:
        raise SystemExit("Could not locate CompactDeviceTile")
    tile = '''@Composable
private fun CompactDeviceTile(
    device: HomeDevice,
    enabled: Boolean,
    pending: Boolean,
    cardSize: String,
    cardWidthDp: Int,
    cardHeightDp: Int,
    onFavorite: (Boolean) -> Unit,
    onOpen: () -> Unit,
    onToggle: (Boolean) -> Unit
) {
    val on = device.onOff == true
    val offline = !device.isOnline
    val iconSize = when (cardSize) { "large" -> 68.dp; "small" -> 48.dp; else -> 58.dp }
    val powerSize = when (cardSize) { "large" -> 48.dp; "small" -> 36.dp; else -> 42.dp }
    val titleSize = when (cardSize) { "large" -> 16.sp; "small" -> 13.sp; else -> 14.sp }
    val cardShape = RoundedCornerShape(22.dp)
    val tileColor = when { offline -> Color(0xFF332A32); on -> Color(0xFF302D3D); else -> Color(0xFF292D37) }
    val outline = when {
        offline -> Color(0xFFFF6578).copy(alpha = 0.34f)
        on -> Color(0xFF9B7BFA).copy(alpha = 0.34f)
        else -> Color.White.copy(alpha = 0.055f)
    }
    val statusColor = when { offline -> Color(0xFFFF6477); on -> Color(0xFF53D6A7); else -> Color(0xFF9CA4B2) }
    Box(Modifier.fillMaxWidth(), contentAlignment = Alignment.TopCenter) {
        Box(
            modifier = Modifier.widthIn(max = cardWidthDp.dp).fillMaxWidth()
                .height(cardHeightDp.coerceIn(148, 280).dp)
                .clip(cardShape).background(tileColor).border(1.dp, outline, cardShape)
                .clickable(onClick = onOpen)
                .padding(if (cardSize == "large") 15.dp else 13.dp)
        ) {
            Column(Modifier.fillMaxSize(), verticalArrangement = Arrangement.SpaceBetween) {
                Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                    Box(
                        Modifier.size(iconSize + 8.dp).clip(RoundedCornerShape(19.dp))
                            .background(if (offline) Color.White.copy(alpha = 0.045f) else if (on) Color(0xFF9B7BFA).copy(alpha = 0.15f) else Color.White.copy(alpha = 0.055f)),
                        contentAlignment = Alignment.Center
                    ) {
                        SmartGlyph(deviceIconKind(device.type, device.name), Modifier.size(iconSize),
                            if (offline) Color(0xFF9298A5) else if (on) Color(0xFFD2C2FF) else Color(0xFFB8BFCC))
                    }
                    Spacer(Modifier.weight(1f))
                    Box(
                        Modifier.size(36.dp).clip(CircleShape).background(Color.White.copy(alpha = 0.055f))
                            .clickable { onFavorite(!device.isFavorite) },
                        contentAlignment = Alignment.Center
                    ) {
                        Text(if (device.isFavorite) "★" else "☆",
                            color = if (device.isFavorite) Color(0xFFFFD166) else Color.White.copy(alpha = 0.56f), fontSize = 19.sp)
                    }
                }
                Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                    Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                        Text(device.name, color = Color(0xFFF3F4F8), fontWeight = FontWeight.Bold,
                            fontSize = titleSize, maxLines = 1, overflow = TextOverflow.Ellipsis)
                        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                            Box(Modifier.size(7.dp).clip(CircleShape).background(statusColor))
                            Text(
                                when {
                                    offline -> "Не в сети"
                                    pending && on -> "Включение…"
                                    pending && !on -> "Выключение…"
                                    on -> "Включено"
                                    device.onOff == false -> "Выключено"
                                    else -> "Готово к управлению"
                                },
                                color = if (offline) Color(0xFFFF7888) else Color.White.copy(alpha = 0.72f),
                                fontSize = 10.sp, fontWeight = if (offline || on) FontWeight.SemiBold else FontWeight.Normal,
                                maxLines = 1, overflow = TextOverflow.Ellipsis
                            )
                        }
                        if (device.room.isNotBlank()) {
                            Text(device.room, color = Color.White.copy(alpha = 0.44f), fontSize = 9.sp,
                                maxLines = 1, overflow = TextOverflow.Ellipsis)
                        }
                    }
                    if (device.canToggle) {
                        Spacer(Modifier.width(9.dp))
                        Box(
                            Modifier.size(powerSize).clip(CircleShape)
                                .background(when { offline -> Color(0xFF4A4650); on -> Color(0xFF8059E8); else -> Color(0xFF414653) })
                                .clickable(enabled = enabled && !offline) { onToggle(!on) },
                            contentAlignment = Alignment.Center
                        ) {
                            if (pending) CircularProgressIndicator(Modifier.size(19.dp), strokeWidth = 2.dp, color = Color.White)
                            else SmartGlyph(if (on) "off" else "power", Modifier.size(24.dp), Color.White)
                        }
                    }
                }
            }
        }
    }
}
''';
    main = main[:start] + tile + main[end:]

    main = main.replace(
        'if (isConnected && page in setOf(AppPage.HOME, AppPage.SCENARIOS, AppPage.DEVICE, AppPage.GROUP_DETAILS, AppPage.ANALYTICS)) {',
        'if (isConnected && page in setOf(AppPage.HOME, AppPage.SCENARIOS, AppPage.HISTORY, AppPage.DEVICE, AppPage.GROUP_DETAILS, AppPage.ANALYTICS)) {',
        1
    )
    nav_tail = '''                        NavigationBarItem(
                            selected = page == AppPage.SCENARIOS,
                            onClick = { page = AppPage.SCENARIOS },
                            icon = { SmartGlyph("sparkles", Modifier.size(22.dp), Color.White.copy(alpha = if (page == AppPage.SCENARIOS) 1f else 0.72f)) }, label = { Text("Сценарии") },
                            colors = NavigationBarItemDefaults.colors(selectedIconColor = Color.White, selectedTextColor = Color.White, unselectedIconColor = Color.White.copy(alpha = 0.72f), unselectedTextColor = Color.White.copy(alpha = 0.72f), indicatorColor = Color.White.copy(alpha = 0.14f))
                        )
'''
    nav_add = nav_tail + '''                        NavigationBarItem(
                            selected = page == AppPage.HISTORY,
                            onClick = { history = HomeHistoryStore.load(context); page = AppPage.HISTORY },
                            icon = { SmartGlyph("clock", Modifier.size(22.dp), Color.White.copy(alpha = if (page == AppPage.HISTORY) 1f else 0.72f)) },
                            label = { Text("История") },
                            colors = NavigationBarItemDefaults.colors(selectedIconColor = Color.White, selectedTextColor = Color.White, unselectedIconColor = Color.White.copy(alpha = 0.72f), unselectedTextColor = Color.White.copy(alpha = 0.72f), indicatorColor = Color.White.copy(alpha = 0.14f))
                        )
'''
    if nav_tail in main:
        main = main.replace(nav_tail, nav_add, 1)
    elif 'selected = page == AppPage.HISTORY' not in main:
        raise SystemExit("Could not add history destination to bottom navigation")

    main = main.replace('listOf(Color(0xFF101C2B), Color(0xFF142B3A), Color(0xFF101B2A))',
                        'listOf(Color(0xFF22242D), Color(0xFF292B36), Color(0xFF20232C))', 1)
    main = main.replace(
        'background = Color(0xFF1C1D25),\n        surface = Color(0xFF2D3039).copy(alpha = glassOpacity),\n        surfaceVariant = Color(0xFF363943).copy(alpha = glassOpacity * 0.94f),',
        'background = Color(0xFF171922),\n        surface = Color(0xFF272B35).copy(alpha = glassOpacity),\n        surfaceVariant = Color(0xFF303642).copy(alpha = glassOpacity * 0.94f),', 1
    )
    main = main.replace('primary = Color(0xFFB5A0FF).copy(alpha = 0.78f + glassOpacity * 0.20f),',
                        'primary = Color(0xFFA78BFA).copy(alpha = 0.78f + glassOpacity * 0.20f),', 1)
    main = main.replace('secondary = Color(0xFF14B8A6).copy(alpha = 0.86f + glassOpacity * 0.14f),',
                        'secondary = Color(0xFF35CFA7).copy(alpha = 0.86f + glassOpacity * 0.14f),', 1)
    main = main.replace(
        'val activeCount = devices.count { it.onOff == true }',
        'val activeCount = devices.count { it.isOnline && it.onOff == true }',
        1
    )
    main = main.replace(
        'selected = page == AppPage.HOME,',
        'selected = page in setOf(AppPage.HOME, AppPage.DEVICE, AppPage.GROUP_DETAILS, AppPage.ANALYTICS),',
        1
    )
    main_path.write_text(main, encoding="utf-8")
else:
    print("Dashboard 1.5.2 visual refinement already present.")


print("Applied reference-style home screen, bold headings, and signature-aware update selection.")
