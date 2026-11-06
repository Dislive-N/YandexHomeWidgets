#!/usr/bin/env python3
"""Redesign remaining primary screens, analytics, settings and navigation."""
from pathlib import Path
import sys
source = Path(sys.argv[1])
text = source.read_text(encoding="utf-8")
MARKER = "// FULL-INTERFACE-PART-B-1.7.0"
if MARKER in text:
    print("Remaining screen redesign already applied.")
    raise SystemExit(0)
def replace_once(old: str, new: str, label: str):
    global text
    n = text.count(old)
    if n != 1: raise SystemExit(f"{label}: expected one anchor, found {n}")
    text = text.replace(old, new, 1)
def replace_function(name: str, next_name: str, body: str, annotate_next: bool = True):
    global text
    start_token = f"private fun {name}("
    end_token = f"private fun {next_name}("
    af = text.find(start_token)
    bf = text.find(end_token, af + len(start_token))
    if af < 0 or bf < 0: raise SystemExit(f"Could not locate {name} -> {next_name}")
    a = text.rfind("@Composable", 0, af) if "@Composable" in text[max(0, af - 24):af] else af
    ba = text.rfind("@Composable", 0, bf)
    b = ba if annotate_next and ba > af and text[ba:bf].strip() == "@Composable" else bf
    text = text[:a] + body.rstrip() + "\n\n" + text[b:]

groups_screen = r'''@Composable
private fun GroupsScreen(
    groups: List<DeviceGroup>,
    devices: List<HomeDevice>,
    onOpenGroup: (DeviceGroup) -> Unit,
    onSave: (DeviceGroup) -> Unit,
    onDelete: (DeviceGroup) -> Unit
) {
    var editorOpen by remember { mutableStateOf(false) }
    var editingId by remember { mutableStateOf("") }
    var draftName by remember { mutableStateOf("") }
    var selectedIds by remember { mutableStateOf<Set<String>>(emptySet()) }
    fun edit(group: DeviceGroup?) {
        editingId = group?.id.orEmpty()
        draftName = group?.name.orEmpty()
        selectedIds = group?.deviceIds?.toSet().orEmpty()
        editorOpen = true
    }
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(horizontal = 15.dp, vertical = 11.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
        Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
            Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(2.dp)) {
                Text("КОМНАТЫ И ГРУППЫ", color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.52f), fontSize = 9.sp, fontWeight = FontWeight.Bold, letterSpacing = 1.2.sp)
                Text("Управляй вместе", fontSize = 19.sp, fontWeight = FontWeight.Bold)
            }
            Text("\${groups.size}", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.62f))
        }
        Text("Объединяй устройства для быстрого доступа и общего управления. Эти группы не меняют комнаты в приложении Яндекса.", fontSize = 11.sp, color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.68f))
        Button(onClick = { edit(null) }, modifier = Modifier.fillMaxWidth(), shape = RoundedCornerShape(15.dp)) { Text("＋  Создать группу", fontWeight = FontWeight.SemiBold) }
        if (groups.isEmpty()) EmptyCard("Пока нет групп. Создай первую и выбери устройства для неё.")
        groups.forEach { group ->
            val members = devices.filter { it.id in group.deviceIds }
            val online = members.count { it.isOnline }
            val active = members.count { it.isOnline && it.onOff == true }
            val tileShape = RoundedCornerShape(21.dp)
            Column(
                Modifier.fillMaxWidth().clip(tileShape)
                    .background(Brush.linearGradient(listOf(Color(0xFF343744), Color(0xFF2A2D37))))
                    .border(1.dp, Color.White.copy(alpha = 0.065f), tileShape)
                    .clickable { onOpenGroup(group) }.padding(14.dp),
                verticalArrangement = Arrangement.spacedBy(9.dp)
            ) {
                Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                    Box(Modifier.size(46.dp).clip(RoundedCornerShape(14.dp)).background(Color(0xFF8860E8).copy(alpha = 0.2f)), contentAlignment = Alignment.Center) {
                        SmartGlyph("grid", Modifier.size(25.dp), Color(0xFFC8B2FF))
                    }
                    Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(2.dp)) {
                        Text(group.name, fontWeight = FontWeight.Bold, fontSize = 15.sp, maxLines = 1, overflow = TextOverflow.Ellipsis)
                        Text("\${members.size} устройств · $online в сети · $active включено", fontSize = 10.sp, color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.62f), maxLines = 1, overflow = TextOverflow.Ellipsis)
                    }
                    Text("›", color = MaterialTheme.colorScheme.primary, fontSize = 27.sp)
                }
                Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                    members.take(5).forEach { device ->
                        Box(Modifier.size(31.dp).clip(RoundedCornerShape(10.dp)).background(Color.White.copy(alpha = 0.06f)), contentAlignment = Alignment.Center) {
                            SmartGlyph(deviceIconKind(device.type, device.name), Modifier.size(19.dp), if (device.isOnline) Color(0xFFC9B6FF) else Color(0xFF7D808A))
                        }
                    }
                    if (members.size > 5) Text("+\${members.size - 5}", modifier = Modifier.align(Alignment.CenterVertically), color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.66f), fontSize = 10.sp)
                }
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    OutlinedButton(onClick = { edit(group) }, modifier = Modifier.weight(1f), shape = RoundedCornerShape(12.dp)) { Text("Изменить") }
                    TextButton(onClick = { onDelete(group) }, modifier = Modifier.weight(1f)) { Text("Удалить", color = MaterialTheme.colorScheme.error) }
                }
            }
        }
    }
    if (editorOpen) {
        AlertDialog(
            onDismissRequest = { editorOpen = false },
            title = { Text(if (editingId.isBlank()) "Новая группа" else "Изменить группу") },
            text = {
                Column(Modifier.heightIn(max = 430.dp).verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(7.dp)) {
                    OutlinedTextField(value = draftName, onValueChange = { draftName = it.take(40) }, label = { Text("Название группы") }, singleLine = true, modifier = Modifier.fillMaxWidth())
                    Text("Устройства", fontWeight = FontWeight.Bold, fontSize = 13.sp)
                    if (devices.isEmpty()) Text("Сначала подключи устройства.", fontSize = 12.sp)
                    devices.forEach { device ->
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Checkbox(checked = device.id in selectedIds, onCheckedChange = { checked -> selectedIds = if (checked) selectedIds + device.id else selectedIds - device.id })
                            SmartGlyph(deviceIconKind(device.type, device.name), Modifier.size(21.dp), if (device.isOnline) MaterialTheme.colorScheme.primary else Color.Gray)
                            Column(Modifier.weight(1f)) {
                                Text(device.name, fontSize = 12.sp)
                                Text(device.room.ifBlank { if (device.isOnline) "В сети" else "Не в сети" }, fontSize = 10.sp, color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.58f))
                            }
                        }
                    }
                }
            },
            confirmButton = {
                TextButton(enabled = draftName.isNotBlank() && selectedIds.isNotEmpty(), onClick = {
                    val id = editingId.ifBlank { java.util.UUID.randomUUID().toString() }
                    onSave(DeviceGroup(id, draftName.trim(), selectedIds.toList()))
                    editorOpen = false
                }) { Text("Сохранить") }
            },
            dismissButton = { TextButton(onClick = { editorOpen = false }) { Text("Отмена") } }
        )
    }
}
'''
replace_function("GroupsScreen", "groupDeviceFamily", groups_screen, annotate_next=False)

history_screen = r'''@Composable
private fun HistoryScreen(history: List<HomeChange>, onClear: () -> Unit) {
    Column(Modifier.fillMaxSize().padding(horizontal = 15.dp, vertical = 11.dp), verticalArrangement = Arrangement.spacedBy(9.dp)) {
        Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
            Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(2.dp)) {
                Text("АКТИВНОСТЬ ДОМА", color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.52f), fontSize = 9.sp, fontWeight = FontWeight.Bold, letterSpacing = 1.1.sp)
                Text("История изменений", fontSize = 18.sp, fontWeight = FontWeight.Bold)
            }
            TextButton(onClick = onClear, enabled = history.isNotEmpty()) { Text("Очистить") }
        }
        if (history.isEmpty()) EmptyCard("История пока пуста. Она начнёт заполняться после обнаружения изменений в доме.")
        else {
            LazyColumn(verticalArrangement = Arrangement.spacedBy(7.dp), contentPadding = PaddingValues(bottom = 16.dp)) {
                items(history, key = { "\${it.timestamp}-\${it.kind}-\${it.title}-\${it.detail}" }) { change ->
                    Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.Top, horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                        Column(Modifier.width(24.dp), horizontalAlignment = Alignment.CenterHorizontally) {
                            Box(Modifier.size(10.dp).clip(CircleShape).background(MaterialTheme.colorScheme.primary))
                            Box(Modifier.width(1.dp).height(52.dp).background(MaterialTheme.colorScheme.onSurface.copy(alpha = 0.12f)))
                        }
                        Column(Modifier.weight(1f).clip(RoundedCornerShape(16.dp)).background(MaterialTheme.colorScheme.surface)
                            .border(1.dp, Color.White.copy(alpha = 0.045f), RoundedCornerShape(16.dp)).padding(12.dp),
                            verticalArrangement = Arrangement.spacedBy(3.dp)) {
                            Text(change.title, fontWeight = FontWeight.SemiBold, fontSize = 12.sp)
                            Text(change.detail, fontSize = 11.sp, color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.7f))
                            Text(SimpleDateFormat("dd.MM.yyyy · HH:mm", Locale.getDefault()).format(Date(change.timestamp)), fontSize = 9.sp, color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.48f))
                        }
                    }
                }
            }
        }
    }
}
'''
replace_function("HistoryScreen", "SensorAnalyticsScreen", history_screen)

replace_once(
    '''        item(key = "analytics_intro") {
            Box(''',
    '''        item(key = "analytics_intro") {
            Column(verticalArrangement = Arrangement.spacedBy(9.dp)) {
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    AnalyticsMetric("Датчики", numericSensors.size.toString(), Color(0xFF9C7BFA), Modifier.weight(1f))
                    AnalyticsMetric("Предупреждения", alerts.size.toString(), if (alerts.isEmpty()) Color(0xFF5CCDA6) else Color(0xFFFF6F82), Modifier.weight(1f))
                    AnalyticsMetric("Устройства", devices.size.toString(), Color(0xFF6FB6E9), Modifier.weight(1f))
                }
            Box(''',
    "Analytics summary opening"
)
replace_once(
    '''            }
        }
        item(key = "analytics_alerts_title")''',
    '''            }
            }
        }
        item(key = "analytics_alerts_title")''',
    "Analytics summary close"
)
metric_helper = r'''@Composable
private fun AnalyticsMetric(label: String, value: String, accent: Color, modifier: Modifier = Modifier) {
    Column(
        modifier.clip(RoundedCornerShape(17.dp))
            .background(Brush.linearGradient(listOf(accent.copy(alpha = 0.18f), MaterialTheme.colorScheme.surface)))
            .border(1.dp, accent.copy(alpha = 0.16f), RoundedCornerShape(17.dp))
            .padding(horizontal = 10.dp, vertical = 11.dp),
        verticalArrangement = Arrangement.spacedBy(4.dp)
    ) {
        Text(value, color = accent, fontSize = 19.sp, fontWeight = FontWeight.Bold)
        Text(label, color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.7f), fontSize = 9.sp, maxLines = 1, overflow = TextOverflow.Ellipsis)
    }
}

'''
replace_once("@Composable\nprivate fun SensorHistoryChart(", metric_helper + "@Composable\nprivate fun SensorHistoryChart(", "Analytics metric helper")

replace_once(
    '''        primary = Color(0xFF9565FF).copy(alpha = 0.88f + glassOpacity * 0.12f),
        onPrimary = Color(0xFF171126),
        secondary = Color(0xFF35CFA7).copy(alpha = 0.86f + glassOpacity * 0.14f),
        background = Color(0xFF1B1D26),
        surface = Color(0xFF2D303A).copy(alpha = glassOpacity),
        surfaceVariant = Color(0xFF373A45).copy(alpha = glassOpacity * 0.96f),
        secondaryContainer = Color(0xFF382B5D).copy(alpha = glassOpacity * 0.84f),''',
    '''        primary = Color(0xFF9B70F5),
        onPrimary = Color.White,
        secondary = Color(0xFF58C6AD),
        tertiary = Color(0xFF73B8E8),
        background = Color(0xFF1A1C24),
        surface = Color(0xFF292C36).copy(alpha = glassOpacity),
        surfaceVariant = Color(0xFF343743).copy(alpha = glassOpacity * 0.96f),
        secondaryContainer = Color(0xFF382B5D).copy(alpha = glassOpacity * 0.84f),''',
    "Material dark palette"
)
replace_once(
    '''        shapes = MaterialTheme.shapes.copy(
            medium = RoundedCornerShape(18.dp),
            large = RoundedCornerShape(22.dp)
        )''',
    '''        shapes = MaterialTheme.shapes.copy(
            small = RoundedCornerShape(11.dp),
            medium = RoundedCornerShape(17.dp),
            large = RoundedCornerShape(22.dp)
        )''',
    "Material shape system"
)
replace_once('listOf(Color(0xFF22242D), Color(0xFF292B36), Color(0xFF20232C))',
             'listOf(Color(0xFF30323D), Color(0xFF282B35), Color(0xFF242731))',
             "Floating navigation gradient")
replace_once(
    '.padding(horizontal = 16.dp, vertical = 7.dp)\n                            .clip(RoundedCornerShape(28.dp))',
    '.padding(horizontal = 12.dp, vertical = 6.dp)\n                            .clip(RoundedCornerShape(25.dp))\n                            .border(1.dp, Color.White.copy(alpha = 0.075f), RoundedCornerShape(25.dp))',
    "Floating navigation border"
)
replace_once('icon = { SmartGlyph("home", Modifier.size(22.dp)', 'icon = { SmartGlyph("home", Modifier.size(23.dp)', "Home nav icon")
replace_once('label = { Text("Дом", maxLines = 1) }', 'label = { Text("Мой дом", maxLines = 1, fontSize = 10.sp) }', "Home nav label")
replace_once('label = { Text("Группы", maxLines = 1) }', 'label = { Text("Группы", maxLines = 1, fontSize = 10.sp) }', "Groups nav label")
replace_once('label = { Text("Сценарии", maxLines = 1) }', 'label = { Text("Сценарии", maxLines = 1, fontSize = 10.sp) }', "Scenarios nav label")
replace_once('label = { Text("Аналитика", maxLines = 1) }', 'label = { Text("Датчики", maxLines = 1, fontSize = 10.sp) }', "Analytics nav label")
replace_once(
    '''    val weatherArtworkSize = when (weatherCardSize) { "small" -> 54.dp; "large" -> 88.dp; else -> 68.dp }
    val weatherTemperatureSize = when (weatherCardSize) { "small" -> 28.sp; "large" -> 38.sp; else -> 32.sp }''',
    '''    val weatherArtworkSize = when (weatherCardSize) { "small" -> 42.dp; "large" -> 62.dp; else -> 50.dp }
    val weatherTemperatureSize = when (weatherCardSize) { "small" -> 24.sp; "large" -> 31.sp; else -> 27.sp }''',
    "Compact weather dimensions"
)
replace_once('listOf(Color(0xFF302D3D), Color(0xFF292D37))',
             'listOf(Color(0xFF343541), Color(0xFF292D37))',
             "Scenario card palette")

settings_start = '    Column(modifier = Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {'
settings_text = '''    Column(modifier = Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(horizontal = 15.dp, vertical = 11.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
        Column(verticalArrangement = Arrangement.spacedBy(2.dp)) {
            Text("ПЕРСОНАЛИЗАЦИЯ И СИСТЕМА", color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.52f), fontSize = 9.sp, fontWeight = FontWeight.Bold, letterSpacing = 1.15.sp)
            Text("Приложение и дом", fontSize = 19.sp, fontWeight = FontWeight.Bold)
        }'''
pos = text.find('private fun SettingsScreen(')
idx = text.find(settings_start, pos)
if idx < 0: raise SystemExit("Settings screen column anchor missing")
text = text[:idx] + settings_text + text[idx + len(settings_start):]
card_old = 'Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)) {'
card_new = 'Card(shape = RoundedCornerShape(20.dp), modifier = Modifier.fillMaxWidth().border(1.dp, Color.White.copy(alpha = 0.055f), RoundedCornerShape(20.dp)), colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)) {'
text = text.replace(card_old, card_new)
replace_once(
    'fontSize = 25.sp, fontWeight = FontWeight.Bold\n                        )',
    'fontSize = 23.sp, fontWeight = FontWeight.ExtraBold, letterSpacing = (-0.35).sp\n                        )',
    "Root title style"
)
text = text.replace('Text("⚙", fontSize = 21.sp)', 'Text("⚙", fontSize = 20.sp, color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.86f))')

text = text.rstrip() + "\n\n" + MARKER + "\n"
source.write_text(text, encoding="utf-8")
print("Applied full redesign to groups, history, analytics, settings and navigation.")
