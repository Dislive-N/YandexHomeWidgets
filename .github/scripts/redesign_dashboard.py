#!/usr/bin/env python3
"""Migrate the current Compose dashboard to the v1.5 UI."""
from pathlib import Path
import subprocess
import sys

source = Path(sys.argv[1])
subprocess.run([sys.executable, str(Path(__file__).with_name("apply_reference_ui_update_fix.py")), str(source.parents[7])], check=True)
print("Applied reference UI and compatible APK updater patch.")
raise SystemExit(0)

tile_start = text.find("@Composable\nprivate fun CompactDeviceTile(")
tile_end = text.find("\nprivate fun deviceIcon(type:", tile_start)
tile_source = text[tile_start:tile_end] if tile_start >= 0 and tile_end >= 0 else ""
if (
    'key = "favorites_shelf"' in text
    and 'private fun DashboardStatusChip(' in text
    and "Modifier.widthIn(max = cardWidthDp.dp)" in tile_source
):
    print("Dashboard v1.5 already applied.")
    subprocess.run([sys.executable, str(Path(__file__).with_name("apply_reference_ui_update_fix.py")), str(source.parents[7])], check=True)
    raise SystemExit(0)


def replace_once(old: str, new: str, label: str) -> None:
    global text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"Expected exactly one {label}; found {count}")
    text = text.replace(old, new, 1)


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
            "Освещение" -> devices.filter { dashboardDeviceCategory(it) == "Освещение" }
            "Свет" -> devices.filter { dashboardDeviceCategory(it) == "Освещение" }
            else -> devices.filter { dashboardDeviceCategory(it) == selectedCategory }
        }
    }
'''
replace_once(old_filter, new_filter, "device filter block")
replace_once(
    '    val favoriteDevices = visibleDevices.filter { it.isFavorite }',
    '    val favoriteDevices = remember(devices) { devices.filter { it.isFavorite } }',
    "favorite-device source",
)

summary_start = '        item(span = { GridItemSpan(maxLineSpan) }, key = "dashboard_summary") {\n'
summary_end = '        item(span = { GridItemSpan(maxLineSpan) }, key = "location_weather") {\n'
start = text.find(summary_start)
end = text.find(summary_end, start)
if start < 0 or end <= start:
    raise SystemExit("Could not find dashboard summary boundaries")

summary = '''        item(span = { GridItemSpan(maxLineSpan) }, key = "dashboard_summary") {
            Box(
                modifier = Modifier.fillMaxWidth()
                    .background(
                        Brush.linearGradient(listOf(Color(0xFF172B45), Color(0xFF164252), Color(0xFF13263A))),
                        RoundedCornerShape(24.dp)
                    )
                    .border(1.dp, Color.White.copy(alpha = 0.10f), RoundedCornerShape(24.dp))
                    .padding(horizontal = 16.dp, vertical = 15.dp)
            ) {
                Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Column(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(3.dp)) {
                            Text("СОСТОЯНИЕ ДОМА", color = Color.White.copy(alpha = 0.70f), fontSize = 9.sp, fontWeight = FontWeight.Bold, letterSpacing = 1.25.sp)
                            Text(
                                when {
                                    devices.isEmpty() -> "Добавь первое устройство"
                                    offlineCount > 0 -> "Проверь соединение"
                                    else -> "Всё под контролем"
                                },
                                color = Color.White,
                                fontSize = 20.sp,
                                fontWeight = FontWeight.Bold,
                                maxLines = 1,
                                overflow = TextOverflow.Ellipsis
                            )
                            Text("$activeCount включено из \${devices.size} устройств", color = Color.White.copy(alpha = 0.82f), fontSize = 11.sp)
                        }
                        Box(
                            modifier = Modifier.size(46.dp)
                                .background(Color.White.copy(alpha = 0.12f), CircleShape),
                            contentAlignment = Alignment.Center
                        ) {
                            SmartGlyph("home", Modifier.size(25.dp), Color.White)
                        }
                    }
                    Row(horizontalArrangement = Arrangement.spacedBy(7.dp), modifier = Modifier.fillMaxWidth()) {
                        DashboardStatusChip("Включено", activeCount.toString(), Color(0xFF41D69A), Modifier.weight(1f))
                        DashboardStatusChip("В сети", onlineCount.toString(), Color(0xFF75C6FF), Modifier.weight(1f))
                        DashboardStatusChip(
                            if (offlineCount > 0) "Не в сети" else "Все онлайн",
                            if (offlineCount > 0) offlineCount.toString() else onlineCount.toString(),
                            if (offlineCount > 0) Color(0xFFFF667A) else Color(0xFF41D69A),
                            Modifier.weight(1f)
                        )
                    }
                }
            }
        }
'''
text = text[:start] + summary + text[end:]

fav_start = '            if (favoriteDevices.isNotEmpty() && selectedCategory == "Все") {\n'
fav_end = '            item(span = { GridItemSpan(maxLineSpan) }, key = "devices_section_header") {\n'
start = text.find(fav_start)
end = text.find(fav_end, start)
if start < 0 or end <= start:
    raise SystemExit("Could not find favourites block")

favorites = '''            if (favoriteDevices.isNotEmpty() && selectedCategory == "Все") {
                item(span = { GridItemSpan(maxLineSpan) }, key = "favorites_shelf") {
                    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Text("Избранное", fontSize = 17.sp, fontWeight = FontWeight.Bold, modifier = Modifier.weight(1f))
                            Text("\${favoriteDevices.size}", color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.62f), fontSize = 11.sp)
                        }
                        Row(
                            Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()),
                            horizontalArrangement = Arrangement.spacedBy(9.dp)
                        ) {
                            favoriteDevices.forEach { device ->
                                Box(Modifier.width(cardWidthDp.dp), contentAlignment = Alignment.TopCenter) {
                                    CompactDeviceTile(
                                        device = device,
                                        enabled = !isBusy && device.id !in pendingDeviceIds,
                                        pending = device.id in pendingDeviceIds,
                                        cardSize = "small",
                                        cardWidthDp = cardWidthDp,
                                        cardHeightDp = cardHeightDp,
                                        onFavorite = { onFavoriteChange(device, it) },
                                        onOpen = { onOpenDevice(device) },
                                        onToggle = { onToggle(device, it) }
                                    )
                                }
                            }
                        }
                    }
                }
            }
'''
text = text[:start] + favorites + text[end:]

old_categories = '''                listOf("Все", "Проблемы", "Свет", "Розетки", "Климат", "Безопасность", "Датчики", "Другое").forEach { category ->
                    val count = when (category) {
                        "Все" -> devices.size
                        "Проблемы" -> offlineCount
                        "Свет" -> devices.count { dashboardDeviceCategory(it) == "Освещение" }
                        else -> devices.count { dashboardDeviceCategory(it) == category }
                    }
                    FilterChip(
                        selected = selectedCategory == category,
                        onClick = { selectedCategory = category },
                        label = { Text("$category · $count", fontSize = 10.sp, maxLines = 1) }
                    )
                }
'''
new_categories = '''                listOf("Все", "Не в сети", "Избранное", "Освещение", "Розетки", "Климат", "Безопасность", "Датчики", "Другое").forEach { category ->
                    val count = when (category) {
                        "Все" -> devices.size
                        "Не в сети" -> offlineCount
                        "Избранное" -> favoriteDevices.size
                        else -> devices.count { dashboardDeviceCategory(it) == category }
                    }
                    FilterChip(
                        selected = selectedCategory == category,
                        onClick = { selectedCategory = category },
                        label = { Text("$category · $count", fontSize = 10.sp, maxLines = 1) }
                    )
                }
'''
replace_once(old_categories, new_categories, "device category list")

tile_start = text.find("@Composable\nprivate fun CompactDeviceTile(")
tile_end = text.find("\nprivate fun deviceIcon(type:", tile_start)
if tile_start < 0 or tile_end < 0:
    raise SystemExit("Could not locate CompactDeviceTile")
tile = text[tile_start:tile_end]
old_layout = '''    BoxWithConstraints(
        modifier = Modifier.fillMaxWidth().height(cardHeightDp.dp)
'''
new_layout = '''    BoxWithConstraints(Modifier.fillMaxWidth(), contentAlignment = Alignment.TopCenter) {
    BoxWithConstraints(
        modifier = Modifier.widthIn(max = cardWidthDp.dp).fillMaxWidth().height(cardHeightDp.dp)
'''
if tile.count(old_layout) != 1:
    raise SystemExit(f"Expected one tile layout root; found {tile.count(old_layout)}")
tile = tile.replace(old_layout, new_layout, 1)
old_tail = '\n    }\n}'
if not tile.endswith(old_tail):
    raise SystemExit("Unexpected CompactDeviceTile closing structure")
tile = tile[:-len(old_tail)] + '\n    }\n    }\n}'
text = text[:tile_start] + tile + text[tile_end:]

quick_start = text.find("@Composable\nprivate fun HomeQuickButton(")
quick_end = text.find("\n@Composable\nprivate fun HistoryQuickButton(", quick_start)
if quick_start < 0 or quick_end < 0:
    raise SystemExit("Could not locate HomeQuickButton")

quick_button = '''@Composable
private fun HomeQuickButton(
    title: String,
    tint: Color,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    enabled: Boolean = true,
    refresh: Boolean = false
) {
    Row(
        modifier = modifier.height(42.dp)
            .clip(RoundedCornerShape(14.dp))
            .background(tint.copy(alpha = if (enabled) 0.16f else 0.07f))
            .border(1.dp, tint.copy(alpha = if (enabled) 0.28f else 0.12f), RoundedCornerShape(14.dp))
            .clickable(enabled = enabled, onClick = onClick)
            .padding(horizontal = 12.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.Center
    ) {
        Text(
            if (refresh) "↻" else title,
            color = tint.copy(alpha = if (enabled) 1f else 0.5f),
            fontSize = if (refresh) 20.sp else 11.sp,
            fontWeight = FontWeight.SemiBold,
            fontFamily = FontFamily.SansSerif,
            letterSpacing = 0.1.sp,
            maxLines = 1,
            overflow = TextOverflow.Ellipsis
        )
    }
}
'''
text = text[:quick_start] + quick_button + text[quick_end:]

if "private fun DashboardStatusChip(" not in text:
    marker = "\n@Composable\nprivate fun HistoryQuickButton("
    helper = '''
@Composable
private fun DashboardStatusChip(label: String, value: String, tint: Color, modifier: Modifier = Modifier) {
    Column(
        modifier = modifier
            .clip(RoundedCornerShape(13.dp))
            .background(Color.White.copy(alpha = 0.075f))
            .padding(horizontal = 9.dp, vertical = 8.dp),
        verticalArrangement = Arrangement.spacedBy(3.dp)
    ) {
        Text(value, color = tint, fontSize = 16.sp, fontWeight = FontWeight.Bold, maxLines = 1)
        Text(label, color = Color.White.copy(alpha = 0.78f), fontSize = 9.sp, maxLines = 1, overflow = TextOverflow.Ellipsis)
    }
}
'''
    if text.count(marker) != 1:
        raise SystemExit("Could not locate helper insertion point")
    text = text.replace(marker, helper + marker, 1)

source.write_text(text, encoding="utf-8")
subprocess.run([sys.executable, str(Path(__file__).with_name("apply_reference_ui_update_fix.py")), str(source.parents[7])], check=True)
print(f"Updated {source}")
