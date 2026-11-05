#!/usr/bin/env python3
from pathlib import Path
import hashlib, tempfile, zipfile

archive = Path("YandexHomeWidgets_source.zip")
main_path = "app/src/main/java/ru/dislive/yandexhomewidgets/MainActivity.kt"

with zipfile.ZipFile(archive, "r") as zin:
    infos = zin.infolist()
    files = {info.filename: zin.read(info.filename) for info in infos}

src = files[main_path].decode("utf-8")

def block(text, marker):
    start = text.find(marker)
    if start < 0:
        raise SystemExit(f"Missing protected block marker: {marker}")
    brace = text.find("{", start)
    if brace < 0:
        raise SystemExit(f"Missing opening brace: {marker}")
    depth = 0
    in_string = False
    escaped = False
    for i in range(brace, len(text)):
        ch = text[i]
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start:i+1]
    raise SystemExit(f"Unbalanced block: {marker}")

protected = {
    "tile_power": block(src, "if (device.canToggle) {"),
    "device_details": block(src, "private fun DeviceDetailsScreen("),
    "group_power": block(src, "private fun GroupGridHeader("),
}

def replace_once(old, new, label):
    global src
    count = src.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one match, got {count}")
    src = src.replace(old, new, 1)

replace_once(
    "val fittingColumns = ((availableWidth + 10.dp) / 126.dp).toInt().coerceIn(1, 3)",
    "val minimumCardWidth = maxOf(126, cardWidthDp).dp\n        val fittingColumns = ((availableWidth + 10.dp) / (minimumCardWidth + 10.dp)).toInt().coerceIn(1, 3)",
    "responsive column threshold"
)
replace_once(
    "else (cardWidthDp * 0.40f).coerceIn(52f, 104f).dp",
    "else (maxWidth.value * 0.40f).coerceIn(52f, 104f).dp",
    "tile icon scaling"
)

text_replacements = [
    ('Text("ПОГОДА РЯДОМ", color = Color.White.copy(alpha = 0.72f)', 'Text("ПОГОДА РЯДОМ", color = Color.White.copy(alpha = 0.84f)'),
    ('Text("Сейчас", color = Color.White.copy(alpha = 0.67f)', 'Text("Сейчас", color = Color.White.copy(alpha = 0.84f)'),
    ('Text("ВЕТЕР", color = Color.White.copy(alpha = 0.62f)', 'Text("ВЕТЕР", color = Color.White.copy(alpha = 0.82f)'),
    ('Text("ВЛАЖНОСТЬ", color = Color.White.copy(alpha = 0.62f)', 'Text("ВЛАЖНОСТЬ", color = Color.White.copy(alpha = 0.82f)'),
    ('Text("ОСАДКИ", color = Color.White.copy(alpha = 0.62f)', 'Text("ОСАДКИ", color = Color.White.copy(alpha = 0.82f)'),
    ('color = if (offline) Color(0xFFFF5968) else Color.White.copy(alpha = 0.62f),', 'color = if (offline) Color(0xFFFF5968) else Color.White.copy(alpha = 0.84f),'),
]
for old, new in text_replacements:
    replace_once(old, new, "dark theme text contrast")

after_protected = {
    "tile_power": block(src, "if (device.canToggle) {"),
    "device_details": block(src, "private fun DeviceDetailsScreen("),
    "group_power": block(src, "private fun GroupGridHeader("),
}
for name in protected:
    if hashlib.sha256(protected[name].encode()).hexdigest() != hashlib.sha256(after_protected[name].encode()).hexdigest():
        raise SystemExit(f"Protected power/UI block changed unexpectedly: {name}")

files[main_path] = src.encode("utf-8")
with tempfile.NamedTemporaryFile(prefix="yhw-1.5.0-", suffix=".zip", dir=archive.parent, delete=False) as tmp:
    temp_path = Path(tmp.name)
with zipfile.ZipFile(temp_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zout:
    for info in infos:
        zout.writestr(info, files[info.filename])
temp_path.replace(archive)

print("Updated responsive card width threshold and tile content scaling.")
print("Raised contrast of secondary weather/device text in dark theme.")
print("Verified unchanged power blocks: tile power, device details, group power.")
