#!/usr/bin/env python3
from pathlib import Path
import hashlib
import re
import sys
import zipfile
import tempfile

archive_path = Path(sys.argv[1])
with tempfile.TemporaryDirectory(prefix="yandex-home-glass-") as tmp:
    root = Path(tmp) / "project"
    root.mkdir()
    with zipfile.ZipFile(archive_path, "r") as zf:
        zf.extractall(root)

    main_path = root / "app/src/main/java/ru/dislive/yandexhomewidgets/MainActivity.kt"
    main = main_path.read_text(encoding="utf-8")

    def require_once(source: str, old: str, new: str, label: str) -> str:
        count = source.count(old)
        if count != 1:
            raise SystemExit(f"{label}: expected exactly one match, got {count}")
        return source.replace(old, new, 1)

    # Snapshot the actual device power-control blocks and command handler.
    protected_patterns = {
        "compact_power_button": re.compile(
            r'(?ms)^                if \(device\.canToggle\) \{\n'
            r'                    Box\(\n'
            r'                        modifier = Modifier\.size\(powerSize\).*?^\s{16}\}'
        ),
        "detail_power_button": re.compile(
            r'(?ms)^                if \(device\.canToggle\) \{\n'
            r'                    Button\(onClick = \{ onToggle\(device\.onOff != true\) \}.*?^\s{16}\}'
        ),
        "group_power_button": re.compile(
            r'(?ms)^        OutlinedButton\(\n'
            r'            onClick = \{ onToggleGroup\(switchable, !allOn\) \}.*?^\s{8}\}'
        ),
        "perform_on_off": re.compile(
            r'(?ms)^    fun performOnOff\(deviceIds: List<String>, value: Boolean\) \{.*?^\s{4}\}'
        ),
    }
    protected = {}
    for name, pattern in protected_patterns.items():
        match = pattern.search(main)
        if not match:
            raise SystemExit(f"Could not locate protected power-control section: {name}")
        protected[name] = hashlib.sha256(match.group(0).encode("utf-8")).hexdigest()

    old_theme = """    val colors = if (isDarkTheme) darkColorScheme(
        primary = Color(0xFFB5A0FF).copy(alpha = 0.78f + glassOpacity * 0.20f),
        onPrimary = Color(0xFF171126),
        secondary = Color(0xFF8E77E4).copy(alpha = 0.72f + glassOpacity * 0.24f),
        background = Color(0xFF080B15),
        surface = Color(0xFF1B2031).copy(alpha = glassOpacity),
        surfaceVariant = Color(0xFF333A52).copy(alpha = glassOpacity * 0.84f),
        secondaryContainer = Color(0xFF443965).copy(alpha = glassOpacity * 0.78f),
        onSurface = Color(0xFFF5F2FF),
        onBackground = Color(0xFFF5F2FF)
    ) else lightColorScheme(
        primary = Color(0xFF7546C8).copy(alpha = glassOpacity),
        onPrimary = Color.White,
        secondary = Color(0xFF9A6AE8),
        background = Color(0xFFF4F0FA),
        surface = Color.White.copy(alpha = glassOpacity),
        surfaceVariant = Color(0xFFE6E0F1).copy(alpha = glassOpacity),
        onSurface = Color(0xFF251B36),
        onBackground = Color(0xFF251B36)
    )"""
    new_theme = """    val colors = if (isDarkTheme) darkColorScheme(
        // Keep primary/onPrimary unchanged so existing power actions retain their exact accent.
        primary = Color(0xFFB5A0FF).copy(alpha = 0.78f + glassOpacity * 0.20f),
        onPrimary = Color(0xFF171126),
        secondary = Color(0xFF14B8A6).copy(alpha = 0.86f + glassOpacity * 0.14f),
        background = Color(0xFF070A12),
        surface = Color(0xFF111827).copy(alpha = glassOpacity),
        surfaceVariant = Color(0xFF172033).copy(alpha = glassOpacity * 0.94f),
        secondaryContainer = Color(0xFF173C49).copy(alpha = glassOpacity * 0.82f),
        onSurface = Color(0xFFF1F5F9),
        onBackground = Color(0xFFF1F5F9)
    ) else lightColorScheme(
        // Preserve the original primary accent for all existing power controls.
        primary = Color(0xFF7546C8).copy(alpha = glassOpacity),
        onPrimary = Color.White,
        secondary = Color(0xFF0F9F91),
        background = Color(0xFFF3F7FB),
        surface = Color.White.copy(alpha = glassOpacity),
        surfaceVariant = Color(0xFFEAF0F7).copy(alpha = glassOpacity),
        onSurface = Color(0xFF172033),
        onBackground = Color(0xFF172033)
    )"""
    main = require_once(main, old_theme, new_theme, "Material color scheme")

    main = require_once(
        main,
        "    MaterialTheme(colorScheme = colors) {",
        """    MaterialTheme(
        colorScheme = colors,
        // Round cards, but leave the small button shape untouched (including power buttons).
        shapes = MaterialTheme.shapes.copy(
            medium = RoundedCornerShape(20.dp),
            large = RoundedCornerShape(24.dp)
        )
    ) {""",
        "MaterialTheme wrapper"
    )

    main = require_once(
        main,
        "colors = listOf(Color(0xFF080B15), Color(0xFF17142B), Color(0xFF0C2230), Color(0xFF090D18))",
        "colors = listOf(Color(0xFF070A12), Color(0xFF0C1728), Color(0xFF0B1E29), Color(0xFF070A12))",
        "dark background gradient"
    )
    main = require_once(
        main,
        "colors = listOf(Color(0xFF7650D0).copy(alpha = 0.44f), Color.Transparent)",
        "colors = listOf(Color(0xFF2563EB).copy(alpha = 0.24f), Color.Transparent)",
        "blue background glow"
    )
    main = require_once(
        main,
        "colors = listOf(Color(0xFF167F91).copy(alpha = 0.32f), Color.Transparent)",
        "colors = listOf(Color(0xFF14B8A6).copy(alpha = 0.17f), Color.Transparent)",
        "teal background glow"
    )

    main = require_once(
        main,
        "Brush.linearGradient(listOf(Color(0xFF3B176E), Color(0xFF7545C5), Color(0xFF34205D))),\n                        RoundedCornerShape(24.dp)\n                    ).padding(17.dp)",
        "Brush.linearGradient(listOf(Color(0xFF142B48), Color(0xFF16445A), Color(0xFF12283A))),\n                        RoundedCornerShape(22.dp)\n                    ).border(1.dp, Color.White.copy(alpha = 0.10f), RoundedCornerShape(22.dp)).padding(17.dp)",
        "dashboard summary glass card"
    )
    main = require_once(
        main,
        """colors = listOf(Color(0xFF224D73), Color(0xFF3B5D94), Color(0xFF55467F)),
                            start = Offset.Zero,""",
        """colors = listOf(Color(0xFF13263B), Color(0xFF164252), Color(0xFF1A3045)),
                            start = Offset.Zero,""",
        "weather glass card palette"
    )
    main = require_once(
        main,
        ".clip(RoundedCornerShape(25.dp))\n                    .background(\n                        Brush.linearGradient(",
        ".clip(RoundedCornerShape(22.dp))\n                    .background(\n                        Brush.linearGradient(",
        "weather card radius"
    )
    main = require_once(
        main,
        """                    )
                    .padding(horizontal = 16.dp, vertical = 14.dp)
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {""",
        """                    )
                    .border(1.dp, Color.White.copy(alpha = 0.09f), RoundedCornerShape(22.dp))
                    .padding(horizontal = 16.dp, vertical = 14.dp)
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {""",
        "weather card border"
    )

    main = require_once(main, 'HomeQuickButton("Аналитика", Color(0xFF6754D9),', 'HomeQuickButton("Аналитика", Color(0xFF2563EB),', "analytics quick action")
    main = require_once(main, 'HomeQuickButton("Группы", Color(0xFF168E92),', 'HomeQuickButton("Группы", Color(0xFF0F8E91),', "groups quick action")
    main = require_once(main, "containerColor = Color(0xFF7153C9), contentColor = Color.White", "containerColor = Color(0xFF225C88), contentColor = Color.White", "history quick action")

    main = require_once(
        main,
        ".background(Brush.horizontalGradient(listOf(MaterialTheme.colorScheme.primary.copy(alpha = 0.15f), MaterialTheme.colorScheme.secondary.copy(alpha = 0.08f))), RoundedCornerShape(17.dp))",
        ".background(Brush.horizontalGradient(listOf(Color(0xFF2563EB).copy(alpha = 0.15f), Color(0xFF14B8A6).copy(alpha = 0.09f))), RoundedCornerShape(18.dp))",
        "group header surface"
    )

    old_tile_colors = """    val tileColor = when {
        offline -> Color(0xFF101014).copy(alpha = 0.94f)
        else -> Color(0xFF171720).copy(alpha = 0.82f)
    }"""
    new_tile_colors = """    val tileColor = when {
        offline -> Color(0xFF101820).copy(alpha = 0.96f)
        else -> Color(0xFF111C2B).copy(alpha = 0.92f)
    }"""
    main = require_once(main, old_tile_colors, new_tile_colors, "device tile glass fill")
    main = require_once(
        main,
        """.background(tileColor, RoundedCornerShape(21.dp))
            .border(1.dp, if (offline) Color(0xFF9F3540).copy(alpha = 0.4f) else Color.White.copy(alpha = 0.07f), RoundedCornerShape(21.dp))""",
        """.background(tileColor, RoundedCornerShape(20.dp))
            .border(1.dp, if (offline) Color(0xFFF43F5E).copy(alpha = 0.42f) else Color.White.copy(alpha = 0.10f), RoundedCornerShape(20.dp))""",
        "device tile border"
    )

    main = require_once(
        main,
        "Brush.linearGradient(\n                                    listOf(Color(0xFF130D24), Color(0xFF30205A), Color(0xFF17445C), Color(0xFF0D1B2A))\n                                )",
        "Brush.linearGradient(\n                                    listOf(Color(0xFF101C2B), Color(0xFF142B3A), Color(0xFF101B2A))\n                                )",
        "bottom navigation surface"
    )
    main = require_once(
        main,
        "Brush.linearGradient(listOf(Color(0xFF285B78), Color(0xFF4E65A5), Color(0xFF7658A7)))",
        "Brush.linearGradient(listOf(Color(0xFF142B48), Color(0xFF1A4053), Color(0xFF173043)))",
        "analytics intro card"
    )

    # Confirm power UI and command handling are byte-for-byte unchanged.
    for name, pattern in protected_patterns.items():
        match = pattern.search(main)
        if not match:
            raise SystemExit(f"Protected power-control section disappeared: {name}")
        digest = hashlib.sha256(match.group(0).encode("utf-8")).hexdigest()
        if digest != protected[name]:
            raise SystemExit(f"Power-control section changed unexpectedly: {name}")

    main_path.write_text(main, encoding="utf-8")

    # Align Android system bars with the new dark palette.
    styles_path = root / "app/src/main/res/values/styles.xml"
    styles = styles_path.read_text(encoding="utf-8")
    styles = require_once(styles, '<item name="android:colorAccent">#C4A5FF</item>', '<item name="android:colorAccent">#3B82F6</item>', "Android accent")
    styles = require_once(styles, '<item name="android:statusBarColor">#130B22</item>', '<item name="android:statusBarColor">#070A12</item>', "status bar")
    styles = require_once(styles, '<item name="android:navigationBarColor">#130B22</item>', '<item name="android:navigationBarColor">#070A12</item>', "system navigation bar")
    styles_path.write_text(styles, encoding="utf-8")

    colors_path = root / "app/src/main/res/values/colors.xml"
    colors = colors_path.read_text(encoding="utf-8")
    colors = require_once(colors, '<color name="icon_background">#130B22</color>', '<color name="icon_background">#070A12</color>', "launcher background")
    colors_path.write_text(colors, encoding="utf-8")

    version_path = root / "VERSION.txt"
    old_version = version_path.read_text(encoding="utf-8").strip()
    if old_version != "1.4.8":
        raise SystemExit(f"Expected source version 1.4.8, found {old_version}")
    version_path.write_text("1.4.9\n", encoding="utf-8")

    # Repack from the project root so the Android workflow can find settings.gradle.kts.
    temp_archive = archive_path.with_suffix(".new.zip")
    with zipfile.ZipFile(temp_archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in sorted(root.rglob("*")):
            if path.is_file():
                zf.write(path, path.relative_to(root))
    temp_archive.replace(archive_path)

    print("Applied Lightweight Glassmorphism 2.0.")
    print("Bumped app version: 1.4.8 -> 1.4.9.")
    print("Verified unchanged power UI blocks: " + ", ".join(protected))
    print(f"Updated archive size: {archive_path.stat().st_size} bytes")
