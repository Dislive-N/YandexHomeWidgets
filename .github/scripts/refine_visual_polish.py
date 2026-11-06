#!/usr/bin/env python3
"""Finish the dual-theme smart-home redesign with room tiles and theme previews."""
from pathlib import Path
import sys

source = Path(sys.argv[1])
text = source.read_text(encoding="utf-8")
MARKER = "// VISUAL-POLISH-1.8.0"
if MARKER in text:
    print("Visual polish already applied.")
    raise SystemExit(0)

def replace_once(old: str, new: str, label: str):
    global text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one anchor, found {count}")
    text = text.replace(old, new, 1)

def replace_lambda_item(anchor: str, replacement: str, label: str):
    global text
    at = text.find(anchor)
    if at < 0:
        raise SystemExit(f"{label}: anchor not found")
    brace = text.find("{", at + len(anchor) - 1)
    if brace < 0:
        raise SystemExit(f"{label}: opening brace missing")
    depth = 0
    end = -1
    for i in range(brace, len(text)):
        if text[i] == "{": depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    if end < 0:
        raise SystemExit(f"{label}: closing brace missing")
    text = text[:at] + replacement + text[end:]

# Fix the unit strings in the weather panel and remove a copied terminal control code.
replace_once(
    'Text("${"%.1f".format(Locale.getDefault(), weather.windMetersPerSecond)} " м/с", color = weatherInk, fontSize = 11.sp, fontWeight = FontWeight.Bold)',
    'Text("${"%.1f".format(Locale.getDefault(), weather.windMetersPerSecond)} м/с", color = weatherInk, fontSize = 11.sp, fontWeight = FontWeight.Bold)',
    "Weather wind value"
)
replace_once(
    'Text("${weather.humidityPercent}"%", color = weatherInk, fontSize = 11.sp, fontWeight = FontWeight.Bold)',
    'Text("${weather.humidityPercent}%", color = weatherInk, fontSize = 11.sp, fontWeight = FontWeight.Bold)',
    "Weather humidity value"
)
replace_once(
    'Text("${"%.1f".format(Locale.getDefault(), weather.precipitationMm)} " мм", color = weatherInk, fontSize = 11.sp, fontWeight = FontWeight.Bold)',
    'Text("${"%.1f".format(Locale.getDefault(), weather.precipitationMm)} мм", color = weatherInk, fontSize = 11.sp, fontWeight = FontWeight.Bold)',
    "Weather precipitation value"
)
text = text.replace("\x1b[0m", "")

# Add local room/sensor summaries; no extra API requests are made.
replace_once(
    '''    val activeLights = lightDevices.count { it.isOnline && it.onOff == true }
    val activeSockets = socketDevices.count { it.isOnline && it.onOff == true }
    val weatherHorizontalPadding''',
    '''    val activeLights = lightDevices.count { it.isOnline && it.onOff == true }
    val activeSockets = socketDevices.count { it.isOnline && it.onOff == true }
    val averageTemperature = devices.flatMap { device -> device.properties.filter { it.instance == "temperature" }.mapNotNull { (it.value as? Number)?.toDouble() } }.takeIf { it.isNotEmpty() }?.average()
    val averageHumidity = devices.flatMap { device -> device.properties.filter { it.instance == "humidity" }.mapNotNull { (it.value as? Number)?.toDouble() } }.takeIf { it.isNotEmpty() }?.average()
    val averageCo2 = devices.flatMap { device -> device.properties.filter { it.instance == "co2_level" }.mapNotNull { (it.value as? Number)?.toDouble() } }.takeIf { it.isNotEmpty() }?.average()
    val homeRoomCards = remember(rooms, devices) { (rooms + devices.map { it.room }.filter { it.isNotBlank() }).distinct() }
    val weatherHorizontalPadding''',
    "Home summary values"
)

hero = r'''        item(span = { GridItemSpan(maxLineSpan) }, key = "dashboard_hero") {
            Column(Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                val heroShape = RoundedCornerShape(25.dp)
                val heroColors = if (darkUi) listOf(Color(0xFF152846), Color(0xFF243B5A), Color(0xFF342B50)) else listOf(Color(0xFFE7E4F9), Color(0xFFE5F0F7), Color(0xFFF5EAF5))
                val heroInk = if (darkUi) Color.White else MaterialTheme.colorScheme.onSurface
                val heroMuted = if (darkUi) Color.White.copy(alpha = 0.76f) else MaterialTheme.colorScheme.onSurfaceVariant
                Row(
                    Modifier.fillMaxWidth().height(158.dp).clip(heroShape)
                        .background(Brush.linearGradient(heroColors, start = Offset.Zero, end = Offset(900f, 600f)))
                        .border(1.dp, MaterialTheme.colorScheme.outlineVariant.copy(alpha = 0.55f), heroShape)
                        .padding(horizontal = 17.dp, vertical = 15.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column(Modifier.weight(0.72f), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                        Text("ВАШ УМНЫЙ ДОМ", color = heroMuted, fontSize = 9.sp, fontWeight = FontWeight.Bold, letterSpacing = 1.3.sp)
                        Text(
                            when {
                                devices.isEmpty() -> "Подключи свой дом"
                                offlineCount > 0 -> "Есть проблемы со связью"
                                else -> "Ваш умный дом в порядке"
                            },
                            color = heroInk, fontSize = 20.sp, lineHeight = 23.sp, fontWeight = FontWeight.ExtraBold,
                            maxLines = 2, overflow = TextOverflow.Ellipsis
                        )
                        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                            Box(Modifier.size(7.dp).clip(CircleShape).background(if (offlineCount > 0) MaterialTheme.colorScheme.error else Color(0xFF52C79E)))
                            Text(
                                when { devices.isEmpty() -> "Ожидает подключения"; offlineCount > 0 -> "$offlineCount устройств не в сети"; else -> "Все устройства работают" },
                                color = heroMuted, fontSize = 10.sp, maxLines = 1, overflow = TextOverflow.Ellipsis
                            )
                        }
                        Text("$onlineCount из ${devices.size} устройств онлайн", color = heroMuted, fontSize = 9.sp)
                    }
                    Box(Modifier.weight(0.28f).fillMaxHeight(), contentAlignment = Alignment.Center) {
                        Box(Modifier.size(94.dp).clip(CircleShape).background(MaterialTheme.colorScheme.primary.copy(alpha = if (darkUi) 0.15f else 0.11f)))
                        SmartGlyph("home", Modifier.size(68.dp), if (darkUi) Color(0xFFD7C7FF) else MaterialTheme.colorScheme.primary)
                    }
                }
                Row(Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    HomeStatusChip("°", "Температура", averageTemperature?.let { "${it.toInt()}°" } ?: "Нет данных", Color(0xFF54A6F0))
                    HomeStatusChip("◌", "Влажность", averageHumidity?.let { "${it.toInt()}%" } ?: "Нет данных", Color(0xFF45BFCB))
                    HomeStatusChip("✦", "Воздух", averageCo2?.let { if (it < 800) "Отлично" else if (it <= 1000) "Норма" else "Проветрить" } ?: "Нет данных", if (averageCo2 != null && averageCo2 > 1000) Color(0xFFFF8A66) else Color(0xFF48C49D))
                    HomeStatusChip("☼", "Свет", "$activeLights из ${lightDevices.size} вкл.", Color(0xFFAA83FF))
                    HomeStatusChip("●", "Розетки", "$activeSockets из ${socketDevices.size} вкл.", Color(0xFF8E72EF))
                }
            }
        }'''
replace_lambda_item('        item(span = { GridItemSpan(maxLineSpan) }, key = "dashboard_hero") {', hero, "Home hero card")

# Room preview row: clicking a room filters the dashboard list to that room.
room_preview = r'''        item(span = { GridItemSpan(maxLineSpan) }, key = "room_previews") {
            if (homeRoomCards.isNotEmpty()) {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                        Text("Комнаты", fontSize = 16.sp, fontWeight = FontWeight.Bold, modifier = Modifier.weight(1f))
                        Text("${homeRoomCards.size}", color = MaterialTheme.colorScheme.onSurfaceVariant, fontSize = 10.sp)
                    }
                    Row(Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(9.dp)) {
                        homeRoomCards.forEachIndexed { index, room ->
                            val roomDevices = devices.filter { it.room == room }
                            val active = roomDevices.count { it.isOnline && it.onOff == true }
                            val shades = if (darkUi) {
                                listOf(listOf(Color(0xFF2B3654), Color(0xFF202B40)), listOf(Color(0xFF3C3156), Color(0xFF282B43)), listOf(Color(0xFF27454A), Color(0xFF202F3E)))
                            } else {
                                listOf(listOf(Color(0xFFE9E5FA), Color(0xFFE3EDF6)), listOf(Color(0xFFF0E7F7), Color(0xFFE9EAF8)), listOf(Color(0xFFE0F1EE), Color(0xFFE8EDF8)))
                            }
                            val roomShape = RoundedCornerShape(18.dp)
                            Column(
                                Modifier.width(132.dp).height(88.dp).clip(roomShape)
                                    .background(Brush.linearGradient(shades[index % shades.size]))
                                    .border(1.dp, MaterialTheme.colorScheme.outlineVariant.copy(alpha = 0.5f), roomShape)
                                    .clickable { selectedCategory = "Все"; deviceSearch = room }
                                    .padding(11.dp),
                                verticalArrangement = Arrangement.SpaceBetween
                            ) {
                                SmartGlyph("home", Modifier.size(22.dp), if (darkUi) Color(0xFFD5C5FF) else MaterialTheme.colorScheme.primary)
                                Column(verticalArrangement = Arrangement.spacedBy(2.dp)) {
                                    Text(room, color = MaterialTheme.colorScheme.onSurface, fontWeight = FontWeight.Bold, fontSize = 11.sp, maxLines = 1, overflow = TextOverflow.Ellipsis)
                                    Text("${roomDevices.size} устройств · $active вкл.", color = MaterialTheme.colorScheme.onSurfaceVariant, fontSize = 9.sp, maxLines = 1, overflow = TextOverflow.Ellipsis)
                                }
                            }
                        }
                    }
                }
            }
        }
'''
replace_once(
    '        item(span = { GridItemSpan(maxLineSpan) }, key = "device_search") {',
    room_preview + '        item(span = { GridItemSpan(maxLineSpan) }, key = "device_search") {',
    "Room preview insertion"
)

# A clearer room header and separators in both themes.
replace_once(
    'Text(roomName, fontSize = 18.sp, fontWeight = FontWeight.Bold)',
    'Text(roomName, fontSize = 16.sp, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.onSurface)',
    "Room section heading"
)
replace_once(
    'Text(roomDevices.size.toString() + " устройств", color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.56f), fontSize = 11.sp)',
    'Text(roomDevices.size.toString() + " устройств", color = MaterialTheme.colorScheme.onSurfaceVariant, fontSize = 10.sp)',
    "Room section count"
)

# Group card outlines and member icon chips are theme neutral.
text = text.replace('Color.White.copy(alpha = 0.065f), tileShape', 'MaterialTheme.colorScheme.outlineVariant.copy(alpha = 0.68f), tileShape')
text = text.replace('background(Color.White.copy(alpha = 0.06f)), contentAlignment = Alignment.Center)', 'background(MaterialTheme.colorScheme.surfaceVariant), contentAlignment = Alignment.Center)')

# Device controls: keep gradient controls vivid, but make the panel and offline state theme aware.
replace_once(
    'Text("Устройство не в сети. Управление временно недоступно.", color = Color(0xFFFF5968), fontSize = 11.sp, fontWeight = FontWeight.Bold)',
    'Text("Устройство не в сети. Управление временно недоступно.", color = MaterialTheme.colorScheme.error, fontSize = 11.sp, fontWeight = FontWeight.Bold)',
    "Device offline warning"
)
replace_once(
    'gradient = listOf(Color(0xFF34224F), Color(0xFF7650B5), Color(0xFFB98BFF), Color(0xFFF5ECFF)),',
    'gradient = if (MaterialTheme.colorScheme.background.red < 0.5f) listOf(Color(0xFF34224F), Color(0xFF7650B5), Color(0xFFB98BFF), Color(0xFFF5ECFF)) else listOf(Color(0xFFB7A1E9), Color(0xFF9070D8), Color(0xFF7653C6), Color(0xFF4D3990)),',
    "Brightness slider palette"
)

# Yandex scenario cards use the correct foreground in both modes and a unified play button.
replace_once(
    'Text(scenario.name, fontWeight = FontWeight.Bold, fontSize = 14.sp, color = MaterialTheme.colorScheme.onSurface, maxLines = 2, overflow = TextOverflow.Ellipsis)',
    'Text(scenario.name, fontWeight = FontWeight.Bold, fontSize = 14.sp, color = MaterialTheme.colorScheme.onSurface, maxLines = 2, overflow = TextOverflow.Ellipsis)',
    "Scenario title verified"
)
replace_once(
    'SmartGlyph("sparkles", Modifier.size(22.dp), Color(0xFFC6B1FF))',
    'SmartGlyph("sparkles", Modifier.size(22.dp), MaterialTheme.colorScheme.primary)',
    "Scenario icon tint"
)
replace_once(
    'containerColor = Color(0xFF8059E8),\n                        contentColor = Color.White,\n                        disabledContainerColor = Color(0xFF514B60),\n                        disabledContentColor = Color.White.copy(alpha = 0.58f)',
    'containerColor = MaterialTheme.colorScheme.primary,\n                        contentColor = Color.White,\n                        disabledContainerColor = MaterialTheme.colorScheme.surfaceVariant,\n                        disabledContentColor = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.58f)',
    "Scenario play button palette"
)

# Analytics hero has its own light/dark treatment; the data remains unchanged.
replace_once(
    '''    val alerts = buildList {''',
    '''    val darkUi = MaterialTheme.colorScheme.background.red < 0.5f
    val alerts = buildList {''',
    "Analytics theme flag"
)
replace_once(
    'Brush.linearGradient(listOf(Color(0xFF142B48), Color(0xFF1A4053), Color(0xFF173043))),',
    'Brush.linearGradient(if (darkUi) listOf(Color(0xFF182B47), Color(0xFF21475A), Color(0xFF1C2F45)) else listOf(Color(0xFFE3E8FA), Color(0xFFE0F0F1), Color(0xFFEEE6F7))),',
    "Analytics hero gradient"
)
replace_once(
    'Text("Тренды и состояние дома", color = Color.White, fontWeight = FontWeight.Bold, fontSize = 18.sp)',
    'Text("Тренды и состояние дома", color = MaterialTheme.colorScheme.onSurface, fontWeight = FontWeight.Bold, fontSize = 18.sp)',
    "Analytics hero title"
)
replace_once(
    'Text("Локальные графики показаний за последние 24 часа или 7 дней", color = Color.White.copy(alpha = 0.8f), fontSize = 11.sp)',
    'Text("Локальные графики показаний за последние 24 часа или 7 дней", color = MaterialTheme.colorScheme.onSurfaceVariant, fontSize = 11.sp)',
    "Analytics hero subtitle"
)

# Re-theme the cards and dialogs that still have white-only outlines.
text = text.replace('Color.White.copy(alpha = 0.045f)', 'MaterialTheme.colorScheme.outlineVariant.copy(alpha = 0.65f)')
text = text.replace('Color.White.copy(alpha = 0.08f), RoundedCornerShape(20.dp)', 'MaterialTheme.colorScheme.outlineVariant.copy(alpha = 0.65f), RoundedCornerShape(20.dp)')
text = text.replace('Color.White.copy(alpha = 0.08f), RoundedCornerShape(18.dp)', 'MaterialTheme.colorScheme.outlineVariant.copy(alpha = 0.65f), RoundedCornerShape(18.dp)')

text = text.rstrip() + "\n\n" + MARKER + "\n"
source.write_text(text, encoding="utf-8")
print("Applied hero, room previews, device control polish and analytics light/dark styling.")