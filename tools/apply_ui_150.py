#!/usr/bin/env python3
from pathlib import Path
import hashlib
import re
import sys
import tempfile
import zipfile

archive = Path(sys.argv[1])

def once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one match, got {count}")
    return text.replace(old, new, 1)

def add_import(text, line):
    if line in text:
        return text
    p = text.find("\n\n")
    if p < 0:
        raise SystemExit("No package/import boundary")
    return text[:p + 2] + line + "\n" + text[p + 2:]

with tempfile.TemporaryDirectory() as td:
    root = Path(td) / "src"
    root.mkdir()
    with zipfile.ZipFile(archive) as z:
        z.extractall(root)

    main_path = root / "app/src/main/java/ru/dislive/yandexhomewidgets/MainActivity.kt"
    scenario_path = root / "app/src/main/java/ru/dislive/yandexhomewidgets/ScenarioCenter.kt"
    main = main_path.read_text(encoding="utf-8")
    scenario = scenario_path.read_text(encoding="utf-8")

    # Hash the bulk power handler before applying any changes.
    match = re.search(r"(?ms)^    fun performOnOff\(deviceIds: List<String>, value: Boolean\) \{.*?^\s{4}\}", main)
    if not match:
        raise SystemExit("performOnOff handler not found")
    power_hash = hashlib.sha256(match.group(0).encode()).hexdigest()
    protected = [
        '.clickable(enabled = enabled && !offline) { onToggle(!on) },',
        'onClick = { onToggle(device.onOff != true) }',
        'onClick = { onToggleGroup(switchable, !allOn) }'
    ]
    for item in protected:
        if item not in main:
            raise SystemExit("Protected power action not found: " + item)

    main = add_import(main, "import androidx.compose.foundation.layout.BoxWithConstraints")

    # Persist new display preferences.
    main = once(main,
        '    var deviceCardHeightDp by remember { mutableStateOf(config.getInt("device_card_height_dp", 188).coerceIn(148, 280)) }\n',
        '    var deviceCardHeightDp by remember { mutableStateOf(config.getInt("device_card_height_dp", 188).coerceIn(148, 280)) }\n'
        '    var deviceColumns by remember { mutableStateOf(config.getInt("device_columns", 2).coerceIn(1, 3)) }\n'
        '    var weatherCardSize by remember { mutableStateOf(config.getString("weather_card_size", "normal") ?: "normal") }\n',
        "display preference state")

    # Query GitHub Releases every time the app starts.
    main = once(main,
        '    LaunchedEffect(Unit) {\n        // With saved API settings the dashboard and its loading indicator are visible',
        '    LaunchedEffect(Unit) { checkUpdates() }\n\n'
        '    LaunchedEffect(Unit) {\n        // With saved API settings the dashboard and its loading indicator are visible',
        "automatic release check")

    # Pass saved settings to the relevant screens.
    main = once(main,
        '                                cardHeightDp = deviceCardHeightDp,\n',
        '                                cardHeightDp = deviceCardHeightDp,\n'
        '                                deviceColumns = deviceColumns,\n'
        '                                weatherCardSize = weatherCardSize,\n',
        "HomeScreen call")
    main = once(main,
        '                                weatherSource = weatherSource,\n',
        '                                deviceColumns = deviceColumns,\n'
        '                                onDeviceColumnsChange = { deviceColumns = it.coerceIn(1, 3); config.edit().putInt("device_columns", deviceColumns).apply() },\n'
        '                                weatherCardSize = weatherCardSize,\n'
        '                                onWeatherCardSizeChange = { weatherCardSize = it; config.edit().putString("weather_card_size", weatherCardSize).apply() },\n'
        '                                weatherSource = weatherSource,\n',
        "SettingsScreen call")
    main = once(main,
        '    cardHeightDp: Int,\n    weather: CurrentWeather?,',
        '    cardHeightDp: Int,\n    deviceColumns: Int,\n    weatherCardSize: String,\n    weather: CurrentWeather?,',
        "HomeScreen signature")
    main = once(main,
        '    onDeviceCardSizeSave: (Int, Int) -> Unit,\n    weatherSource: String,',
        '    onDeviceCardSizeSave: (Int, Int) -> Unit,\n'
        '    deviceColumns: Int,\n    onDeviceColumnsChange: (Int) -> Unit,\n'
        '    weatherCardSize: String,\n    onWeatherCardSizeChange: (String) -> Unit,\n'
        '    weatherSource: String,',
        "SettingsScreen signature")

    # Improve subdued on-surface text contrast without changing decorative borders.
    def brighter(match):
        alpha = float(match.group(2)[:-1])
        return match.group(1) + "0.78f" + match.group(3) if 0.45 <= alpha < 0.78 else match.group(0)
    pattern = r'(MaterialTheme\.colorScheme\.onSurface\.copy\(alpha\s*=\s*)(0\.\d+f)(\))'
    main = re.sub(pattern, brighter, main)
    scenario = re.sub(pattern, brighter, scenario)

    # A maximum of three columns; narrow windows automatically use fewer,
    # wider cards instead of squeezing their contents.
    main = once(main,
        '    LazyVerticalGrid(\n        columns = GridCells.Adaptive(minSize = cardWidthDp.dp),',
        '    BoxWithConstraints(Modifier.fillMaxSize()) {\n'
        '        val availableWidth = (maxWidth - 28.dp).coerceAtLeast(116.dp)\n'
        '        val fittingColumns = ((availableWidth + 10.dp) / 126.dp).toInt().coerceIn(1, 3)\n'
        '        val effectiveColumns = deviceColumns.coerceIn(1, 3).coerceAtMost(fittingColumns)\n'
        '        LazyVerticalGrid(\n        columns = GridCells.Fixed(effectiveColumns),',
        "adaptive device grid")
    main = once(main,
        '\n    }\n}\n\n@Composable\nprivate fun GroupGridHeader(',
        '\n        }\n    }\n}\n\n@Composable\nprivate fun GroupGridHeader(',
        "responsive grid wrapper")

    # Weather-card compact / normal / large presets.
    current_power = '    val currentPower = devices.flatMap { device -> device.properties.filter { it.instance == "power" }.mapNotNull { (it.value as? Number)?.toDouble() } }.takeIf { it.isNotEmpty() }?.sum()\n'
    main = once(main, current_power,
        current_power +
        '    val weatherHorizontalPadding = when (weatherCardSize) { "small" -> 12.dp; "large" -> 20.dp; else -> 16.dp }\n'
        '    val weatherVerticalPadding = when (weatherCardSize) { "small" -> 10.dp; "large" -> 18.dp; else -> 14.dp }\n'
        '    val weatherArtworkSize = when (weatherCardSize) { "small" -> 76.dp; "large" -> 124.dp; else -> 104.dp }\n'
        '    val weatherTemperatureSize = when (weatherCardSize) { "small" -> 34.sp; "large" -> 48.sp; else -> 42.sp }\n',
        "weather size metrics")
    main = once(main,
        '.padding(horizontal = 16.dp, vertical = 14.dp)\n            ) {\n                Row(verticalAlignment = Alignment.CenterVertically) {',
        '.padding(horizontal = weatherHorizontalPadding, vertical = weatherVerticalPadding)\n            ) {\n                Row(verticalAlignment = Alignment.CenterVertically) {',
        "weather card padding")
    main = once(main,
        '                                    fontSize = 42.sp,\n                                    fontWeight = FontWeight.Light,\n                                    lineHeight = 44.sp',
        '                                    fontSize = weatherTemperatureSize,\n                                    fontWeight = FontWeight.Light,\n                                    lineHeight = weatherTemperatureSize',
        "weather temperature size")
    main = once(main,
        'YandexWeatherArtwork(weather?.weatherCode ?: -1, Modifier.size(104.dp))',
        'YandexWeatherArtwork(weather?.weatherCode ?: -1, Modifier.size(weatherArtworkSize))',
        "weather illustration size")

    # Change only the device tile layout shell. The power button click target
    # and its on/off code stay as they are.
    ts = main.index("private fun CompactDeviceTile(")
    te = main.index("private fun deviceIcon(", ts)
    tile = main[ts:te]
    tile = once(tile,
        '    val iconSize = (cardWidthDp * 0.40f).coerceIn(52f, 104f).dp\n'
        '    val powerSize = (cardHeightDp * 0.29f).coerceIn(44f, 74f).dp\n'
        '    val rowHeight = (cardHeightDp - 86).coerceIn(60, 194).dp',
        '    val powerSize = (cardHeightDp * 0.29f).coerceIn(44f, 74f).dp\n'
        '    val rowHeight = (cardHeightDp - 86).coerceIn(60, 194).dp',
        "tile dimensions")
    tile = once(tile,
        '    Box(\n        modifier = Modifier.widthIn(max = cardWidthDp.dp).fillMaxWidth().height(cardHeightDp.dp)',
        '    BoxWithConstraints(\n        modifier = Modifier.fillMaxWidth().height(cardHeightDp.dp)',
        "tile full width")
    tile = once(tile,
        '    ) {\n        Column(verticalArrangement = Arrangement.spacedBy(if (cardSize == "small") 5.dp else 9.dp), modifier = Modifier.padding(top = 10.dp)) {',
        '    ) {\n'
        '        val compactLayout = maxWidth < 132.dp\n'
        '        val tileHorizontalPadding = if (compactLayout) 7.dp else if (cardSize == "large") 17.dp else 12.dp\n'
        '        val iconSize = if (compactLayout) (maxWidth.value - tileHorizontalPadding.value * 2f - powerSize.value - 14f).coerceIn(32f, 46f).dp else (cardWidthDp * 0.40f).coerceIn(52f, 104f).dp\n'
        '        Column(verticalArrangement = Arrangement.spacedBy(if (cardSize == "small") 5.dp else 9.dp), modifier = Modifier.padding(top = 10.dp)) {',
        "tile compact layout")
    tile = once(tile,
        '.clickable(onClick = onOpen).padding(horizontal = if (cardSize == "large") 17.dp else 12.dp, vertical = if (cardSize == "small") 8.dp else 12.dp)',
        '.clickable(onClick = onOpen).padding(horizontal = tileHorizontalPadding, vertical = if (cardSize == "small") 8.dp else 12.dp)',
        "tile adaptive padding")
    main = main[:ts] + tile + main[te:]

    # Add settings cards for columns and weather size.
    main = once(main, '        var cardEditorOpen by remember { mutableStateOf(false) }',
        '        Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)) {\n'
        '            Column(modifier = Modifier.padding(15.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {\n'
        '                Text("Устройств в строке", fontSize = 17.sp, fontWeight = FontWeight.SemiBold)\n'
        '                Text("Можно выбрать до трёх колонок. На узком экране сетка сама уменьшит число колонок, а карточки займут всю доступную ширину.", fontSize = 11.sp, color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.78f))\n'
        '                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(7.dp)) {\n'
        '                    listOf(1, 2, 3).forEach { count -> FilterChip(selected = deviceColumns == count, onClick = { onDeviceColumnsChange(count) }, label = { Text(count.toString()) }) }\n'
        '                }\n'
        '            }\n'
        '        }\n'
        '        var cardEditorOpen by remember { mutableStateOf(false) }',
        "columns settings card")
    main = once(main,
        '        var weatherKeyInput by remember(yandexWeatherApiKey) { mutableStateOf(yandexWeatherApiKey) }',
        '        Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)) {\n'
        '            Column(modifier = Modifier.padding(15.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {\n'
        '                Text("Размер блока погоды", fontSize = 17.sp, fontWeight = FontWeight.SemiBold)\n'
        '                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(7.dp)) {\n'
        '                    listOf("small" to "Компактный", "normal" to "Обычный", "large" to "Крупный").forEach { (size, label) -> FilterChip(selected = weatherCardSize == size, onClick = { onWeatherCardSizeChange(size) }, label = { Text(label, fontSize = 10.sp) }) }\n'
        '                }\n'
        '            }\n'
        '        }\n'
        '        var weatherKeyInput by remember(yandexWeatherApiKey) { mutableStateOf(yandexWeatherApiKey) }',
        "weather settings card")
    main = once(main,
        '            Column(Modifier.fillMaxSize().padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {\n                Text("Размер карточек"',
        '            Column(Modifier.fillMaxSize().padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {\n                ApplyGlassDialogBackdropBlur()\n                Text("Размер карточек"',
        "card editor backdrop blur")

    # Put long scenario descriptions behind an info button.
    scenario = once(scenario,
        '    var ideasOpen by remember { mutableStateOf(false) }\n',
        '    var ideasOpen by remember { mutableStateOf(false) }\n    var infoAutomation by remember { mutableStateOf<LocalAutomation?>(null) }\n',
        "scenario info state")
    switch_line = '                        Switch(checked = automation.enabled, onCheckedChange = { onToggleAutomation(automation.id, it) })'
    if scenario.count(switch_line) != 1:
        raise SystemExit("Automation card switch not found uniquely")
    info_button = '                        TextButton(onClick = { infoAutomation = automation }, modifier = Modifier.size(34.dp), contentPadding = PaddingValues(0.dp)) { Text("i", fontSize = 17.sp, fontWeight = FontWeight.Bold) }\n'
    scenario = scenario.replace(switch_line, info_button + switch_line, 1)
    scenario, cond_count = re.subn(r'(?m)^\s*Text\(automation\.conditions\.joinToString.*\n', '', scenario)
    scenario, act_count = re.subn(r'(?m)^\s*Text\("Тогда: " \+ automation\.actions\.joinToString.*\n', '', scenario)
    if cond_count != 1 or act_count != 1:
        raise SystemExit(f"Scenario descriptions not found uniquely: conditions={cond_count}, actions={act_count}")
    info_dialog = '''    infoAutomation?.let { detail ->
        Dialog(onDismissRequest = { infoAutomation = null }, properties = DialogProperties(usePlatformDefaultWidth = false)) {
            Card(Modifier.fillMaxWidth(0.94f).fillMaxHeight(0.78f), shape = RoundedCornerShape(24.dp), colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)) {
                Column(Modifier.fillMaxWidth().verticalScroll(rememberScrollState()).padding(18.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    ApplyGlassDialogBackdropBlur()
                    Text(detail.name, fontSize = 19.sp, fontWeight = FontWeight.Bold)
                    Text("УСЛОВИЯ", fontSize = 12.sp, fontWeight = FontWeight.ExtraBold, color = MaterialTheme.colorScheme.primary)
                    Text(detail.conditions.joinToString(if (detail.matchAllConditions) " И " else " ИЛИ ") { conditionDescription(it, devices) }, fontSize = 13.sp, color = MaterialTheme.colorScheme.onSurface)
                    Divider(color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.14f))
                    Text("ДЕЙСТВИЯ", fontSize = 12.sp, fontWeight = FontWeight.ExtraBold, color = MaterialTheme.colorScheme.secondary)
                    Text(detail.actions.joinToString(separator = "\\n") { "• " + actionDescription(it, devices, variables, cloudScenarios) }, fontSize = 13.sp, color = MaterialTheme.colorScheme.onSurface)
                    Button(onClick = { infoAutomation = null }, modifier = Modifier.fillMaxWidth()) { Text("Закрыть") }
                }
            }
        }
    }
'''
    scenario = once(scenario, '    if (editorOpen) {\n', info_dialog + '    if (editorOpen) {\n', "scenario info dialog")

    # Single action list containing every device with its supported actions,
    # followed by global actions.
    scenario = once(scenario, '    var actionSection by remember { mutableStateOf("device") }\n', '', "remove action category")
    button_old = '                            Button(onClick = { actionSection = "device"; actionDialog = true }, modifier = Modifier.fillMaxWidth(), shape = RoundedCornerShape(14.dp)) {'
    button_new = '                            Button(onClick = { actionDialog = true }, modifier = Modifier.fillMaxWidth(), shape = RoundedCornerShape(14.dp)) {'
    scenario = once(scenario, button_old, button_new, "unified action button")
    start = scenario.find('                        ChoiceDropdown(\n                            "Категория действия",')
    end = scenario.find('                        when (actionType) {', start + 1) if start >= 0 else -1
    if start < 0 or end < 0:
        raise SystemExit("Split action picker block not found")
    unified = '''                        Text("Устройства и их действия", fontWeight = FontWeight.SemiBold, fontSize = 14.sp)
                        if (controlDeviceOptions.isEmpty()) {
                            Text("Нет устройств с доступными изменениями.", fontSize = 11.sp, color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.78f))
                        } else {
                            devices.forEach { device ->
                                val options = buildList<Pair<String, String>> {
                                    if (device.canToggle) add(AutomationActionType.DEVICE_POWER to "Питание")
                                    if (device.canDim) add(AutomationActionType.BRIGHTNESS to "Яркость")
                                    val cap = device.colorCapability
                                    if (cap != null && (cap.colorModel ?: cap.instance) in setOf("hsv", "rgb")) add(AutomationActionType.COLOR_HSV to "Цвет")
                                    if (device.modeCapabilities.isNotEmpty()) add(AutomationActionType.MODE to "Режим")
                                }
                                if (options.isNotEmpty()) {
                                    Column(Modifier.fillMaxWidth().background(MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.36f), RoundedCornerShape(14.dp)).padding(10.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                                        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                            IconTile(deviceIconKind(device.type, device.name), Modifier.size(30.dp), iconSize = 18.dp)
                                            Column(Modifier.weight(1f)) {
                                                Text(device.name, fontSize = 12.sp, fontWeight = FontWeight.SemiBold)
                                                Text(device.room.ifBlank { "Без комнаты" }, fontSize = 10.sp, color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.78f))
                                            }
                                        }
                                        Row(Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                                            options.forEach { (type, label) ->
                                                FilterChip(selected = actionDevice == device.id && actionType == type, onClick = { actionDevice = device.id; actionType = type; actionModeInstance = ""; actionModeValue = "" }, label = { Text(label, fontSize = 10.sp) })
                                            }
                                        }
                                    }
                                }
                            }
                        }
                        Divider(color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.14f))
                        Text("Общие действия", fontWeight = FontWeight.SemiBold, fontSize = 14.sp)
                        Row(Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                            listOf(AutomationActionType.NOTIFICATION to "Уведомление", AutomationActionType.DELAY to "Задержка", AutomationActionType.SET_VARIABLE to "Переменная", AutomationActionType.RUN_YANDEX_SCENARIO to "Сценарий Яндекса").forEach { (type, label) ->
                                FilterChip(selected = actionDevice.isBlank() && actionType == type, onClick = { actionDevice = ""; actionType = type }, label = { Text(label, fontSize = 10.sp) })
                            }
                        }
'''
    scenario = scenario[:start] + unified + scenario[end:]

    # Apply real blur-behind to translucent dialog windows on Android 12+.
    scenario = once(scenario,
        '            Column(Modifier.fillMaxSize()) {\n                Column(\n',
        '            Column(Modifier.fillMaxSize()) {\n                ApplyGlassDialogBackdropBlur()\n                Column(\n',
        "scenario editor blur")
    action_dialog_marker = '                Column(Modifier.fillMaxSize()) {\n                    Column(Modifier.fillMaxWidth().background(Brush.horizontalGradient'
    action_dialog_blur = '                Column(Modifier.fillMaxSize()) {\n                    ApplyGlassDialogBackdropBlur()\n                    Column(Modifier.fillMaxWidth().background(Brush.horizontalGradient'
    action_dialog_count = scenario.count(action_dialog_marker)
    if action_dialog_count < 1:
        raise SystemExit("No translucent action dialog shells found")
    scenario = scenario.replace(action_dialog_marker, action_dialog_blur)

    glass = root / "app/src/main/java/ru/dislive/yandexhomewidgets/GlassDialogBlur.kt"
    if glass.exists():
        raise SystemExit("GlassDialogBlur.kt already exists")
    glass.write_text('''package ru.dislive.yandexhomewidgets

import android.graphics.Color
import android.graphics.drawable.ColorDrawable
import android.os.Build
import android.view.WindowManager
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.LocalView
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.DialogWindowProvider

@Composable
fun ApplyGlassDialogBackdropBlur() {
    val view = LocalView.current
    val density = LocalDensity.current
    val window = (view.parent as? DialogWindowProvider)?.window
    val radius = with(density) { 24.dp.roundToPx() }
    DisposableEffect(window, radius) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S && window != null) {
            window.setBackgroundDrawable(ColorDrawable(Color.TRANSPARENT))
            window.addFlags(WindowManager.LayoutParams.FLAG_BLUR_BEHIND)
            window.setBackgroundBlurRadius(radius)
            val params = window.attributes
            params.dimAmount = 0.22f
            window.attributes = params
        } else if (window != null) {
            window.setBackgroundDrawable(ColorDrawable(0x66070A12))
        }
        onDispose {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S && window != null) {
                window.setBackgroundBlurRadius(0)
                window.clearFlags(WindowManager.LayoutParams.FLAG_BLUR_BEHIND)
            }
        }
    }
}
''', encoding="utf-8")

    # Verify every power command path is unchanged.
    tile_click = protected[0]
    if tile_click not in main:
        raise SystemExit("Tile power click was modified")
    after = re.search(r"(?ms)^    fun performOnOff\(deviceIds: List<String>, value: Boolean\) \{.*?^\s{4}\}", main)
    if not after or hashlib.sha256(after.group(0).encode()).hexdigest() != power_hash:
        raise SystemExit("Bulk power handler was modified")
    for item in protected[1:]:
        if item not in main:
            raise SystemExit("Device or group power action changed")

    version_file = root / "VERSION.txt"
    if version_file.read_text().strip() != "1.4.9":
        raise SystemExit("Expected current source version 1.4.9")
    version_file.write_text("1.5.0\n")
    gradle_file = root / "app/build.gradle.kts"
    gradle = once(gradle_file.read_text(), 'versionName = "1.4.9"', 'versionName = "1.5.0"', "Gradle version")
    gradle_file.write_text(gradle)

    main_path.write_text(main, encoding="utf-8")
    scenario_path.write_text(scenario, encoding="utf-8")
    out = archive.with_suffix(".new.zip")
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for path in sorted(root.rglob("*")):
            if path.is_file():
                z.write(path, path.relative_to(root))
    out.replace(archive)
    print("Applied requested interface changes for v1.5.0.")
    print("Power buttons and command handlers verified unchanged.")
