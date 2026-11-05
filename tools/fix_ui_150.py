#!/usr/bin/env python3
from pathlib import Path
import sys, tempfile, zipfile

archive = Path(sys.argv[1])

def once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one match, got {count}")
    return text.replace(old, new, 1)

with tempfile.TemporaryDirectory(prefix="yhw-ui-150-fix-") as td:
    root = Path(td) / "src"
    root.mkdir()
    with zipfile.ZipFile(archive) as zf:
        zf.extractall(root)

    main_path = root / "app/src/main/java/ru/dislive/yandexhomewidgets/MainActivity.kt"
    main = main_path.read_text(encoding="utf-8")
    old_padding = '.clickable(onClick = onOpen).padding(horizontal = tileHorizontalPadding, vertical = if (cardSize == "small") 8.dp else 12.dp)'
    new_padding = '.clickable(onClick = onOpen).padding(horizontal = if (cardSize == "large") 12.dp else 8.dp, vertical = if (cardSize == "small") 8.dp else 12.dp)'
    main = once(main, old_padding, new_padding, "tile modifier padding")
    main_path.write_text(main, encoding="utf-8")

    scenario_path = root / "app/src/main/java/ru/dislive/yandexhomewidgets/ScenarioCenter.kt"
    scenario = scenario_path.read_text(encoding="utf-8")
    required_imports = [
        "import androidx.compose.foundation.layout.PaddingValues",
        "import androidx.compose.foundation.layout.fillMaxHeight",
        "import androidx.compose.material3.Divider",
    ]
    missing = [line for line in required_imports if line not in scenario]
    if missing:
        lines = scenario.splitlines()
        import_indices = [i for i, line in enumerate(lines) if line.startswith("import ")]
        if not import_indices:
            raise SystemExit("ScenarioCenter.kt import section not found")
        insert_at = max(import_indices) + 1
        lines[insert_at:insert_at] = missing
        scenario = "\n".join(lines) + "\n"
    scenario_path.write_text(scenario, encoding="utf-8")

    version = (root / "VERSION.txt").read_text(encoding="utf-8").strip()
    if version != "1.5.0":
        raise SystemExit(f"Expected source version 1.5.0, found {version}")
    gradle = (root / "app/build.gradle.kts").read_text(encoding="utf-8")
    if 'versionName = "1.5.0"' not in gradle:
        raise SystemExit("Gradle versionName is not 1.5.0")

    out = archive.with_suffix(".new.zip")
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in sorted(root.rglob("*")):
            if path.is_file():
                zf.write(path, path.relative_to(root))
    out.replace(archive)
    print("Fixed device tile padding scope.")
    print("Added missing Compose layout/Material imports in ScenarioCenter.kt.")
    print("Confirmed VERSION.txt and Gradle both remain 1.5.0.")
