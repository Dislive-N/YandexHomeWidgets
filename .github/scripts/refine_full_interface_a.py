#!/usr/bin/env python3
"""Full reference-inspired redesign of home and device detail."""
from pathlib import Path
import sys
source = Path(sys.argv[1])
text = source.read_text(encoding="utf-8")
MARKER = "// FULL-INTERFACE-PART-A-1.7.0"
if MARKER in text:
    print("Home and device redesign already applied.")
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
    a_func = text.find(start_token)
    b_func = text.find(end_token, a_func + len(start_token))
    if a_func < 0 or b_func < 0:
        raise SystemExit(f"Could not locate function boundaries: {name} -> {next_name}")
    a = text.rfind("@Composable", 0, a_func) if "@Composable" in text[max(0, a_func - 24):a_func] else a_func
    b_annot = text.rfind("@Composable", 0, b_func)
    b = b_annot if annotate_next and b_annot > a_func and text[b_annot:b_func].strip() == "@Composable" else b_func
    text = text[:a] + body.rstrip() + "\n\n" + text[b:]

old_filter = '''        val byCategory = when (selectedCategory) {
            "Все" -> devices
            "Не в сети" -> devices.filterNot { it.isOnline }
            "Избранное" -> devices.filter { it.isFavorite }
            "Свет", "Освещение" -> devices.filter { dashboardDeviceCategory(it) == "Освещение" }
            else -> devices.filter { dashboardDeviceCategory(it) == selectedCategory }
        }'''
new_filter = '''        val byCategory = when (selectedCategory) {
            "Все" -> devices
            "Проблемы" -> devices.filter(::deviceNeedsAttention)
            "Не в сети" -> devices.filterNot { it.isOnline }
            "Избранное" -> devices.filter { it.isFavorite }
            "Свет", "Освещение" -> devices.filter { dashboardDeviceCategory(it) == "Освещение" }
            "Медиа" -> devices.filter { dashboardDeviceCategory(it) == "Медиа" }
            else -> devices.filter { dashboardDeviceCategory(it) == selectedCategory }
        }'''
replace_once(old_filter, new_filter, "Problems filter")

replace_once(
    '''                listOf("Все", "Не в сети", "Избранное", "Освещение", "Розетки", "Климат", "Безопасность", "Датчики", "Медиа", "Другое").forEach { category ->''',
    '''                listOf("Все", "Проблемы", "Свет", "Медиа", "Избранное", "Розетки", "Климат", "Безопасность", "Датчики").forEach { category ->''',
    "Home category chips"
)
replace_once(
    '''                        "Избранное" -> favoriteDevices.size
                        else -> devices.count { dashboardDeviceCategory(it) == category }''',
    '''                        "Избранное" -> favoriteDevices.size
                        "Проблемы" -> devices.count(::deviceNeedsAttention)
                        "Свет" -> lightDevices.size
                        else -> devices.count { dashboardDeviceCategory(it) == category }''',
    "Home category counts"
)
replace_once(
    'label = { Text("$category · $count", fontSize = 10.sp, maxLines = 1) }',
    'label = { Text(if (category == "Проблемы") "$category $count" else category, fontSize = 11.sp, maxLines = 1) }',
    "Category labels"
)
replace_once(
    '''        listOf("camera", "lock", "security", "door", "замок", "камера", "двер").any(key::contains) -> "Безопасность"
        device.properties.isNotEmpty()''',
    '''        listOf("camera", "lock", "security", "door", "замок", "камера", "двер").any(key::contains) -> "Безопасность"
        listOf("tv", "media", "speaker", "audio", "телевиз", "колонк", "медиаплеер", "приставк").any(key::contains) -> "Медиа"
        device.properties.isNotEmpty()''',
    "Media device classification"
)

problem_helper = '''
private fun deviceNeedsAttention(device: HomeDevice): Boolean {
    if (!device.isOnline) return true
    return device.properties.any { property ->
        val numeric = (property.value as? Number)?.toDouble()
        when (property.instance.lowercase()) {
            "battery_level" -> numeric != null && numeric < 20.0
            "co2_level" -> numeric != null && numeric > 1000.0
            "water_leak", "smoke", "gas" -> when (val value = property.value) {
                is Boolean -> value
                is Number -> value.toInt() != 0
                is String -> value.lowercase() in setOf("detected", "true", "1", "on", "leak", "smoke")
                else -> false
            }
            else -> false
        }
    }
}
'''
replace_once(
    "private fun dashboardDeviceCategory(device: HomeDevice): String {",
    problem_helper + "\nprivate fun dashboardDeviceCategory(device: HomeDevice): String {",
    "Problem detection helper"
)

compact_tile = r'''@Composable
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
    val iconSize = when (cardSize) { "large" -> 52.dp; "small" -> 38.dp; else -> 44.dp }
    val tileShape = RoundedCornerShape(19.dp)
    val background = when {
        offline -> listOf(Color(0xFF382A32), Color(0xFF292A33))
        on -> listOf(Color(0xFF38304D), Color(0xFF292C3A))
        else -> listOf(Color(0xFF303540), Color(0xFF282C35))
    }
    val border = when {
        offline -> Color(0xFFFF6879).copy(alpha = 0.24f)
        on -> Color(0xFF9B7BFA).copy(alpha = 0.22f)
        else -> Color.White.copy(alpha = 0.055f)
    }
    Box(Modifier.fillMaxWidth(), contentAlignment = Alignment.TopCenter) {
        Column(
            Modifier.widthIn(max = cardWidthDp.dp).fillMaxWidth()
                .height(cardHeightDp.coerceIn(112, 220).dp)
                .clip(tileShape)
                .background(Brush.linearGradient(background, start = Offset.Zero, end = Offset(360f, 520f)))
                .border(1.dp, border, tileShape)
                .clickable(onClick = onOpen)
                .padding(horizontal = 9.dp, vertical = 9.dp),
            verticalArrangement = Arrangement.SpaceBetween
        ) {
            Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.Top) {
                Box(Modifier.weight(1f).height(55.dp), contentAlignment = Alignment.Center) {
                    SmartGlyph(deviceIconKind(device.type, device.name), Modifier.size(iconSize),
                        when { offline -> Color(0xFF8C909B); on -> Color(0xFFD7C9FF); else -> Color(0xFFC5CBD6) })
                }
                Column(horizontalAlignment = Alignment.End, verticalArrangement = Arrangement.spacedBy(5.dp)) {
                    Box(Modifier.size(25.dp).clip(CircleShape).background(Color.White.copy(alpha = 0.075f))
                        .clickable { onFavorite(!device.isFavorite) }, contentAlignment = Alignment.Center) {
                        Text(if (device.isFavorite) "★" else "☆",
                            color = if (device.isFavorite) Color(0xFFFFD166) else Color.White.copy(alpha = 0.58f), fontSize = 15.sp)
                    }
                    if (device.canToggle) {
                        Box(Modifier.size(27.dp).clip(CircleShape)
                            .background(Brush.linearGradient(when {
                                offline -> listOf(Color(0xFF70404A), Color(0xFF49333F))
                                on -> listOf(Color(0xFFAA72FF), Color(0xFF6846C4))
                                else -> listOf(Color(0xFF56667F), Color(0xFF39485B))
                            }))
                            .clickable(enabled = enabled && !offline) { onToggle(!on) },
                            contentAlignment = Alignment.Center) {
                            if (pending) CircularProgressIndicator(Modifier.size(14.dp), strokeWidth = 1.7.dp, color = Color.White)
                            else SmartGlyph(if (on) "off" else "power", Modifier.size(17.dp), Color.White)
                        }
                    }
                }
            }
            Column(Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(3.dp)) {
                Text(device.name, color = Color(0xFFF3F4F8), fontWeight = FontWeight.SemiBold,
                    fontSize = if (cardSize == "large") 12.sp else 10.sp, maxLines = 2, lineHeight = 12.sp, overflow = TextOverflow.Ellipsis)
                Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                    Box(Modifier.size(6.dp).clip(CircleShape).background(
                        when { offline -> Color(0xFFFF6477); on -> Color(0xFF57D4A5); else -> Color(0xFF9CA4B2) }))
                    Text(when {
                        offline -> "Не в сети"
                        pending -> "Обновление…"
                        on -> "Включено"
                        device.onOff == false -> "Выключено"
                        else -> device.room.ifBlank { "В сети" }
                    }, color = if (offline) Color(0xFFFF8290) else Color.White.copy(alpha = 0.66f),
                        fontSize = 8.sp, maxLines = 1, overflow = TextOverflow.Ellipsis)
                }
            }
        }
    }
}
'''
replace_function("CompactDeviceTile", "DeviceDetailsScreen", compact_tile)

device_detail = r'''@Composable
private fun DeviceDetailsScreen(
    device: HomeDevice,
    isBusy: Boolean,
    onFavorite: (Boolean) -> Unit,
    onToggle: (Boolean) -> Unit,
    onBrightness: (Int) -> Unit,
    onHue: (Int) -> Unit,
    onTemperature: (Int) -> Unit,
    onColorScene: (String) -> Unit,
    onMode: (String, String) -> Unit
) {
    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(horizontal = 15.dp, vertical = 10.dp),
        verticalArrangement = Arrangement.spacedBy(11.dp)
    ) {
        item(key = "device_hero") {
            val offline = !device.isOnline
            val active = device.onOff == true
            val shape = RoundedCornerShape(26.dp)
            Column(
                Modifier.fillMaxWidth().clip(shape)
                    .background(Brush.linearGradient(when {
                        offline -> listOf(Color(0xFF3A2932), Color(0xFF282A34))
                        active -> listOf(Color(0xFF42345E), Color(0xFF29313F), Color(0xFF252D37))
                        else -> listOf(Color(0xFF343B49), Color(0xFF282D38))
                    }, start = Offset.Zero, end = Offset(900f, 800f)))
                    .border(1.dp, Color.White.copy(alpha = 0.075f), shape).padding(18.dp),
                horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                    Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(2.dp)) {
                        Text(device.room.ifBlank { "МОЙ ДОМ" }.uppercase(), color = Color.White.copy(alpha = 0.55f), fontSize = 9.sp, fontWeight = FontWeight.Bold, letterSpacing = 1.sp)
                        Text(ApiTextRu.translate(device.type), color = Color.White.copy(alpha = 0.58f), fontSize = 10.sp)
                    }
                    TextButton(onClick = { onFavorite(!device.isFavorite) }, contentPadding = PaddingValues(4.dp)) {
                        Text(if (device.isFavorite) "★" else "☆", color = if (device.isFavorite) Color(0xFFFFD166) else Color.White.copy(alpha = 0.72f), fontSize = 22.sp)
                    }
                }
                Box(Modifier.size(118.dp), contentAlignment = Alignment.Center) {
                    if (active && !offline) Box(Modifier.size(108.dp).clip(CircleShape).background(Color(0xFF9D79F3).copy(alpha = 0.12f)))
                    SmartGlyph(deviceIconKind(device.type, device.name), Modifier.size(82.dp),
                        when { offline -> Color(0xFF8F929D); active -> Color(0xFFE0D4FF); else -> Color(0xFFC7CEDA) })
                }
                Text(device.name, color = Color.White, fontWeight = FontWeight.Bold, fontSize = 20.sp,
                    textAlign = androidx.compose.ui.text.style.TextAlign.Center, maxLines = 2, overflow = TextOverflow.Ellipsis)
                Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                    Box(Modifier.size(7.dp).clip(CircleShape).background(if (offline) Color(0xFFFF6578) else if (active) Color(0xFF5BD5A8) else Color(0xFF9CA4B2)))
                    Text(when { offline -> "Не в сети"; active -> "Включено"; device.onOff == false -> "Выключено"; else -> "Подключено" },
                        color = if (offline) Color(0xFFFF8290) else Color.White.copy(alpha = 0.72f), fontSize = 11.sp, fontWeight = FontWeight.SemiBold)
                }
                if (device.canToggle) {
                    Button(onClick = { onToggle(!active) }, enabled = !isBusy && device.isOnline,
                        modifier = Modifier.fillMaxWidth(), shape = RoundedCornerShape(15.dp),
                        colors = ButtonDefaults.buttonColors(containerColor = if (active) Color(0xFF8059E8) else Color(0xFF4A5364),
                            contentColor = Color.White, disabledContainerColor = Color(0xFF494A53), disabledContentColor = Color.White.copy(alpha = 0.5f))
                    ) { Text(if (active) "Выключить" else "Включить", fontWeight = FontWeight.Bold) }
                }
            }
        }
        item(key = "device_controls") {
            DeviceCard(device = device, isBusy = isBusy, onToggle = onToggle, onBrightness = onBrightness,
                onHue = onHue, onTemperature = onTemperature, onColorScene = onColorScene, onMode = onMode)
        }
        if (device.properties.isNotEmpty()) {
            item(key = "device_sensor_heading") { Text("Показатели устройства", fontSize = 15.sp, fontWeight = FontWeight.Bold, modifier = Modifier.padding(top = 2.dp)) }
            items(device.properties, key = { "property_\${device.id}_\${it.instance}" }) { property ->
                SensorVisualization(property = property, device = device, modifier = Modifier.fillMaxWidth().height(106.dp))
            }
        }
    }
}
'''
replace_function("DeviceDetailsScreen", "GroupsScreen", device_detail)
text = text.rstrip() + "\n\n" + MARKER + "\n"
source.write_text(text, encoding="utf-8")
print("Applied reference-inspired home, compact device tiles and device details.")
