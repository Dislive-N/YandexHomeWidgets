#!/usr/bin/env python3
from pathlib import Path
import sys, tempfile, zipfile

archive = Path(sys.argv[1])
with tempfile.TemporaryDirectory(prefix="yhw-version-fix-") as tmp:
    root = Path(tmp) / "src"
    root.mkdir()
    with zipfile.ZipFile(archive) as zf:
        zf.extractall(root)
    gradle = root / "app/build.gradle.kts"
    text = gradle.read_text(encoding="utf-8")
    old = 'versionName = "1.4.8"'
    new = 'versionName = "1.4.9"'
    if text.count(old) != 1:
        raise SystemExit(f"Expected one hard-coded versionName 1.4.8, found {text.count(old)}")
    gradle.write_text(text.replace(old, new, 1), encoding="utf-8")
    if (root / "VERSION.txt").read_text(encoding="utf-8").strip() != "1.4.9":
        raise SystemExit("VERSION.txt and Gradle versionName are inconsistent")
    out = archive.with_suffix(".new.zip")
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in sorted(root.rglob("*")):
            if path.is_file():
                zf.write(path, path.relative_to(root))
    out.replace(archive)
print("Gradle versionName synchronized to 1.4.9.")
