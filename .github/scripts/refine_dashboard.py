#!/usr/bin/env python3
"""Polish the shipped Compose dashboard without changing device APIs."""
from pathlib import Path
import sys

source = Path(sys.argv[1])
main = source.read_text(encoding="utf-8")
main = main.replace("// UI-REFINED-1.5.2", "")
marker = "// UI-REFINED-1.5.3"

if marker in main:
    print("Dashboard UI 1.5.2 already refined.")
    raise SystemExit(0)

tile_start = "@Composable\nprivate fun CompactDeviceTile("
tile_end = "\nprivate fun deviceIcon(type:"
start = main.find(tile_start)
end = main.find(tile_end, start)
if start < 0 or end <= start:
    raise SystemExit("Could not locate CompactDeviceTile")

tile = r'''@Composable
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
    val tileGradient = when { offline -> listOf(Color(0xFF44313F), Color(0xFF2B303C)); on -> listOf(Color(0xFF493773), Color(0xFF2C405B), Color(0xFF29313F)); else -> listOf(Color(0xFF354557), Color(0xFF2A303D), Color(0xFF252B35)) }
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
                .clip(cardShape).background(Brush.linearGradient(colors = tileGradient, start = Offset.Zero, end = Offset(520f, 720f))).border(1.dp, outline, cardShape)
                .clickable(onClick = onOpen)
                .padding(if (cardSize == "large") 15.dp else 13.dp)
        ) {
            Column(Modifier.fillMaxSize(), verticalArrangement = Arrangement.SpaceBetween) {
                Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                    Box(
                        Modifier.size(iconSize + 8.dp).clip(RoundedCornerShape(19.dp))
                            .background(
                                if (offline) Color.White.copy(alpha = 0.045f)
                                else if (on) Color(0xFF9B7BFA).copy(alpha = 0.15f)
                                else Color.White.copy(alpha = 0.055f)
                            ),
                        contentAlignment = Alignment.Center
                    ) {
                        SmartGlyph(
                            deviceIconKind(device.type, device.name),
                            Modifier.size(iconSize),
                            if (offline) Color(0xFF9298A5) else if (on) Color(0xFFD2C2FF) else Color(0xFFB8BFCC)
                        )
                    }
                    Spacer(Modifier.weight(1f))
                    Box(
                        Modifier.size(36.dp).clip(CircleShape)
                            .background(Color.White.copy(alpha = 0.055f))
                            .clickable { onFavorite(!device.isFavorite) },
                        contentAlignment = Alignment.Center
                    ) {
                        Text(
                            if (device.isFavorite) "★" else "☆",
                            color = if (device.isFavorite) Color(0xFFFFD166) else Color.White.copy(alpha = 0.56f),
                            fontSize = 19.sp
                        )
                    }
                }

                Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                    Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                        Text(
                            device.name,
                            color = Color(0xFFF3F4F8),
                            fontWeight = FontWeight.Bold,
                            fontSize = titleSize,
                            maxLines = 1,
                            overflow = TextOverflow.Ellipsis
                        )
                        Row(
                            Modifier.fillMaxWidth(),
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(6.dp)
                        ) {
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
                                fontSize = 10.sp,
                                fontWeight = if (offline || on) FontWeight.SemiBold else FontWeight.Normal,
                                maxLines = 1,
                                overflow = TextOverflow.Ellipsis,
                                modifier = Modifier.weight(1f)
                            )
                        }
                        if (device.room.isNotBlank()) {
                            Text(
                                device.room,
                                color = Color.White.copy(alpha = 0.44f),
                                fontSize = 9.sp,
                                maxLines = 1,
                                overflow = TextOverflow.Ellipsis
                            )
                        }
                    }
                    if (device.canToggle) {
                        Spacer(Modifier.width(9.dp))
                        Box(
                            Modifier.size(powerSize).clip(CircleShape)
                                .background(
                                    Brush.linearGradient(
                                        colors = when {
                                            offline -> listOf(Color(0xFF55404C), Color(0xFF3C3C4A))
                                            on -> listOf(Color(0xFFAA72FF), Color(0xFF6846C4))
                                            else -> listOf(Color(0xFF53677F), Color(0xFF39485B))
                                        },
                                        start = Offset.Zero,
                                        end = Offset(180f, 180f)
                                    )
                                )
                                .clickable(enabled = enabled && !offline) { onToggle(!on) },
                            contentAlignment = Alignment.Center
                        ) {
                            if (pending) {
                                CircularProgressIndicator(Modifier.size(19.dp), strokeWidth = 2.dp, color = Color.White)
                            } else {
                                SmartGlyph(if (on) "off" else "power", Modifier.size(24.dp), Color.White)
                            }
                        }
                    }
                }
            }
        }
    }
}
'''
main = main[:start] + tile + main[end:]

# Remove repeated home content and replace global light/outlet switches with contextual navigation.
def replace_kotlin_block(text, anchor, replacement):
    position = text.find(anchor)
    if position < 0:
        raise SystemExit("Could not locate Kotlin block: " + anchor)
    line_start = text.rfind("\\n", 0, position) + 1
    opening = text.find("{", position)
    if opening < 0:
        raise SystemExit("Kotlin block has no opening brace: " + anchor)
    depth = 0
    for index in range(opening, len(text)):
        if text[index] == "{":
            depth += 1
        elif text[index] == "}":
            depth -= 1
            if depth == 0:
                end = index + 1
                if end < len(text) and text[end] == "\\n":
                    end += 1
                return text[:line_start] + replacement + text[end:]
    raise SystemExit("Could not find closing brace for Kotlin block: " + anchor)

main = replace_kotlin_block(
    main,
    'if (favoriteDevices.isNotEmpty() && selectedCategory == "Все") {',
    ''
)
main = replace_kotlin_block(
    main,
    'item(span = { GridItemSpan(maxLineSpan) }, key = "home_actions") {',
    '''        item(span = { GridItemSpan(maxLineSpan) }, key = "home_actions") {
            Row(
                Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                HomeQuickButton("Группы", Color(0xFF9B7BFA), onOpenGroups, Modifier.widthIn(min = 112.dp))
                HomeQuickButton("Аналитика", Color(0xFF52C9B0), onAnalytics, Modifier.widthIn(min = 112.dp))
            }
        }'''
)
main = main.replace(
    '                        Text(activeCount.toString() + " включено · " + onlineCount + " в сети из " + devices.size, color = Color.White.copy(alpha = 0.76f), fontSize = 11.sp, maxLines = 1, overflow = TextOverflow.Ellipsis)
',
    ''
)
main = main.replace(
    '.background(Color.White.copy(alpha = 0.075f))',
    '.background(Brush.linearGradient(listOf(Color(0xFF7654B8).copy(alpha = 0.34f), Color(0xFF32627C).copy(alpha = 0.30f))))',
    1
)
main = main.replace(
    'Brush.linearGradient(listOf(Color(0xFF302B42), Color(0xFF242C3A), Color(0xFF202D35)))',
    'Brush.linearGradient(listOf(Color(0xFF493568), Color(0xFF2D4660), Color(0xFF203B43)))',
    1
)

# Do not count an unreachable offline device as currently switched on.
main = main.replace(
    "val activeCount = devices.count { it.onOff == true }",
    "val activeCount = devices.count { it.isOnline && it.onOff == true }",
    1
)

# Keep the Home destination highlighted while a device or room detail is open.
main = main.replace(
    "selected = page == AppPage.HOME,",
    "selected = page in setOf(AppPage.HOME, AppPage.DEVICE, AppPage.GROUP_DETAILS, AppPage.ANALYTICS),",
    1
)

# Make scenarios feel part of the same visual system, with a clear run action.
main = main.replace(
    'if (index % 2 == 0) listOf(Color(0xFF192A40), Color(0xFF1C3446))\n                            else listOf(Color(0xFF25223F), Color(0xFF1D3042))',
    'if (index % 2 == 0) listOf(Color(0xFF302D3D), Color(0xFF292D37))\n                            else listOf(Color(0xFF26363A), Color(0xFF282C36))',
    1
)
main = main.replace(
    'containerColor = Color(0xFF8B5CF6).copy(alpha = 0.22f)',
    'containerColor = Color(0xFF9B7BFA).copy(alpha = 0.18f)',
    1
)
main = main.replace(
    'Button(\n                    onClick = { onRun(scenario) },\n                    enabled = !isBusy,\n                    shape = RoundedCornerShape(13.dp),\n                    contentPadding = PaddingValues(horizontal = 12.dp, vertical = 8.dp)\n                ) { Text("Запустить", fontSize = 10.sp, fontWeight = FontWeight.Bold) }',
    'Button(\n                    onClick = { onRun(scenario) },\n                    enabled = !isBusy,\n                    shape = RoundedCornerShape(14.dp),\n                    contentPadding = PaddingValues(horizontal = 15.dp, vertical = 9.dp),\n                    colors = ButtonDefaults.buttonColors(\n                        containerColor = Color(0xFF8059E8),\n                        contentColor = Color.White,\n                        disabledContainerColor = Color(0xFF514B60),\n                        disabledContentColor = Color.White.copy(alpha = 0.58f)\n                    )\n                ) { Text("Запустить", fontSize = 11.sp, fontWeight = FontWeight.Bold) }',
    1
)

# Add the completion marker so the workflow does not apply the redesign twice.
main = main.rstrip() + "\n\n" + marker + "\n"
source.write_text(main, encoding="utf-8")
print("Applied the 1.5.3 gradient dashboard redesign, duplicate cleanup and contextual controls.")
