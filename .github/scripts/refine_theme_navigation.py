#!/usr/bin/env python3
"""Complete the reference-style dual-theme navigation and screen set."""
from pathlib import Path
import sys

source = Path(sys.argv[1])
text = source.read_text(encoding="utf-8")
MARKER = "// THEME-NAV-1.8.0"
if MARKER in text:
    print("Theme/navigation refinement already applied.")
    raise SystemExit(0)

def replace_once(old: str, new: str, label: str):
    global text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one anchor, found {count}")
    text = text.replace(old, new, 1)

def replace_function(name: str, next_name: str, body: str, annotate_next: bool = True):
    global text
    start_token = f"private fun {name}("
    end_token = f"private fun {next_name}("
    af = text.find(start_token)
    bf = text.find(end_token, af + len(start_token))
    if af < 0 or bf < 0:
        raise SystemExit(f"Could not locate {name} -> {next_name}")
    a = text.rfind("@Composable", 0, af) if "@Composable" in text[max(0, af - 24):af] else af
    ba = text.rfind("@Composable", 0, bf)
    b = ba if annotate_next and ba > af and text[ba:bf].strip() == "@Composable" else bf
    text = text[:a] + body.rstrip() + "\n\n" + text[b:]

# New routes are separate views; existing detailed screens remain reachable.
replace_once(
    "private enum class AppPage { HOME, SCENARIOS, HISTORY, ANALYTICS, SETTINGS, DEVICE, GROUPS, GROUP_DETAILS }",
    "private enum class AppPage { HOME, DEVICES, SCENARIOS, AUTOMATIONS, PROFILE, HISTORY, ANALYTICS, SETTINGS, DEVICE, GROUPS, GROUP_DETAILS }",
    "AppPage enum"
)

# Poll only the visible smart-home sections, not profile/settings.
replace_once(
    "page in setOf(AppPage.HOME, AppPage.SCENARIOS, AppPage.DEVICE, AppPage.GROUP_DETAILS, AppPage.ANALYTICS)",
    "page in setOf(AppPage.HOME, AppPage.DEVICES, AppPage.SCENARIOS, AppPage.AUTOMATIONS, AppPage.DEVICE, AppPage.GROUP_DETAILS, AppPage.ANALYTICS)",
    "Visible screen polling"
)

# A true Material theme for both palettes. All theme-aware surfaces derive from these tokens.
theme_start = "    val colors = if (isDarkTheme) darkColorScheme("
theme_end = "\n\n    MaterialTheme("
a = text.find(theme_start)
b = text.find(theme_end, a)
if a < 0 or b < 0:
    raise SystemExit("Could not find Material color scheme block")
theme_block = '''    val colors = if (isDarkTheme) darkColorScheme(
        primary = Color(0xFFA98BFF),
        onPrimary = Color.White,
        primaryContainer = Color(0xFF43336A),
        onPrimaryContainer = Color(0xFFE9DEFF),
        secondary = Color(0xFF61D6B8),
        onSecondary = Color(0xFF073B31),
        secondaryContainer = Color(0xFF194A43),
        onSecondaryContainer = Color(0xFFB9F3E4),
        tertiary = Color(0xFF83BDF3),
        background = Color(0xFF101525),
        surface = Color(0xFF1D2538).copy(alpha = glassOpacity),
        surfaceVariant = Color(0xFF29334A).copy(alpha = glassOpacity * 0.98f),
        onSurface = Color(0xFFF2F4FC),
        onSurfaceVariant = Color(0xFFB4BDD0),
        onBackground = Color(0xFFF2F4FC),
        outline = Color(0xFF56617A),
        outlineVariant = Color(0xFF3A455D),
        error = Color(0xFFFF7185),
        errorContainer = Color(0xFF512B39),
        onErrorContainer = Color(0xFFFFDCE2)
    ) else lightColorScheme(
        primary = Color(0xFF7553D1),
        onPrimary = Color.White,
        primaryContainer = Color(0xFFE9E0FF),
        onPrimaryContainer = Color(0xFF35205F),
        secondary = Color(0xFF158F82),
        onSecondary = Color.White,
        secondaryContainer = Color(0xFFD7F2EB),
        onSecondaryContainer = Color(0xFF154E45),
        tertiary = Color(0xFF397FC0),
        background = Color(0xFFF4F3FA),
        surface = Color(0xFFFCFCFF).copy(alpha = glassOpacity),
        surfaceVariant = Color(0xFFECECF5).copy(alpha = glassOpacity),
        onSurface = Color(0xFF172039),
        onSurfaceVariant = Color(0xFF5C657A),
        onBackground = Color(0xFF172039),
        outline = Color(0xFFD0D3E1),
        outlineVariant = Color(0xFFE2E3EC),
        error = Color(0xFFBD3850),
        errorContainer = Color(0xFFFFE7EC),
        onErrorContainer = Color(0xFF7C182D)
    )'''
text = text[:a] + theme_block + text[b:]

# Theme-aware root canvas: no dark-violet tint leaks into the light theme.
replace_once(
    "colors = listOf(Color(0xFF191B23), Color(0xFF20222B), Color(0xFF1B1D26), Color(0xFF191B23)),",
    "colors = listOf(Color(0xFF0E1424), Color(0xFF172238), Color(0xFF171C2C), Color(0xFF101525)),",
    "Dark root background"
)
replace_once(
    "colors = listOf(Color(0xFFF5EFFD), Color(0xFFEAF4FA), Color(0xFFF7F0FB)),",
    "colors = listOf(Color(0xFFF6F4FC), Color(0xFFEEF3FA), Color(0xFFF8F1FB)),",
    "Light root background"
)
replace_once(
    "if (isDarkTheme) {\n                        drawCircle(",
    "if (isDarkTheme) {\n                        drawCircle(",
    "Root background glow anchor"
)

# Main header labels for new sections.
replace_once(
    '''                                AppPage.HOME -> "Дом"
                                AppPage.SCENARIOS -> "Сценарии"''',
    '''                                AppPage.HOME -> "Главная"
                                AppPage.DEVICES -> "Устройства"
                                AppPage.SCENARIOS -> "Сценарии"
                                AppPage.AUTOMATIONS -> "Автоматизации"
                                AppPage.PROFILE -> "Профиль"''',
    "Header route labels"
)

# Top bar: home/devices get refresh + history + profile; secondary screens get back.
replace_once(
    "if (isConnected && page == AppPage.HOME) {",
    "if (isConnected && page in setOf(AppPage.HOME, AppPage.DEVICES)) {",
    "Home/device top bar"
)
replace_once(
    '''                        TextButton(onClick = { page = AppPage.SETTINGS }, contentPadding = PaddingValues(horizontal = 4.dp, vertical = 4.dp)) { Text("⚙", fontSize = 20.sp, color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.86f)) }
                    } else if (page == AppPage.SCENARIOS) {
                        TextButton(onClick = { page = AppPage.SETTINGS }) { Text("⚙", fontSize = 20.sp, color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.86f)) }
                    } else {''',
    '''                        TextButton(onClick = { page = AppPage.PROFILE }, contentPadding = PaddingValues(horizontal = 4.dp, vertical = 4.dp)) { SmartGlyph("user", Modifier.size(21.dp), MaterialTheme.colorScheme.primary) }
                    } else if (page in setOf(AppPage.SCENARIOS, AppPage.AUTOMATIONS, AppPage.PROFILE)) {
                        if (page != AppPage.PROFILE) TextButton(onClick = { page = AppPage.PROFILE }) { SmartGlyph("user", Modifier.size(21.dp), MaterialTheme.colorScheme.primary) }
                        else TextButton(onClick = { page = AppPage.SETTINGS }) { SmartGlyph("settings", Modifier.size(21.dp), MaterialTheme.colorScheme.primary) }
                    } else {''',
    "Secondary header actions"
)

# Extend the HomeScreen signature with navigation callbacks.
replace_once(
    '''    onAnalytics: () -> Unit,
    onOpenGroups: () -> Unit,
    onOpenGroup: (DeviceGroup) -> Unit,''',
    '''    onAnalytics: () -> Unit,
    onOpenGroups: () -> Unit,
    onOpenDevices: () -> Unit,
    onOpenScenarios: () -> Unit,
    onOpenAutomations: () -> Unit,
    onOpenGroup: (DeviceGroup) -> Unit,''',
    "Home screen navigation callbacks"
)

# Add the new independent Devices screen.
devices_screen = r'''@Composable
private fun DevicesScreen(
    devices: List<HomeDevice>,
    pendingDeviceIds: Set<String>,
    isBusy: Boolean,
    cardSize: String,
    cardWidthDp: Int,
    cardHeightDp: Int,
    deviceColumns: Int,
    onOpenDevice: (HomeDevice) -> Unit,
    onFavoriteChange: (HomeDevice, Boolean) -> Unit,
    onToggle: (HomeDevice, Boolean) -> Unit
) {
    var query by remember { mutableStateOf("") }
    var category by remember { mutableStateOf("Все") }
    val counts = remember(devices) {
        mapOf(
            "Все" to devices.size,
            "Проблемы" to devices.count(::deviceNeedsAttention),
            "Свет" to devices.count { dashboardDeviceCategory(it) == "Освещение" },
            "Розетки" to devices.count { dashboardDeviceCategory(it) == "Розетки" },
            "Датчики" to devices.count { dashboardDeviceCategory(it) == "Датчики" },
            "Медиа" to devices.count { dashboardDeviceCategory(it) == "Медиа" },
            "Избранное" to devices.count { it.isFavorite }
        )
    }
    val filtered = remember(devices, query, category) {
        val base = when (category) {
            "Проблемы" -> devices.filter(::deviceNeedsAttention)
            "Свет" -> devices.filter { dashboardDeviceCategory(it) == "Освещение" }
            "Розетки", "Датчики", "Медиа" -> devices.filter { dashboardDeviceCategory(it) == category }
            "Избранное" -> devices.filter { it.isFavorite }
            else -> devices
        }
        if (query.isBlank()) base else base.filter {
            it.name.contains(query, true) || it.room.contains(query, true) || it.type.contains(query, true)
        }
    }
    LazyVerticalGrid(
        columns = GridCells.Fixed(deviceColumns.coerceIn(1, 3)),
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(horizontal = 14.dp, vertical = 12.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp),
        horizontalArrangement = Arrangement.spacedBy(10.dp)
    ) {
        item(span = { GridItemSpan(maxLineSpan) }, key = "devices_intro") {
            Column(verticalArrangement = Arrangement.spacedBy(9.dp)) {
                Row(verticalAlignment = Alignment.Bottom) {
                    Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(2.dp)) {
                        Text("ВСЕ ПОДКЛЮЧЕНИЯ", color = MaterialTheme.colorScheme.onSurfaceVariant, fontSize = 9.sp, fontWeight = FontWeight.Bold, letterSpacing = 1.1.sp)
                        Text("Устройства", fontSize = 20.sp, fontWeight = FontWeight.Bold)
                    }
                    Text("[0m${devices.size} всего", fontSize = 11.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
                OutlinedTextField(
                    value = query,
                    onValueChange = { query = it.take(64) },
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true,
                    label = { Text("Поиск по названию или комнате") },
                    shape = RoundedCornerShape(17.dp)
                )
                Row(Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(7.dp)) {
                    listOf("Все", "Проблемы", "Свет", "Розетки", "Датчики", "Медиа", "Избранное").forEach { item ->
                        FilterChip(
                            selected = category == item,
                            onClick = { category = item },
                            label = { Text("$item · ${counts[item] ?: 0}", fontSize = 10.sp, maxLines = 1) }
                        )
                    }
                }
            }
        }
        if (filtered.isEmpty()) {
            item(span = { GridItemSpan(maxLineSpan) }, key = "devices_empty") {
                EmptyCard(if (query.isNotBlank()) "По запросу ничего не найдено." else "В этой категории пока нет устройств.")
            }
        } else {
            gridItems(filtered, key = { it.id }) { device ->
                CompactDeviceTile(
                    device = device,
                    enabled = !isBusy && device.isOnline,
                    pending = device.id in pendingDeviceIds,
                    cardSize = cardSize,
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

'''
replace_once("@Composable\nprivate fun HomeScreen(", devices_screen + "@Composable\nprivate fun HomeScreen(", "Devices screen insertion")

# Home quick actions become useful entry points; no old functions are removed.
replace_once(
    '''                HomeQuickButton("Группы", Color(0xFF9B7BFA), onOpenGroups, Modifier.widthIn(min = 112.dp))
                HomeQuickButton("Аналитика", Color(0xFF52C9B0), onAnalytics, Modifier.widthIn(min = 112.dp))''',
    '''                HomeQuickButton("Устройства", MaterialTheme.colorScheme.primary, onOpenDevices, Modifier.widthIn(min = 112.dp))
                HomeQuickButton("Группы", MaterialTheme.colorScheme.secondary, onOpenGroups, Modifier.widthIn(min = 112.dp))
                HomeQuickButton("Сценарии", MaterialTheme.colorScheme.tertiary, onOpenScenarios, Modifier.widthIn(min = 112.dp))
                HomeQuickButton("Автоматизации", MaterialTheme.colorScheme.primary, onOpenAutomations, Modifier.widthIn(min = 130.dp))
                HomeQuickButton("Датчики", MaterialTheme.colorScheme.secondary, onAnalytics, Modifier.widthIn(min = 112.dp))''',
    "Home quick action links"
)

# Split Yandex scenarios and user automations into their own tabs without deleting either.
replace_once(
    '''                            AppPage.SCENARIOS -> ScenarioCenterScreen(''',
    '''                            AppPage.SCENARIOS -> ScenariosScreen(
                                scenarios = scenarios,
                                isBusy = isBusy,
                                onRun = { scenario -> if (!isBusy) performDeviceAction { it.runScenario(scenario.id) } }
                            )
                            AppPage.AUTOMATIONS -> ScenarioCenterScreen(''',
    "Scenario/automation route split"
)

# Add Devices and Profile route branches to the main dispatcher.
devices_branch = '''                            AppPage.DEVICES -> DevicesScreen(
                                devices = devices,
                                pendingDeviceIds = pendingDeviceIds,
                                isBusy = isBusy,
                                cardSize = deviceCardSize,
                                cardWidthDp = deviceCardWidthDp,
                                cardHeightDp = deviceCardHeightDp,
                                deviceColumns = deviceColumns,
                                onOpenDevice = { selectedDeviceId = it.id; page = AppPage.DEVICE },
                                onFavoriteChange = { device, favorite ->
                                    HomeCache.setFavorite(context, device.id, favorite)
                                    devices = devices.map { if (it.id == device.id) it.copy(isFavorite = favorite) else it }
                                    scope.launch { HomeWidget().updateAll(context) }
                                },
                                onToggle = { device, value -> if (!isBusy) performOnOff(listOf(device.id), value) }
                            )
'''
replace_once("                            AppPage.DEVICE -> {", devices_branch + "                            AppPage.DEVICE -> {", "Devices route branch")

profile_screen = r'''@Composable
private fun ProfileScreen(
    isConnected: Boolean,
    deviceCount: Int,
    roomCount: Int,
    onOpenSettings: () -> Unit,
    onOpenGroups: () -> Unit,
    onOpenHistory: () -> Unit,
    onOpenAnalytics: () -> Unit
) {
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(horizontal = 15.dp, vertical = 12.dp), verticalArrangement = Arrangement.spacedBy(11.dp)) {
        Card(shape = RoundedCornerShape(24.dp), colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)) {
            Row(Modifier.fillMaxWidth().padding(17.dp), verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(13.dp)) {
                Box(Modifier.size(58.dp).clip(CircleShape).background(MaterialTheme.colorScheme.primaryContainer), contentAlignment = Alignment.Center) {
                    SmartGlyph("user", Modifier.size(30.dp), MaterialTheme.colorScheme.primary)
                }
                Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(3.dp)) {
                    Text("Мой профиль", fontSize = 18.sp, fontWeight = FontWeight.Bold)
                    Text("Личный центр управления домом", fontSize = 11.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    Text(if (isConnected) "Яндекс подключён" else "Яндекс не подключён", fontSize = 10.sp, color = if (isConnected) MaterialTheme.colorScheme.secondary else MaterialTheme.colorScheme.error)
                }
                SmartGlyph("settings", Modifier.size(23.dp), MaterialTheme.colorScheme.primary)
            }
        }
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(9.dp)) {
            AnalyticsMetric("Устройства", deviceCount.toString(), MaterialTheme.colorScheme.primary, Modifier.weight(1f))
            AnalyticsMetric("Комнаты", roomCount.toString(), MaterialTheme.colorScheme.secondary, Modifier.weight(1f))
        }
        Text("УПРАВЛЕНИЕ", color = MaterialTheme.colorScheme.onSurfaceVariant, fontSize = 9.sp, fontWeight = FontWeight.Bold, letterSpacing = 1.2.sp, modifier = Modifier.padding(top = 5.dp))
        ProfileActionRow("Мой дом и комнаты", "Группы, помещения и устройства", "house", onOpenGroups)
        ProfileActionRow("История изменений", "Все последние события дома", "clock", onOpenHistory)
        ProfileActionRow("Датчики и аналитика", "Графики, показатели и предупреждения", "chart", onOpenAnalytics)
        ProfileActionRow("Настройки приложения", "Тема, карточки, погода и обновления", "settings", onOpenSettings)
        Card(shape = RoundedCornerShape(18.dp), colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)) {
            Column(Modifier.fillMaxWidth().padding(14.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                Text("Виджеты и автоматизации", fontWeight = FontWeight.SemiBold, fontSize = 13.sp)
                Text("Настраивай виджеты на рабочем столе и автоматические действия во вкладке «Автоматизации».", fontSize = 11.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
        }
    }
}

@Composable
private fun ProfileActionRow(title: String, description: String, glyph: String, onClick: () -> Unit) {
    Row(
        Modifier.fillMaxWidth().clip(RoundedCornerShape(17.dp)).background(MaterialTheme.colorScheme.surface)
            .border(1.dp, MaterialTheme.colorScheme.outlineVariant.copy(alpha = 0.65f), RoundedCornerShape(17.dp))
            .clickable(onClick = onClick).padding(horizontal = 13.dp, vertical = 12.dp),
        verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(11.dp)
    ) {
        Box(Modifier.size(38.dp).clip(RoundedCornerShape(12.dp)).background(MaterialTheme.colorScheme.primaryContainer), contentAlignment = Alignment.Center) {
            SmartGlyph(glyph, Modifier.size(21.dp), MaterialTheme.colorScheme.primary)
        }
        Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(2.dp)) {
            Text(title, fontSize = 12.sp, fontWeight = FontWeight.SemiBold)
            Text(description, fontSize = 10.sp, color = MaterialTheme.colorScheme.onSurfaceVariant, maxLines = 2, overflow = TextOverflow.Ellipsis)
        }
        Text("›", fontSize = 23.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
    }
}

'''
replace_once("@Composable\nprivate fun ConnectionScreen(", profile_screen + "@Composable\nprivate fun ConnectionScreen(", "Profile screen insertion")

profile_branch = '''                            AppPage.PROFILE -> ProfileScreen(
                                isConnected = isConnected,
                                deviceCount = devices.size,
                                roomCount = roomNames.size,
                                onOpenSettings = { page = AppPage.SETTINGS },
                                onOpenGroups = { page = AppPage.GROUPS },
                                onOpenHistory = { history = HomeHistoryStore.load(context); page = AppPage.HISTORY },
                                onOpenAnalytics = { page = AppPage.ANALYTICS }
                            )
'''
replace_once("                            AppPage.SETTINGS -> SettingsScreen(", profile_branch + "                            AppPage.SETTINGS -> SettingsScreen(", "Profile route branch")

# Wire new Home callbacks.
replace_once(
    '''                                onAnalytics = { page = AppPage.ANALYTICS },
                                onOpenGroups = { page = AppPage.GROUPS },
                                onOpenGroup =''',
    '''                                onAnalytics = { page = AppPage.ANALYTICS },
                                onOpenGroups = { page = AppPage.GROUPS },
                                onOpenDevices = { page = AppPage.DEVICES },
                                onOpenScenarios = { page = AppPage.SCENARIOS },
                                onOpenAutomations = { page = AppPage.AUTOMATIONS },
                                onOpenGroup =''',
    "Home callback wiring"
)

# Replace bottom navigation with the five reference tabs and theme-aware colors.
nav_start = "                if (isConnected && page in setOf(AppPage.HOME, AppPage.SCENARIOS, AppPage.HISTORY, AppPage.DEVICE, AppPage.GROUPS, AppPage.GROUP_DETAILS, AppPage.ANALYTICS)) {\n                    NavigationBar("
nav_end = "\n                }\n            }\n        }\n    }\n}\n}\n\n@Composable\nprivate fun ProfileScreen"
a = text.find(nav_start)
b = text.find(nav_end, a)
if a < 0 or b < 0:
    raise SystemExit("Could not locate bottom NavigationBar boundaries")
nav = '''                if (isConnected && page in setOf(AppPage.HOME, AppPage.DEVICES, AppPage.SCENARIOS, AppPage.AUTOMATIONS, AppPage.PROFILE, AppPage.HISTORY, AppPage.DEVICE, AppPage.GROUPS, AppPage.GROUP_DETAILS, AppPage.ANALYTICS)) {
                    val navBackground = if (isDarkTheme) listOf(Color(0xFF20283A), Color(0xFF171F31)) else listOf(Color(0xFFFDFDFF), Color(0xFFEDEBFA))
                    NavigationBar(
                        modifier = Modifier.fillMaxWidth().padding(horizontal = 12.dp, vertical = 6.dp)
                            .clip(RoundedCornerShape(23.dp))
                            .border(1.dp, MaterialTheme.colorScheme.outlineVariant.copy(alpha = 0.7f), RoundedCornerShape(23.dp))
                            .background(Brush.linearGradient(navBackground)),
                        containerColor = Color.Transparent,
                        tonalElevation = 0.dp
                    ) {
                        val selectedColor = MaterialTheme.colorScheme.primary
                        val idleColor = MaterialTheme.colorScheme.onSurfaceVariant
                        NavigationBarItem(
                            selected = page in setOf(AppPage.HOME, AppPage.GROUP_DETAILS, AppPage.HISTORY),
                            onClick = { page = AppPage.HOME },
                            icon = { SmartGlyph("home", Modifier.size(21.dp), if (page == AppPage.HOME) selectedColor else idleColor) },
                            label = { Text("Главная", maxLines = 1, fontSize = 9.sp) },
                            colors = NavigationBarItemDefaults.colors(selectedIconColor = selectedColor, selectedTextColor = selectedColor, unselectedIconColor = idleColor, unselectedTextColor = idleColor, indicatorColor = selectedColor.copy(alpha = 0.13f))
                        )
                        NavigationBarItem(
                            selected = page in setOf(AppPage.DEVICES, AppPage.DEVICE, AppPage.GROUPS),
                            onClick = { page = AppPage.DEVICES },
                            icon = { SmartGlyph("grid", Modifier.size(21.dp), if (page in setOf(AppPage.DEVICES, AppPage.DEVICE, AppPage.GROUPS)) selectedColor else idleColor) },
                            label = { Text("Устройства", maxLines = 1, fontSize = 9.sp) },
                            colors = NavigationBarItemDefaults.colors(selectedIconColor = selectedColor, selectedTextColor = selectedColor, unselectedIconColor = idleColor, unselectedTextColor = idleColor, indicatorColor = selectedColor.copy(alpha = 0.13f))
                        )
                        NavigationBarItem(
                            selected = page == AppPage.SCENARIOS,
                            onClick = { page = AppPage.SCENARIOS },
                            icon = { SmartGlyph("sparkles", Modifier.size(21.dp), if (page == AppPage.SCENARIOS) selectedColor else idleColor) },
                            label = { Text("Сценарии", maxLines = 1, fontSize = 9.sp) },
                            colors = NavigationBarItemDefaults.colors(selectedIconColor = selectedColor, selectedTextColor = selectedColor, unselectedIconColor = idleColor, unselectedTextColor = idleColor, indicatorColor = selectedColor.copy(alpha = 0.13f))
                        )
                        NavigationBarItem(
                            selected = page == AppPage.AUTOMATIONS,
                            onClick = { page = AppPage.AUTOMATIONS },
                            icon = { SmartGlyph("sparkles", Modifier.size(21.dp), if (page == AppPage.AUTOMATIONS) selectedColor else idleColor) },
                            label = { Text("Автоматизации", maxLines = 1, fontSize = 8.sp) },
                            colors = NavigationBarItemDefaults.colors(selectedIconColor = selectedColor, selectedTextColor = selectedColor, unselectedIconColor = idleColor, unselectedTextColor = idleColor, indicatorColor = selectedColor.copy(alpha = 0.13f))
                        )
                        NavigationBarItem(
                            selected = page in setOf(AppPage.PROFILE, AppPage.SETTINGS, AppPage.ANALYTICS),
                            onClick = { page = AppPage.PROFILE },
                            icon = { SmartGlyph("user", Modifier.size(21.dp), if (page in setOf(AppPage.PROFILE, AppPage.SETTINGS, AppPage.ANALYTICS)) selectedColor else idleColor) },
                            label = { Text("Профиль", maxLines = 1, fontSize = 9.sp) },
                            colors = NavigationBarItemDefaults.colors(selectedIconColor = selectedColor, selectedTextColor = selectedColor, unselectedIconColor = idleColor, unselectedTextColor = idleColor, indicatorColor = selectedColor.copy(alpha = 0.13f))
                        )
                    }
                }'''
text = text[:a] + nav + text[b+len("\n                }"):]

# The floating panels are dynamic in both themes.
replace_once(
    '''            .background(Brush.linearGradient(listOf(Color(0xFF343742), Color(0xFF2C303A))))
            .padding(horizontal = 12.dp, vertical = 8.dp),''',
    '''            .background(MaterialTheme.colorScheme.surfaceVariant)
            .border(1.dp, MaterialTheme.colorScheme.outlineVariant.copy(alpha = 0.62f), RoundedCornerShape(18.dp))
            .padding(horizontal = 12.dp, vertical = 8.dp),''',
    "Status chip background"
)
replace_once('Text(title, color = Color.White, fontSize = 12.sp, fontWeight = FontWeight.Bold, maxLines = 1)',
             'Text(title, color = MaterialTheme.colorScheme.onSurface, fontSize = 12.sp, fontWeight = FontWeight.Bold, maxLines = 1)',
             "Status chip title")
replace_once('Text(detail, color = Color.White.copy(alpha = 0.64f), fontSize = 10.sp, maxLines = 1)',
             'Text(detail, color = MaterialTheme.colorScheme.onSurfaceVariant, fontSize = 10.sp, maxLines = 1)',
             "Status chip detail")

# Device card: adaptive tile color/text palette.
replace_once(
    '''    val iconSize = when (cardSize) { "large" -> 52.dp; "small" -> 38.dp; else -> 44.dp }
    val tileShape''',
    '''    val iconSize = when (cardSize) { "large" -> 52.dp; "small" -> 38.dp; else -> 44.dp }
    val darkUi = MaterialTheme.colorScheme.background.red < 0.5f
    val tileShape''',
    "Device tile palette flag"
)
replace_once(
    '''    val background = when {
        offline -> listOf(Color(0xFF382A32), Color(0xFF292A33))
        on -> listOf(Color(0xFF38304D), Color(0xFF292C3A))
        else -> listOf(Color(0xFF303540), Color(0xFF282C35))
    }''',
    '''    val background = when {
        offline -> if (darkUi) listOf(Color(0xFF382A36), Color(0xFF292B38)) else listOf(Color(0xFFFFE9ED), Color(0xFFF8F1F5))
        on -> if (darkUi) listOf(Color(0xFF393253), Color(0xFF282D42)) else listOf(Color(0xFFEDE6FF), Color(0xFFF4F1FC))
        else -> if (darkUi) listOf(Color(0xFF30394B), Color(0xFF262E40)) else listOf(Color(0xFFE9EDF5), Color(0xFFF7F8FC))
    }''',
    "Device tile background palette"
)
replace_once(
    '        offline -> Color(0xFFFF6879).copy(alpha = 0.24f)\n        on -> Color(0xFF9B7BFA).copy(alpha = 0.22f)\n        else -> Color.White.copy(alpha = 0.055f)',
    'offline -> if (darkUi) Color(0xFFFF6879).copy(alpha = 0.28f) else Color(0xFFE8AAB5)\n        on -> if (darkUi) Color(0xFF9B7BFA).copy(alpha = 0.28f) else Color(0xFFD3C4F6)\n        else -> MaterialTheme.colorScheme.outlineVariant.copy(alpha = 0.72f)',
    "Device tile border palette"
)
replace_once(
    'offline -> Color(0xFF8C909B); on -> Color(0xFFD7C9FF); else -> Color(0xFFC5CBD6)',
    'offline -> if (darkUi) Color(0xFF8C909B) else Color(0xFF89909F); on -> if (darkUi) Color(0xFFD7C9FF) else Color(0xFF7653C6); else -> MaterialTheme.colorScheme.onSurfaceVariant',
    "Device tile icon colors"
)
replace_once('''                            color = if (device.isFavorite) Color(0xFFFFD166) else Color.White.copy(alpha = 0.58f), fontSize = 15.sp)''',
             '''                            color = if (device.isFavorite) Color(0xFFFFB938) else MaterialTheme.colorScheme.onSurfaceVariant, fontSize = 15.sp)''',
             "Device favourite color")
replace_once(
    'offline -> listOf(Color(0xFF70404A), Color(0xFF49333F))\n                                on -> listOf(Color(0xFFAA72FF), Color(0xFF6846C4))\n                                else -> listOf(Color(0xFF56667F), Color(0xFF39485B))',
    'offline -> if (darkUi) listOf(Color(0xFF70404A), Color(0xFF49333F)) else listOf(Color(0xFFE6A4AF), Color(0xFFD98091))\n                                on -> listOf(Color(0xFFA47AF7), Color(0xFF7451D1))\n                                else -> if (darkUi) listOf(Color(0xFF56667F), Color(0xFF39485B)) else listOf(Color(0xFF9DAAC0), Color(0xFF75849D))',
    "Device power button palette"
)
replace_once('''                Text(device.name, color = Color(0xFFF3F4F8), fontWeight = FontWeight.SemiBold,''',
             '''                Text(device.name, color = MaterialTheme.colorScheme.onSurface, fontWeight = FontWeight.SemiBold,''',
             "Device tile name")
replace_once('''                    }, color = if (offline) Color(0xFFFF8290) else Color.White.copy(alpha = 0.66f),''',
             '''                    }, color = if (offline) MaterialTheme.colorScheme.error else MaterialTheme.colorScheme.onSurfaceVariant,''',
             "Device tile status")

# Theme-aware weather panel. The data and refresh behaviour remain unchanged.
replace_once(
    '''    val weatherTemperatureSize = when (weatherCardSize) { "small" -> 24.sp; "large" -> 31.sp; else -> 27.sp }

    BoxWithConstraints''',
    '''    val weatherTemperatureSize = when (weatherCardSize) { "small" -> 24.sp; "large" -> 31.sp; else -> 27.sp }
    val darkUi = MaterialTheme.colorScheme.background.red < 0.5f
    val weatherInk = if (darkUi) Color.White else MaterialTheme.colorScheme.onSurface
    val weatherMuted = if (darkUi) Color.White.copy(alpha = 0.76f) else MaterialTheme.colorScheme.onSurfaceVariant
    val weatherPanel = if (darkUi) listOf(Color(0xFF243653), Color(0xFF294859), Color(0xFF252E43)) else listOf(Color(0xFFE4E8FA), Color(0xFFE3F0F4), Color(0xFFF0E8F8))

    BoxWithConstraints''',
    "Weather palette values"
)
replace_once(
    'colors = listOf(Color(0xFF343044), Color(0xFF2B3746), Color(0xFF27333D)),',
    'colors = weatherPanel,',
    "Weather panel gradient"
)
replace_once('Text("ПОГОДА РЯДОМ", color = Color.White.copy(alpha = 0.84f)', 'Text("ПОГОДА РЯДОМ", color = weatherMuted', "Weather title")
replace_once('color = Color.White.copy(alpha = 0.94f),\n                                    fontSize = 12.sp,', 'color = weatherInk,\n                                    fontSize = 12.sp,', "Weather place")
replace_once('CircularProgressIndicator(Modifier.size(16.dp), color = Color.White, strokeWidth = 1.8.dp)', 'CircularProgressIndicator(Modifier.size(16.dp), color = weatherInk, strokeWidth = 1.8.dp)', "Weather loading")
replace_once('else Text("↻", color = Color.White, fontSize = 20.sp)', 'else Text("↻", color = weatherInk, fontSize = 20.sp)', "Weather refresh icon")
replace_once('''                                    color = Color.White,
                                    fontSize = weatherTemperatureSize,''', '''                                    color = weatherInk,
                                    fontSize = weatherTemperatureSize,''', "Weather temperature")
replace_once('Text(weather.description, color = Color.White,', 'Text(weather.description, color = weatherInk,', "Weather description")
replace_once('Text("Сейчас", color = Color.White.copy(alpha = 0.84f)', 'Text("Сейчас", color = weatherMuted', "Weather now caption")
replace_once('Text("ВЕТЕР", color = Color.White.copy(alpha = 0.82f)', 'Text("ВЕТЕР", color = weatherMuted', "Weather wind caption")
replace_once('Text("ВЛАЖНОСТЬ", color = Color.White.copy(alpha = 0.82f)', 'Text("ВЛАЖНОСТЬ", color = weatherMuted', "Weather humidity caption")
replace_once('Text("ОСАДКИ", color = Color.White.copy(alpha = 0.82f)', 'Text("ОСАДКИ", color = weatherMuted', "Weather precipitation caption")
replace_once('''Text("${"%.1f".format(Locale.getDefault(), weather.windMetersPerSecond)} м/с", color = Color.White, fontSize = 11.sp, fontWeight = FontWeight.Bold)''', '''Text("${"%.1f".format(Locale.getDefault(), weather.windMetersPerSecond)} м/с", color = weatherInk, fontSize = 11.sp, fontWeight = FontWeight.Bold)''', "Weather wind value")
replace_once('''Text("${weather.humidityPercent}%", color = Color.White, fontSize = 11.sp, fontWeight = FontWeight.Bold)''', '''Text("${weather.humidityPercent}%", color = weatherInk, fontSize = 11.sp, fontWeight = FontWeight.Bold)''', "Weather humidity value")
replace_once('''Text("${"%.1f".format(Locale.getDefault(), weather.precipitationMm)} мм", color = Color.White, fontSize = 11.sp, fontWeight = FontWeight.Bold)''', '''Text("${"%.1f".format(Locale.getDefault(), weather.precipitationMm)} мм", color = weatherInk, fontSize = 11.sp, fontWeight = FontWeight.Bold)''', "Weather precipitation value")
replace_once('Text(if (weatherLoading) "Определяем погоду…" else "Показывать погоду по местоположению", color = Color.White,', 'Text(if (weatherLoading) "Определяем погоду…" else "Показывать погоду по местоположению", color = weatherInk,', "Weather empty title")
replace_once('color = if (weatherError.isNotBlank()) Color(0xFFFFD1D1) else Color.White.copy(alpha = 0.72f),', 'color = if (weatherError.isNotBlank()) MaterialTheme.colorScheme.error else weatherMuted,', "Weather error body")
replace_once('Text("Включить погоду", color = Color.White, fontSize = 11.sp)', 'Text("Включить погоду", color = MaterialTheme.colorScheme.primary, fontSize = 11.sp)', "Weather enable link")

# Theme-aware hero/quick action chips and group cards.
replace_once(
    '''            .background(Brush.linearGradient(listOf(Color(0xFF7654B8).copy(alpha = 0.34f), Color(0xFF32627C).copy(alpha = 0.30f))))''',
    '''            .background(Brush.linearGradient(listOf(MaterialTheme.colorScheme.primaryContainer, MaterialTheme.colorScheme.secondaryContainer)))''',
    "Dashboard stats gradient"
)
replace_once('Text(value, color = Color.White, fontSize = 17.sp, fontWeight = FontWeight.Bold)', 'Text(value, color = MaterialTheme.colorScheme.onSurface, fontSize = 17.sp, fontWeight = FontWeight.Bold)', "Dashboard stat value")
replace_once('Text(label, color = Color.White.copy(alpha = 0.72f), fontSize = 9.sp', 'Text(label, color = MaterialTheme.colorScheme.onSurfaceVariant, fontSize = 9.sp', "Dashboard stat label")
replace_once('SmartGlyph(kind, Modifier.size(16.dp), Color.White.copy(alpha = 0.92f))', 'SmartGlyph(kind, Modifier.size(16.dp), MaterialTheme.colorScheme.primary)', "Dashboard metric icon")
replace_once('Text(value, color = Color.White.copy(alpha = 0.94f), fontSize = 11.sp', 'Text(value, color = MaterialTheme.colorScheme.onSurface, fontSize = 11.sp', "Dashboard metric text")

# Dynamic device detail hero panel.
replace_once(
    '''            val offline = !device.isOnline
            val active = device.onOff == true
            val shape''',
    '''            val offline = !device.isOnline
            val active = device.onOff == true
            val darkUi = MaterialTheme.colorScheme.background.red < 0.5f
            val heroInk = MaterialTheme.colorScheme.onSurface
            val heroMuted = MaterialTheme.colorScheme.onSurfaceVariant
            val shape''',
    "Device detail theme values"
)
replace_once(
    '''                    .background(Brush.linearGradient(when {
                        offline -> listOf(Color(0xFF3A2932), Color(0xFF282A34))
                        active -> listOf(Color(0xFF42345E), Color(0xFF29313F), Color(0xFF252D37))
                        else -> listOf(Color(0xFF343B49), Color(0xFF282D38))
                    }, start = Offset.Zero, end = Offset(900f, 800f)))''',
    '''                    .background(Brush.linearGradient(when {
                        offline -> if (darkUi) listOf(Color(0xFF3A2938), Color(0xFF282A38)) else listOf(Color(0xFFFFE8ED), Color(0xFFF7EDF1))
                        active -> if (darkUi) listOf(Color(0xFF42345E), Color(0xFF29313F), Color(0xFF252D37)) else listOf(Color(0xFFE9E0FF), Color(0xFFEAF0FB), Color(0xFFF7F1FC))
                        else -> if (darkUi) listOf(Color(0xFF343B49), Color(0xFF282D38)) else listOf(Color(0xFFE8ECF4), Color(0xFFF8F9FC))
                    }, start = Offset.Zero, end = Offset(900f, 800f)))''',
    "Device detail hero background"
)
replace_once('Text(device.room.ifBlank { "МОЙ ДОМ" }.uppercase(), color = Color.White.copy(alpha = 0.55f)', 'Text(device.room.ifBlank { "МОЙ ДОМ" }.uppercase(), color = heroMuted', "Device detail room label")
replace_once('Text(ApiTextRu.translate(device.type), color = Color.White.copy(alpha = 0.58f)', 'Text(ApiTextRu.translate(device.type), color = heroMuted', "Device detail type label")
replace_once('color = if (device.isFavorite) Color(0xFFFFD166) else Color.White.copy(alpha = 0.72f)', 'color = if (device.isFavorite) Color(0xFFFFB938) else heroMuted', "Device detail favorite")
replace_once('offline -> Color(0xFF8F929D); active -> Color(0xFFE0D4FF); else -> Color(0xFFC7CEDA)', 'offline -> Color(0xFF8F929D); active -> if (darkUi) Color(0xFFE0D4FF) else Color(0xFF7653C6); else -> heroMuted', "Device detail glyph")
replace_once('Text(device.name, color = Color.White, fontWeight = FontWeight.Bold', 'Text(device.name, color = heroInk, fontWeight = FontWeight.Bold', "Device detail name")
replace_once('color = if (offline) Color(0xFFFF8290) else Color.White.copy(alpha = 0.72f), fontSize = 11.sp', 'color = if (offline) MaterialTheme.colorScheme.error else heroMuted, fontSize = 11.sp', "Device detail status")
replace_once('colors = ButtonDefaults.buttonColors(containerColor = if (active) Color(0xFF8059E8) else Color(0xFF4A5364),', 'colors = ButtonDefaults.buttonColors(containerColor = if (active) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.secondaryContainer,', "Device detail main action")
replace_once('contentColor = Color.White, disabledContainerColor = Color(0xFF494A53), disabledContentColor = Color.White.copy(alpha = 0.5f))', 'contentColor = if (active) Color.White else MaterialTheme.colorScheme.onSecondaryContainer, disabledContainerColor = MaterialTheme.colorScheme.surfaceVariant, disabledContentColor = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.5f))', "Device detail action content")

# Group cards adapt to the active theme.
replace_once(
    '''    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(horizontal = 15.dp, vertical = 11.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
        Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
            Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(2.dp)) {
                Text("КОМНАТЫ И ГРУППЫ"''',
    '''    val darkUi = MaterialTheme.colorScheme.background.red < 0.5f
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(horizontal = 15.dp, vertical = 11.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
        Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
            Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(2.dp)) {
                Text("КОМНАТЫ И ГРУППЫ"''',
    "Group screen theme flag"
)
replace_once(
    '.background(Brush.linearGradient(listOf(Color(0xFF343744), Color(0xFF2A2D37))))',
    '.background(Brush.linearGradient(if (darkUi) listOf(Color(0xFF263047), Color(0xFF202A3D)) else listOf(Color(0xFFFFFFFF), Color(0xFFECEBFA))))',
    "Group card gradient"
)
replace_once('Color(0xFF8860E8).copy(alpha = 0.2f)', 'MaterialTheme.colorScheme.primaryContainer', "Group icon background")
replace_once('Color(0xFFC8B2FF)', 'MaterialTheme.colorScheme.primary', "Group icon tint")
replace_once('if (device.isOnline) Color(0xFFC9B6FF) else Color(0xFF7D808A)', 'if (device.isOnline) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.onSurfaceVariant', "Group member icon tint")

# Scenario cards and analytics cards become theme surfaces, not fixed dark blocks.
replace_once(
    '''                            if (index % 2 == 0) listOf(Color(0xFF343541), Color(0xFF292D37))
                            else listOf(Color(0xFF26363A), Color(0xFF282C36))''',
    '''                            if (MaterialTheme.colorScheme.background.red < 0.5f) {
                                if (index % 2 == 0) listOf(Color(0xFF30334A), Color(0xFF252C3D)) else listOf(Color(0xFF263F43), Color(0xFF252D3B))
                            } else {
                                if (index % 2 == 0) listOf(Color(0xFFF0EAFE), Color(0xFFE7EEF8)) else listOf(Color(0xFFE3F4F0), Color(0xFFECEEF8))
                            }''',
    "Scenario card dual palette"
)
replace_once(
    'Text(scenario.name, fontWeight = FontWeight.Bold, fontSize = 14.sp, color = Color.White, maxLines = 2, overflow = TextOverflow.Ellipsis)',
    'Text(scenario.name, fontWeight = FontWeight.Bold, fontSize = 14.sp, color = MaterialTheme.colorScheme.onSurface, maxLines = 2, overflow = TextOverflow.Ellipsis)',
    "Scenario title theme"
)
replace_once(
    'Text(if (scenario.isActive) "Готов к запуску" else "Сценарий дома", color = Color.White.copy(alpha = 0.65f), fontSize = 10.sp)',
    'Text(if (scenario.isActive) "Готов к запуску" else "Сценарий дома", color = MaterialTheme.colorScheme.onSurfaceVariant, fontSize = 10.sp)',
    "Scenario subtitle theme"
)

# Remove all fixed white card borders; the same component reads well in both palettes.
text = text.replace('Color.White.copy(alpha = 0.055f)', 'MaterialTheme.colorScheme.outlineVariant.copy(alpha = 0.72f)')
text = text.replace('Color.White.copy(alpha = 0.075f)', 'MaterialTheme.colorScheme.onSurface.copy(alpha = 0.08f)')

# Add the marker only after every anchor was found.
text = text.rstrip() + "\n\n" + MARKER + "\n"
source.write_text(text, encoding="utf-8")
print("Applied dual theme, five-tab navigation, independent devices/automation/profile screens and dynamic key cards.")