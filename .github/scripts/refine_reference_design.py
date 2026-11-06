#!/usr/bin/env python3
"""Apply the unified reference-inspired smart-home UI."""
from pathlib import Path
import sys

source = Path(sys.argv[1])
main = source.read_text(encoding="utf-8")
marker = "// REFERENCE-DESIGN-1.6.0"
if marker in main:
    print("Reference design already applied.")
    raise SystemExit(0)

# Shared dark visual system.
for old, new in [
    ("primary = Color(0xFFA78BFA).copy(alpha = 0.78f + glassOpacity * 0.20f),", "primary = Color(0xFF9565FF).copy(alpha = 0.88f + glassOpacity * 0.12f),"),
    ("background = Color(0xFF171922),", "background = Color(0xFF1B1D26),"),
    ("surface = Color(0xFF272B35).copy(alpha = glassOpacity),", "surface = Color(0xFF2D303A).copy(alpha = glassOpacity),"),
    ("surfaceVariant = Color(0xFF303642).copy(alpha = glassOpacity * 0.94f),", "surfaceVariant = Color(0xFF373A45).copy(alpha = glassOpacity * 0.96f),"),
    ("secondaryContainer = Color(0xFF173C49).copy(alpha = glassOpacity * 0.82f),", "secondaryContainer = Color(0xFF382B5D).copy(alpha = glassOpacity * 0.84f),"),
    ("colors = listOf(Color(0xFF1C1D25), Color(0xFF20212A), Color(0xFF191A22), Color(0xFF1C1D25)),", "colors = listOf(Color(0xFF191B23), Color(0xFF20222B), Color(0xFF1B1D26), Color(0xFF191B23)),"),
    ("medium = RoundedCornerShape(20.dp),\n            large = RoundedCornerShape(24.dp)", "medium = RoundedCornerShape(18.dp),\n            large = RoundedCornerShape(22.dp)"),
    ('AppPage.HOME -> "Мой дом"', 'AppPage.HOME -> "Дом"'),
]:
    if old not in main:
        raise SystemExit(f"Missing required UI anchor: {old}")
    main = main.replace(old, new, 1)

# Compact three-column room tiles on first launch; keep user customisations.
for old, new in [
    ('config.getInt("device_card_width_dp", 156).coerceIn(132, 260)', 'config.getInt("device_card_width_dp", 100).coerceIn(92, 260)'),
    ('config.getInt("device_card_height_dp", 188).coerceIn(148, 280)', 'config.getInt("device_card_height_dp", 136).coerceIn(112, 280)'),
    ('config.getInt("device_columns", 2).coerceIn(1, 3)', 'config.getInt("device_columns", 3).coerceIn(1, 3)'),
    ('deviceCardWidthDp = width.coerceIn(132, 260)', 'deviceCardWidthDp = width.coerceIn(92, 260)'),
    ('deviceCardHeightDp = height.coerceIn(148, 280)', 'deviceCardHeightDp = height.coerceIn(112, 280)'),
    ('val minimumCardWidth = maxOf(126, cardWidthDp).dp', 'val minimumCardWidth = maxOf(92, cardWidthDp).dp'),
    ('initialWidth.coerceIn(132, 260)', 'initialWidth.coerceIn(92, 260)'),
    ('initialHeight.coerceIn(148, 280)', 'initialHeight.coerceIn(112, 280)'),
    ('valueRange = 132f..260f', 'valueRange = 92f..260f'),
    ('valueRange = 148f..280f', 'valueRange = 112f..280f'),
    ('widthDp = 144f; heightDp = 164f', 'widthDp = 100f; heightDp = 128f'),
    ('widthDp = 156f; heightDp = 188f', 'widthDp = 136f; heightDp = 146f'),
    ('widthDp = 190f; heightDp = 232f', 'widthDp = 168f; heightDp = 178f'),
    ('"large" -> 68.dp; "small" -> 48.dp; else -> 58.dp', '"large" -> 54.dp; "small" -> 38.dp; else -> 46.dp'),
    ('"large" -> 48.dp; "small" -> 36.dp; else -> 42.dp', '"large" -> 42.dp; "small" -> 30.dp; else -> 34.dp'),
    ('cardHeightDp.coerceIn(148, 280).dp', 'cardHeightDp.coerceIn(112, 220).dp'),
]:
    if old not in main:
        raise SystemExit(f"Missing compact-layout anchor: {old}")
    main = main.replace(old, new, 1)

# Dashboard live summaries: useful at a glance without repeating device cards.
old_counts = '''    val activeCount = devices.count { it.isOnline && it.onOff == true }
    val onlineCount = devices.count { it.isOnline }
    val offlineCount = devices.size - onlineCount
    val favoriteDevices = remember(devices) { devices.filter { it.isFavorite } }
    val temperature = devices.flatMap { device -> device.properties.filter { it.instance == "temperature" }.mapNotNull { (it.value as? Number)?.toDouble() } }.takeIf { it.isNotEmpty() }?.average()
    val humidity = devices.flatMap { device -> device.properties.filter { it.instance == "humidity" }.mapNotNull { (it.value as? Number)?.toDouble() } }.takeIf { it.isNotEmpty() }?.average()
    val currentPower = devices.flatMap { device -> device.properties.filter { it.instance == "power" }.mapNotNull { (it.value as? Number)?.toDouble() } }.takeIf { it.isNotEmpty() }?.sum()
'''
new_counts = '''    val onlineCount = devices.count { it.isOnline }
    val offlineCount = devices.size - onlineCount
    val favoriteDevices = remember(devices) { devices.filter { it.isFavorite } }
    val lightDevices = remember(devices) { devices.filter { dashboardDeviceCategory(it) == "Освещение" } }
    val socketDevices = remember(devices) { devices.filter { dashboardDeviceCategory(it) == "Розетки" } }
    val activeLights = lightDevices.count { it.isOnline && it.onOff == true }
    val activeSockets = socketDevices.count { it.isOnline && it.onOff == true }
'''
if main.count(old_counts) != 1:
    raise SystemExit("Could not locate dashboard summary values")
main = main.replace(old_counts, new_counts, 1)

hero_start = '        item(span = { GridItemSpan(maxLineSpan) }, key = "dashboard_hero") {\n'
weather_start = '        item(span = { GridItemSpan(maxLineSpan) }, key = "location_weather") {\n'
start = main.find(hero_start)
end = main.find(weather_start, start)
if start < 0 or end <= start:
    raise SystemExit("Could not locate dashboard hero")
hero = '''        item(span = { GridItemSpan(maxLineSpan) }, key = "dashboard_hero") {
            Column(Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(9.dp)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(2.dp)) {
                        Text("ДОМ", color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.56f), fontSize = 9.sp, fontWeight = FontWeight.Bold, letterSpacing = 1.3.sp)
                        Text(
                            when {
                                devices.isEmpty() -> "Подключи свой дом"
                                offlineCount > 0 -> "Есть проблемы со связью"
                                else -> "Всё под контролем"
                            },
                            color = MaterialTheme.colorScheme.onSurface, fontSize = 19.sp, fontWeight = FontWeight.Bold,
                            maxLines = 1, overflow = TextOverflow.Ellipsis
                        )
                    }
                    Text("${devices.size} устройств", color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.58f), fontSize = 11.sp)
                }
                Row(Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    HomeStatusChip(if (offlineCount > 0) "×" else "✓", if (offlineCount > 0) "Не в сети" else "В сети", if (offlineCount > 0) "\$offlineCount устройств" else "Все подключены", if (offlineCount > 0) Color(0xFFFF6477) else Color(0xFF57D4A5))
                    HomeStatusChip("☼", "Свет", "\$activeLights из ${lightDevices.size} вкл.", Color(0xFFAA83FF))
                    HomeStatusChip("●", "Розетки", "\$activeSockets из ${socketDevices.size} вкл.", Color(0xFF8E72EF))
                }
            }
        }
'''
# Undo JS template escapes so the Python file receives Kotlin interpolation literally.
hero = hero.replace("\\$", "$")
main = main[:start] + hero + main[end:]

# Make the location/weather panel match the graphite surfaces.
main = main.replace(
    'colors = listOf(Color(0xFF13263B), Color(0xFF164252), Color(0xFF1A3045)),',
    'colors = listOf(Color(0xFF343044), Color(0xFF2B3746), Color(0xFF27333D)),',
    1,
)

# Functional search by device name, room and type.
old_filter = '''    var selectedCategory by remember { mutableStateOf("Все") }
    val visibleDevices = remember(devices, selectedCategory) {
        when (selectedCategory) {
            "Все" -> devices
            "Не в сети" -> devices.filterNot { it.isOnline }
            "Избранное" -> devices.filter { it.isFavorite }
            "Свет", "Освещение" -> devices.filter { dashboardDeviceCategory(it) == "Освещение" }
            else -> devices.filter { dashboardDeviceCategory(it) == selectedCategory }
        }
    }
'''
new_filter = '''    var selectedCategory by remember { mutableStateOf("Все") }
    var deviceSearch by remember { mutableStateOf("") }
    val visibleDevices = remember(devices, selectedCategory, deviceSearch) {
        val byCategory = when (selectedCategory) {
            "Все" -> devices
            "Не в сети" -> devices.filterNot { it.isOnline }
            "Избранное" -> devices.filter { it.isFavorite }
            "Свет", "Освещение" -> devices.filter { dashboardDeviceCategory(it) == "Освещение" }
            else -> devices.filter { dashboardDeviceCategory(it) == selectedCategory }
        }
        val query = deviceSearch.trim()
        if (query.isBlank()) byCategory else byCategory.filter { device ->
            device.name.contains(query, ignoreCase = true) || device.room.contains(query, ignoreCase = true) || device.type.contains(query, ignoreCase = true)
        }
    }
'''
if main.count(old_filter) != 1:
    raise SystemExit("Could not locate device filter")
main = main.replace(old_filter, new_filter, 1)
search_anchor = '        item(span = { GridItemSpan(maxLineSpan) }, key = "device_categories") {\n'
if main.count(search_anchor) != 1:
    raise SystemExit("Could not locate device categories")
main = main.replace(search_anchor, '''        item(span = { GridItemSpan(maxLineSpan) }, key = "device_search") {
            OutlinedTextField(
                value = deviceSearch,
                onValueChange = { deviceSearch = it.take(64) },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
                label = { Text("Найти устройство или комнату") },
                shape = RoundedCornerShape(17.dp)
            )
        }
''' + search_anchor, 1)

# Better chip proportions.
main = main.replace(
    '.height(60.dp)\n            .clip(RoundedCornerShape(19.dp))\n            .background(Color(0xFF30323B))',
    '.widthIn(min = 116.dp)\n            .height(60.dp)\n            .clip(RoundedCornerShape(18.dp))\n            .background(Brush.linearGradient(listOf(Color(0xFF343742), Color(0xFF2C303A))))',
    1,
)

# Bottom dock: Home, Groups, Scenarios and Analytics. History remains available from the clock action.
main = main.replace(
    'page in setOf(AppPage.HOME, AppPage.SCENARIOS, AppPage.HISTORY, AppPage.DEVICE, AppPage.GROUP_DETAILS, AppPage.ANALYTICS)',
    'page in setOf(AppPage.HOME, AppPage.SCENARIOS, AppPage.HISTORY, AppPage.DEVICE, AppPage.GROUPS, AppPage.GROUP_DETAILS, AppPage.ANALYTICS)',
    1,
)
main = main.replace(
    'selected = page in setOf(AppPage.HOME, AppPage.DEVICE, AppPage.GROUP_DETAILS, AppPage.ANALYTICS),',
    'selected = page in setOf(AppPage.HOME, AppPage.DEVICE, AppPage.GROUP_DETAILS, AppPage.HISTORY),',
    1,
)
main = main.replace('label = { Text("Главная") },', 'label = { Text("Дом", maxLines = 1) },', 1)
old_scenarios_nav = '''                        NavigationBarItem(
                            selected = page == AppPage.SCENARIOS,
'''
groups_nav = '''                        NavigationBarItem(
                            selected = page == AppPage.GROUPS,
                            onClick = { page = AppPage.GROUPS },
                            icon = { SmartGlyph("grid", Modifier.size(21.dp), Color.White.copy(alpha = if (page == AppPage.GROUPS) 1f else 0.62f)) },
                            label = { Text("Группы", maxLines = 1) },
                            colors = NavigationBarItemDefaults.colors(selectedIconColor = Color.White, selectedTextColor = Color.White, unselectedIconColor = Color.White.copy(alpha = 0.62f), unselectedTextColor = Color.White.copy(alpha = 0.62f), indicatorColor = Color(0xFF7952D7).copy(alpha = 0.42f))
                        )
                        NavigationBarItem(
                            selected = page == AppPage.SCENARIOS,
'''
if main.count(old_scenarios_nav) != 1:
    raise SystemExit("Could not insert Groups tab")
main = main.replace(old_scenarios_nav, groups_nav, 1)
main = main.replace('''                            icon = { SmartGlyph("sparkles", Modifier.size(22.dp), Color.White.copy(alpha = if (page == AppPage.SCENARIOS) 1f else 0.72f)) }, label = { Text("Сценарии") },''', '''                            icon = { SmartGlyph("sparkles", Modifier.size(21.dp), Color.White.copy(alpha = if (page == AppPage.SCENARIOS) 1f else 0.62f)) }, label = { Text("Сценарии", maxLines = 1) },''', 1)
old_history_nav = '''                        NavigationBarItem(
                            selected = page == AppPage.HISTORY,
                            onClick = { history = HomeHistoryStore.load(context); page = AppPage.HISTORY },
                            icon = { SmartGlyph("clock", Modifier.size(22.dp), Color.White.copy(alpha = if (page == AppPage.HISTORY) 1f else 0.72f)) },
                            label = { Text("История") },
                            colors = NavigationBarItemDefaults.colors(selectedIconColor = Color.White, selectedTextColor = Color.White, unselectedIconColor = Color.White.copy(alpha = 0.72f), unselectedTextColor = Color.White.copy(alpha = 0.72f), indicatorColor = Color.White.copy(alpha = 0.14f))
                        )
'''
new_analytics_nav = '''                        NavigationBarItem(
                            selected = page == AppPage.ANALYTICS,
                            onClick = { page = AppPage.ANALYTICS },
                            icon = { SmartGlyph("chart", Modifier.size(21.dp), Color.White.copy(alpha = if (page == AppPage.ANALYTICS) 1f else 0.62f)) },
                            label = { Text("Аналитика", maxLines = 1) },
                            colors = NavigationBarItemDefaults.colors(selectedIconColor = Color.White, selectedTextColor = Color.White, unselectedIconColor = Color.White.copy(alpha = 0.62f), unselectedTextColor = Color.White.copy(alpha = 0.62f), indicatorColor = Color(0xFF7952D7).copy(alpha = 0.42f))
                        )
'''
if main.count(old_history_nav) != 1:
    raise SystemExit("Could not replace History tab with Analytics")
main = main.replace(old_history_nav, new_analytics_nav, 1)

main = main.rstrip() + "\n\n" + marker + "\n"
source.write_text(main, encoding="utf-8")
print("Applied graphite theme, status tiles, search, three-column device cards and four-tab navigation.")
