#!/usr/bin/env python3
"""Polish the shipped Compose dashboard without changing device APIs."""
from pathlib import Path
import sys

source = Path(sys.argv[1])
main = source.read_text(encoding="utf-8")
marker = "// UI-REFINED-1.5.2"

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
                                    when {
                                        offline -> Color(0xFF4A4650)
                                        on -> Color(0xFF8059E8)
                                        else -> Color(0xFF414653)
                                    }
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
print("Applied the 1.5.2 device-card, home-navigation and scenario polish.")
