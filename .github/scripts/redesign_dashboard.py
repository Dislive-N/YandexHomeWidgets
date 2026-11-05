#!/usr/bin/env python3
"""Refresh the Yandex Home dashboard layout while preserving device controls."""
from pathlib import Path
import sys

source = Path(sys.argv[1])
text = source.read_text(encoding="utf-8")
if 'Text("СОСТОЯНИЕ ДОМА"' in text:
    print("Dashboard already redesigned; leaving source unchanged.")
    raise SystemExit(0)

replacements = [
    ('AppPage.HOME -> "Яндекс Дом"', 'AppPage.HOME -> "Мой дом"', "home header title"),
    (
        'modifier = Modifier.fillMaxWidth().padding(horizontal = 18.dp, vertical = 12.dp),',
        'modifier = Modifier.fillMaxWidth().padding(horizontal = 18.dp, vertical = 7.dp),',
        "header vertical spacing",
    ),
    (
        '}, fontSize = 25.sp, fontWeight = FontWeight.Bold\n                        )',
        '}, fontSize = if (page == AppPage.HOME) 22.sp else 23.sp, fontWeight = FontWeight.Bold\n                        )',
        "header title scale",
    ),
]
for old, new, name in replacements:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"Expected one occurrence for {name}, found {count}")
    text = text.replace(old, new, 1)

old = '''    val visibleDevices = remember(devices, selectedCategory) {
        if (selectedCategory == "Все") devices else devices.filter { dashboardDeviceCategory(it) == selectedCategory }
    }
'''
new = '''    val visibleDevices = remember(devices, selectedCategory) {
        when (selectedCategory) {
            "Все" -> devices
            "Не в сети" -> devices.filterNot { it.isOnline }
            "Избранное" -> devices.filter { it.isFavorite }
            else -> devices.filter { dashboardDeviceCategory(it) == selectedCategory }
        }
    }
'''
if text.count(old) != 1:
    raise SystemExit("Could not find the device category filter block")
text = text.replace(old, new, 1)

old = '''    val activeCount = devices.count { it.onOff == true }
    val temperature = devices.flatMap { device -> device.properties.filter { it.instance == "temperature" }.mapNotNull { (it.value as? Number)?.toDouble() } }.takeIf { it.isNotEmpty() }?.average()
'''
new = '''    val activeCount = devices.count { it.onOff == true }
    val onlineCount = devices.count { it.isOnline }
    val offlineCount = devices.size - onlineCount
    val favoriteDevices = remember(devices) { devices.filter { it.isFavorite } }
    val temperature = devices.flatMap { device -> device.properties.filter { it.instance == "temperature" }.mapNotNull { (it.value as? Number)?.toDouble() } }.takeIf { it.isNotEmpty() }?.average()
'''
if text.count(old) != 1:
    raise SystemExit("Could not find dashboard metrics block")
text = text.replace(old, new, 1)

start_marker = '        item(span = { GridItemSpan(maxLineSpan) }, key = "dashboard_summary") {\n'
end_marker = '        item(span = { GridItemSpan(maxLineSpan) }, key = "location_weather") {\n'
start = text.find(start_marker)
end = text.find(end_marker, start)
if start < 0 or end < 0 or end <= start:
    raise SystemExit("Could not locate dashboard summary section")

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
                                if (offlineCount > 0) "Проверь соединение" else "Всё под контролем",
                                color = Color.White,
                                fontSize = 20.sp,
                                fontWeight = FontWeight.Bold
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
                            if (offlineCount > 0) "Не в сети" else "Без ошибок",
                            if (offlineCount > 0) offlineCount.toString() else "OK",
                            if (offlineCount > 0) Color(0xFFFF667A) else Color(0xFF41D69A),
                            Modifier.weight(1f)
                        )
                    }
                }
            }
        }
'''
text = text[:start] + summary + text[end:]

marker = '        item(span = { GridItemSpan(maxLineSpan) }, key = "device_categories") {\n'
favorites = '''        if (selectedCategory == "Все" && favoriteDevices.isNotEmpty()) {
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
                            Box(Modifier.width(184.dp)) {
                                CompactDeviceTile(
                                    device = device,
                                    enabled = !isBusy && device.id !in pendingDeviceIds,
                                    pending = device.id in pendingDeviceIds,
                                    cardSize = "small",
                                    cardWidthDp = 184,
                                    cardHeightDp = 156,
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
        item(span = { GridItemSpan(maxLineSpan) }, key = "device_categories") {
'''
if text.count(marker) != 1:
    raise SystemExit("Could not locate category row")
text = text.replace(marker, favorites, 1)

old = '''                listOf("Все", "Освещение", "Розетки", "Климат", "Безопасность", "Датчики", "Другое").forEach { category ->
                    FilterChip(selected = selectedCategory == category, onClick = { selectedCategory = category }, label = { Text(category, fontSize = 10.sp) })
                }
'''
new = '''                listOf("Все", "Не в сети", "Избранное", "Освещение", "Розетки", "Климат", "Безопасность", "Датчики", "Другое").forEach { category ->
                    val categoryCount = when (category) {
                        "Не в сети" -> offlineCount
                        "Избранное" -> favoriteDevices.size
                        else -> null
                    }
                    FilterChip(
                        selected = selectedCategory == category,
                        onClick = { selectedCategory = category },
                        label = { Text(if (categoryCount != null) "$category · $categoryCount" else category, fontSize = 10.sp) }
                    )
                }
'''
if text.count(old) != 1:
    raise SystemExit("Could not find category chip list")
text = text.replace(old, new, 1)

old = '''        if (visibleDevices.isEmpty()) {
            item(span = { GridItemSpan(maxLineSpan) }, key = "empty_devices") {
'''
new = '''        item(span = { GridItemSpan(maxLineSpan) }, key = "devices_section_title") {
            Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.padding(top = 2.dp, bottom = 1.dp)) {
                Text(if (selectedCategory == "Все") "Устройства" else selectedCategory, fontSize = 17.sp, fontWeight = FontWeight.Bold, modifier = Modifier.weight(1f))
                Text("\${visibleDevices.size}", color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.62f), fontSize = 11.sp)
            }
        }
        if (visibleDevices.isEmpty()) {
            item(span = { GridItemSpan(maxLineSpan) }, key = "empty_devices") {
'''
if text.count(old) != 1:
    raise SystemExit("Could not find empty devices branch")
text = text.replace(old, new, 1)

old = '''@Composable
private fun HomeQuickButton(
    title: String,
    tint: Color,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    enabled: Boolean = true,
    refresh: Boolean = false
) {
    Button(
        onClick = onClick,
        enabled = enabled,
        modifier = modifier.height(44.dp),
        shape = RoundedCornerShape(14.dp),
        contentPadding = PaddingValues(horizontal = 3.dp, vertical = 3.dp),
        colors = ButtonDefaults.buttonColors(containerColor = tint, contentColor = Color.White, disabledContainerColor = tint.copy(alpha = 0.45f))
    ) {
        Text(if (refresh) "↻" else title, fontSize = if (refresh) 20.sp else 10.sp,
            fontWeight = FontWeight.Bold, fontFamily = FontFamily.SansSerif, letterSpacing = 0.15.sp,
            maxLines = 1, overflow = TextOverflow.Ellipsis)
    }
}
'''
new = '''@Composable
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
        Text(if (refresh) "↻" else title, color = tint.copy(alpha = if (enabled) 1f else 0.5f), fontSize = if (refresh) 20.sp else 11.sp,
            fontWeight = FontWeight.SemiBold, fontFamily = FontFamily.SansSerif, letterSpacing = 0.1.sp,
            maxLines = 1, overflow = TextOverflow.Ellipsis)
    }
}

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
if text.count(old) != 1:
    raise SystemExit("Could not find HomeQuickButton implementation")
text = text.replace(old, new, 1)

source.write_text(text, encoding="utf-8")
print(f"Updated {source}")
