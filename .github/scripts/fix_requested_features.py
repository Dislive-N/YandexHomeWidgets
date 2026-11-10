#!/usr/bin/env python3
import base64
import subprocess
import sys
import zlib
from pathlib import Path
from PIL import Image

PATCH_B64 = """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"""
root = Path(sys.argv[1]).resolve()
marker = root / "app/src/main/java/ru/dislive/yandexhomewidgets/data/LocalAutomation.kt"
if "LOCAL_SCENARIO_DISABLE" not in marker.read_text(encoding="utf-8"):
    patch = zlib.decompress(base64.b64decode(PATCH_B64)).decode("utf-8")
    result = subprocess.run(
        ["patch", "-p0", "--batch", "--forward", "-d", str(root)],
        input=patch, text=True, capture_output=True
    )
    if result.returncode:
        sys.stderr.write(result.stdout + result.stderr)
        raise SystemExit(result.returncode)
    print(result.stdout)
else:
    print("Requested Kotlin source patch already present")

scenario = root / "app/src/main/java/ru/dislive/yandexhomewidgets/ScenarioCenter.kt"
scenario_text = scenario.read_text(encoding="utf-8")
wrong_call = "actionDescription(action, devices, variables, cloudScenarios), Modifier.weight(1f)"
right_call = "actionDescription(action, devices, variables, cloudScenarios, localScenarios), Modifier.weight(1f)"
scenario_text = scenario_text.replace(wrong_call, right_call)
missing_brace = '''                            ) { actionLocalScenario = it }
                        }
                    Row(Modifier.fillMaxWidth().padding(14.dp)'''
with_brace = '''                            ) { actionLocalScenario = it }
                        }
                    }
                    Row(Modifier.fillMaxWidth().padding(14.dp)'''
scenario_text = scenario_text.replace(missing_brace, with_brace)
scenario.write_text(scenario_text, encoding="utf-8")

icon = root / "app/src/main/res/drawable-nodpi/ic_launcher_foreground.webp"
image = Image.open(icon).convert("RGBA")
bounds = image.getchannel("A").getbbox()
if not bounds:
    raise SystemExit("Launcher icon foreground has no visible pixels")
left, top, right, bottom = bounds
if left > 5 or top > 5 or right < image.width - 5 or bottom < image.height - 5:
    bounds = (max(0, left - 3), max(0, top - 3), min(image.width, right + 3), min(image.height, bottom + 3))
    image = image.crop(bounds).resize((432, 432), Image.Resampling.LANCZOS)
    image.save(icon, format="WEBP", quality=96, method=6)
    print("Launcher icon transparent margins cropped")
else:
    print("Launcher icon already fills foreground")

# Fix release-tag parsing. Four backslashes in the Kotlin source produced an
# invalid regex, so same-version builds were treated as build 0 by the updater.
updates_file = root / "app/src/main/java/ru/dislive/yandexhomewidgets/data/AppUpdates.kt"
updates_text = updates_file.read_text(encoding="utf-8")
wrong_version_pattern = r'(?:\\\\.[0-9]+)'
right_version_pattern = r'(?:\\.[0-9]+)'
wrong_build_pattern = r'(\\\\d+)'
right_build_pattern = r'(\\d+)'
wrong_count = updates_text.count(wrong_version_pattern)
wrong_build_count = updates_text.count(wrong_build_pattern)
if wrong_count == 1 and wrong_build_count == 1:
    updates_text = updates_text.replace(wrong_version_pattern, right_version_pattern, 1)
    updates_text = updates_text.replace(wrong_build_pattern, right_build_pattern, 1)
    updates_file.write_text(updates_text, encoding="utf-8")
    print("Fixed GitHub release version/build parsing in AppUpdates.kt")
elif wrong_count == 0 and wrong_build_count == 0 and updates_text.count(right_version_pattern) == 1 and updates_text.count(right_build_pattern) == 1:
    print("GitHub release version/build parsing already fixed")
else:
    raise SystemExit(
        "Unexpected AppUpdates.kt release regex state: "
        f"version_old={wrong_count}, build_old={wrong_build_count}, "
        f"version_fixed={updates_text.count(right_version_pattern)}, "
        f"build_fixed={updates_text.count(right_build_pattern)}"
    )



# HOME-WIDGETS-NAV-AUTO-1.8.3: theme, navigation, responsive columns and event widget.
main_activity = root / "app/src/main/java/ru/dislive/yandexhomewidgets/MainActivity.kt"
manifest = root / "app/src/main/AndroidManifest.xml"
strings = root / "app/src/main/res/values/strings.xml"
widget_dir = root / "app/src/main/java/ru/dislive/yandexhomewidgets/widget"
widget_xml = root / "app/src/main/res/xml/notifications_widget_info.xml"
main_text = main_activity.read_text(encoding="utf-8")
marker = "// HOME-WIDGETS-NAV-AUTO-1.8.3"

def replace_unique(source, old, new, label):
    count = source.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one anchor, found {count}")
    return source.replace(old, new, 1)

if marker not in main_text:
    main_text = replace_unique(
        main_text,
        "Surface(modifier = Modifier.fillMaxSize(), color = Color.Transparent)",
        "Surface(modifier = Modifier.fillMaxSize(), color = Color.Transparent, contentColor = MaterialTheme.colorScheme.onSurface)",
        "dark theme root text color"
    )
    main_text = replace_unique(
        main_text,
        "private enum class AppPage { HOME, DEVICES, SCENARIOS, AUTOMATIONS, PROFILE, HISTORY, ANALYTICS, SETTINGS, DEVICE, GROUPS, GROUP_DETAILS }",
        "private enum class AppPage { HOME, DEVICES, SCENARIOS, AUTOMATIONS, HISTORY, ANALYTICS, SETTINGS, DEVICE, GROUPS, GROUP_DETAILS }",
        "remove Profile page"
    )
    main_text = replace_unique(main_text, '                                AppPage.PROFILE -> "Профиль"\n', "", "remove Profile title")
    old_actions = '''                    if (isConnected && page in setOf(AppPage.HOME, AppPage.DEVICES)) {
                        TextButton(onClick = { history = HomeHistoryStore.load(context); page = AppPage.HISTORY }, contentPadding = PaddingValues(horizontal = 4.dp, vertical = 4.dp)) {
                            SmartGlyph("clock", Modifier.size(21.dp), MaterialTheme.colorScheme.primary)
                        }
                        TextButton(onClick = { if (!isBusy && !isSyncing) scope.launch { reloadHome() } }, enabled = !isBusy && !isSyncing, contentPadding = PaddingValues(horizontal = 4.dp, vertical = 4.dp)) {
                            if (isSyncing) CircularProgressIndicator(Modifier.size(19.dp), strokeWidth = 2.dp)
                            else Text("↻", fontSize = 25.sp, color = MaterialTheme.colorScheme.primary)
                        }
                        TextButton(onClick = { page = AppPage.PROFILE }, contentPadding = PaddingValues(horizontal = 4.dp, vertical = 4.dp)) { SmartGlyph("user", Modifier.size(21.dp), MaterialTheme.colorScheme.primary) }
                    } else if (page in setOf(AppPage.SCENARIOS, AppPage.AUTOMATIONS, AppPage.PROFILE)) {
                        if (page != AppPage.PROFILE) TextButton(onClick = { page = AppPage.PROFILE }) { SmartGlyph("user", Modifier.size(21.dp), MaterialTheme.colorScheme.primary) }
                        else TextButton(onClick = { page = AppPage.SETTINGS }) { SmartGlyph("settings", Modifier.size(21.dp), MaterialTheme.colorScheme.primary) }
                    } else {
                        TextButton(onClick = {
                            if (page == AppPage.GROUP_DETAILS) page = AppPage.GROUPS
                            else { page = AppPage.HOME; selectedDeviceId = null; selectedGroupId = null }
                        }) { Text("← Назад") }
                    }'''
    new_actions = '''                    if (page in setOf(AppPage.HOME, AppPage.DEVICES)) {
                        if (isConnected) {
                            TextButton(onClick = { history = HomeHistoryStore.load(context); page = AppPage.HISTORY }, contentPadding = PaddingValues(horizontal = 4.dp, vertical = 4.dp)) {
                                SmartGlyph("clock", Modifier.size(21.dp), MaterialTheme.colorScheme.primary)
                            }
                            TextButton(onClick = { if (!isBusy && !isSyncing) scope.launch { reloadHome() } }, enabled = !isBusy && !isSyncing, contentPadding = PaddingValues(horizontal = 4.dp, vertical = 4.dp)) {
                                if (isSyncing) CircularProgressIndicator(Modifier.size(19.dp), strokeWidth = 2.dp)
                                else Text("↻", fontSize = 25.sp, color = MaterialTheme.colorScheme.primary)
                            }
                        }
                        TextButton(onClick = { page = AppPage.SETTINGS }, contentPadding = PaddingValues(horizontal = 4.dp, vertical = 4.dp)) {
                            SmartGlyph("settings", Modifier.size(21.dp), MaterialTheme.colorScheme.primary)
                        }
                    } else if (page in setOf(AppPage.SCENARIOS, AppPage.AUTOMATIONS, AppPage.ANALYTICS, AppPage.HISTORY)) {
                        TextButton(onClick = { page = AppPage.SETTINGS }, contentPadding = PaddingValues(horizontal = 4.dp, vertical = 4.dp)) {
                            SmartGlyph("settings", Modifier.size(21.dp), MaterialTheme.colorScheme.primary)
                        }
                    } else {
                        TextButton(onClick = {
                            if (page == AppPage.GROUP_DETAILS) page = AppPage.GROUPS
                            else { page = AppPage.HOME; selectedDeviceId = null; selectedGroupId = null }
                        }) { Text("← Назад") }
                    }'''
    main_text = replace_unique(main_text, old_actions, new_actions, "top-right Settings action")
    profile_branch = '''                            AppPage.PROFILE -> ProfileScreen(
                                isConnected = isConnected,
                                deviceCount = devices.size,
                                roomCount = roomNames.size,
                                onOpenSettings = { page = AppPage.SETTINGS },
                                onOpenGroups = { page = AppPage.GROUPS },
                                onOpenHistory = { history = HomeHistoryStore.load(context); page = AppPage.HISTORY },
                                onOpenAnalytics = { page = AppPage.ANALYTICS }
                            )
'''
    main_text = replace_unique(main_text, profile_branch, "", "remove Profile route")
    main_text = main_text.replace(
        "AppPage.AUTOMATIONS, AppPage.PROFILE, AppPage.HISTORY",
        "AppPage.AUTOMATIONS, AppPage.HISTORY"
    )
    old_nav = '''                        NavigationBarItem(
                            selected = page in setOf(AppPage.PROFILE, AppPage.SETTINGS, AppPage.ANALYTICS),
                            onClick = { page = AppPage.PROFILE },
                            icon = { SmartGlyph("user", Modifier.size(21.dp), if (page in setOf(AppPage.PROFILE, AppPage.SETTINGS, AppPage.ANALYTICS)) selectedColor else idleColor) },
                            label = { Text("Профиль", maxLines = 1, fontSize = 9.sp) },
                            colors = NavigationBarItemDefaults.colors(selectedIconColor = selectedColor, selectedTextColor = selectedColor, unselectedIconColor = idleColor, unselectedTextColor = idleColor, indicatorColor = selectedColor.copy(alpha = 0.13f))
                        )'''
    new_nav = '''                        NavigationBarItem(
                            selected = page == AppPage.ANALYTICS,
                            onClick = { page = AppPage.ANALYTICS },
                            icon = { SmartGlyph("chart", Modifier.size(21.dp), if (page == AppPage.ANALYTICS) selectedColor else idleColor) },
                            label = { Text("Аналитика", maxLines = 1, fontSize = 9.sp) },
                            colors = NavigationBarItemDefaults.colors(selectedIconColor = selectedColor, selectedTextColor = selectedColor, unselectedIconColor = idleColor, unselectedTextColor = idleColor, indicatorColor = selectedColor.copy(alpha = 0.13f))
                        )'''
    main_text = replace_unique(main_text, old_nav, new_nav, "replace Profile tab with Analytics")
    main_text = replace_unique(
        main_text,
        'var deviceColumns by remember { mutableStateOf(config.getInt("device_columns", 3).coerceIn(1, 3)) }',
        'var deviceColumns by remember { mutableStateOf(config.getInt("device_columns", 0).coerceIn(0, 3)) }',
        "automatic grid default"
    )
    main_text = replace_unique(
        main_text,
        'onDeviceColumnsChange = { deviceColumns = it.coerceIn(1, 3); config.edit().putInt("device_columns", deviceColumns).apply() },',
        'onDeviceColumnsChange = { deviceColumns = it.coerceIn(0, 3); config.edit().putInt("device_columns", deviceColumns).apply() },',
        "automatic grid save"
    )
    main_text = main_text.replace(
        'val effectiveColumns = deviceColumns.coerceIn(1, 3).coerceAtMost(fittingColumns)',
        'val effectiveColumns = if (deviceColumns == 0) fittingColumns else deviceColumns.coerceIn(1, 3).coerceAtMost(fittingColumns)'
    )
    if main_text.count("if (deviceColumns == 0) fittingColumns") != 2:
        raise SystemExit("Automatic column calculation must exist on both device grids")
    main_text = replace_unique(
        main_text,
        'Text("Можно выбрать до трёх колонок. На узком экране сетка сама уменьшит число колонок, а карточки займут всю доступную ширину.", fontSize = 11.sp, color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.78f))',
        'Text("Авто подбирает максимально возможное число колонок (до трёх) по ширине экрана и размеру карточек. Можно также зафиксировать 1, 2 или 3 колонки.", fontSize = 11.sp, color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.78f))',
        "automatic grid description"
    )
    main_text = replace_unique(
        main_text,
        'listOf(1, 2, 3).forEach { count -> FilterChip(selected = deviceColumns == count, onClick = { onDeviceColumnsChange(count) }, label = { Text(count.toString()) }) }',
        'listOf(0, 1, 2, 3).forEach { count -> FilterChip(selected = deviceColumns == count, onClick = { onDeviceColumnsChange(count) }, label = { Text(if (count == 0) "Авто" else count.toString()) }) }',
        "automatic grid selector"
    )
    main_text = main_text.replace(
        'import ru.dislive.yandexhomewidgets.widget.HomeWidget\n',
        'import ru.dislive.yandexhomewidgets.widget.HomeWidget\nimport ru.dislive.yandexhomewidgets.widget.NotificationsWidget\n',
        1
    )
    main_text = replace_unique(
        main_text,
        '            HomeWidget().updateAll(context)\n            ScenarioWidget().updateAll(context)',
        '            HomeWidget().updateAll(context)\n            ScenarioWidget().updateAll(context)\n            NotificationsWidget().updateAll(context)',
        "refresh notification widget"
    )
    main_text = replace_unique(
        main_text,
        'history = history,\n                                onClear = { HomeHistoryStore.clear(context); history = emptyList() }',
        'history = history,\n                                onClear = { HomeHistoryStore.clear(context); history = emptyList(); scope.launch { NotificationsWidget().updateAll(context) } }',
        "clear notification widget"
    )
    main_text = main_text.rstrip() + "\n\n" + marker + "\n"
    main_activity.write_text(main_text, encoding="utf-8")

# Update the periodic background refresh, without redundant same-package imports.
worker = root / "app/src/main/java/ru/dislive/yandexhomewidgets/widget/SyncWorker.kt"
worker_text = worker.read_text(encoding="utf-8")
worker_marker = "// NOTIFICATIONS-WIDGET-SYNC-1.8.3"
if worker_marker not in worker_text:
    worker_text = replace_unique(
        worker_text,
        '            HomeWidget().updateAll(applicationContext)\n            Result.success()',
        '            HomeWidget().updateAll(applicationContext)\n            ScenarioWidget().updateAll(applicationContext)\n            NotificationsWidget().updateAll(applicationContext)\n            Result.success()',
        "background widget refresh"
    )
    worker_text = worker_text.rstrip() + "\n" + worker_marker + "\n"
    worker.write_text(worker_text, encoding="utf-8")

# A resizable Android home-screen widget backed by the real local event history.
widget_dir.mkdir(parents=True, exist_ok=True)
(widget_dir / "NotificationsWidget.kt").write_text(r'''package ru.dislive.yandexhomewidgets.widget

import android.content.Context
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.glance.GlanceId
import androidx.glance.GlanceModifier
import androidx.glance.appwidget.GlanceAppWidget
import androidx.glance.appwidget.GlanceAppWidgetReceiver
import androidx.glance.appwidget.provideContent
import androidx.glance.background
import androidx.glance.layout.Alignment
import androidx.glance.layout.Column
import androidx.glance.layout.Row
import androidx.glance.layout.Spacer
import androidx.glance.layout.fillMaxSize
import androidx.glance.layout.fillMaxWidth
import androidx.glance.layout.height
import androidx.glance.layout.padding
import androidx.glance.text.FontWeight
import androidx.glance.text.Text
import androidx.glance.text.TextStyle
import androidx.glance.unit.ColorProvider
import ru.dislive.yandexhomewidgets.data.HomeHistoryStore
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

class NotificationsWidget : GlanceAppWidget() {
    override suspend fun provideGlance(context: Context, id: GlanceId) {
        val changes = HomeHistoryStore.load(context).take(4)
        val timeFormat = SimpleDateFormat("HH:mm", Locale.getDefault())
        provideContent {
            Column(
                modifier = GlanceModifier.fillMaxSize()
                    .background(ColorProvider(Color(0xFF172238)))
                    .padding(12.dp),
                verticalAlignment = Alignment.Vertical.Top
            ) {
                Row(verticalAlignment = Alignment.Vertical.CenterVertically) {
                    Text(
                        "Уведомления",
                        modifier = GlanceModifier.defaultWeight(),
                        style = TextStyle(color = ColorProvider(Color.White), fontSize = 16.sp, fontWeight = FontWeight.Bold)
                    )
                    Text(
                        changes.size.toString(),
                        style = TextStyle(color = ColorProvider(Color(0xFFC7B2FF)), fontSize = 12.sp, fontWeight = FontWeight.Bold)
                    )
                }
                Spacer(GlanceModifier.height(7.dp))
                if (changes.isEmpty()) {
                    Text(
                        "Новых событий пока нет. Здесь появятся изменения устройств и датчиков.",
                        style = TextStyle(color = ColorProvider(Color(0xFFC2CAD8)), fontSize = 11.sp)
                    )
                } else {
                    changes.forEachIndexed { index, change ->
                        Column(
                            modifier = GlanceModifier.fillMaxWidth()
                                .background(ColorProvider(Color(0xFF24334B)))
                                .padding(horizontal = 9.dp, vertical = 6.dp)
                        ) {
                            Row(verticalAlignment = Alignment.Vertical.CenterVertically) {
                                Text(
                                    change.title,
                                    modifier = GlanceModifier.defaultWeight(),
                                    maxLines = 1,
                                    style = TextStyle(color = ColorProvider(Color(0xFFE5D8FF)), fontSize = 10.sp, fontWeight = FontWeight.Bold)
                                )
                                Text(
                                    timeFormat.format(Date(change.timestamp)),
                                    style = TextStyle(color = ColorProvider(Color(0xFF9FAFC4)), fontSize = 9.sp)
                                )
                            }
                            Text(
                                change.detail,
                                maxLines = 2,
                                style = TextStyle(color = ColorProvider(Color.White), fontSize = 10.sp)
                            )
                        }
                        if (index != changes.lastIndex) Spacer(GlanceModifier.height(5.dp))
                    }
                }
            }
        }
    }
}

class NotificationsWidgetReceiver : GlanceAppWidgetReceiver() {
    override val glanceAppWidget: GlanceAppWidget = NotificationsWidget()
}
''', encoding="utf-8")

widget_xml.write_text('''<?xml version="1.0" encoding="utf-8"?>
<appwidget-provider xmlns:android="http://schemas.android.com/apk/res/android"
    android:minWidth="220dp"
    android:minHeight="150dp"
    android:minResizeWidth="180dp"
    android:minResizeHeight="110dp"
    android:updatePeriodMillis="0"
    android:initialLayout="@layout/widget_loading"
    android:resizeMode="horizontal|vertical"
    android:widgetCategory="home_screen"
    android:description="@string/notifications_widget_description" />
''', encoding="utf-8")

manifest_text = manifest.read_text(encoding="utf-8")
if 'android:name=".widget.NotificationsWidgetReceiver"' not in manifest_text:
    entry = '''        <receiver android:name=".widget.NotificationsWidgetReceiver" android:exported="true">
            <intent-filter>
                <action android:name="android.appwidget.action.APPWIDGET_UPDATE" />
            </intent-filter>
            <meta-data android:name="android.appwidget.provider" android:resource="@xml/notifications_widget_info" />
        </receiver>
'''
    manifest_text = replace_unique(
        manifest_text,
        '        <receiver android:name=".widget.ScenarioWidgetReceiver" android:exported="true">',
        entry + '        <receiver android:name=".widget.ScenarioWidgetReceiver" android:exported="true">',
        "Notifications widget receiver"
    )
    manifest.write_text(manifest_text, encoding="utf-8")

strings_text = strings.read_text(encoding="utf-8")
if "notifications_widget_description" not in strings_text:
    strings_text = strings_text.replace(
        "</resources>",
        '<string name="notifications_widget_description">Последние изменения устройств и датчиков умного дома</string></resources>'
    )
    strings.write_text(strings_text, encoding="utf-8")


# SMART-HOME-UX-NOTIFICATIONS-NAV-1.8.5
# Scenario run notices, room/page-state restoration and roomier device power controls.
main_activity = root / "app/src/main/java/ru/dislive/yandexhomewidgets/MainActivity.kt"
main_text = main_activity.read_text(encoding="utf-8")

if "import androidx.activity.compose.BackHandler" not in main_text:
    main_text = replace_unique(
        main_text,
        "import androidx.activity.ComponentActivity\n",
        "import androidx.activity.compose.BackHandler\nimport androidx.activity.ComponentActivity\n",
        "BackHandler import"
    )

# Make sure each route remembers where it was opened from.
page_state = '    var page by remember { mutableStateOf(AppPage.HOME) }'
if "var settingsReturnPage by remember" not in main_text:
    main_text = replace_unique(main_text, page_state, page_state + '\n    var settingsReturnPage by remember { mutableStateOf(AppPage.HOME) }', "settings return page")
if "var deviceReturnPage by remember" not in main_text:
    anchor = '    var settingsReturnPage by remember { mutableStateOf(AppPage.HOME) }'
    main_text = replace_unique(main_text, anchor, anchor + '\n    var deviceReturnPage by remember { mutableStateOf(AppPage.HOME) }', "device return page")
if "var groupReturnPage by remember" not in main_text:
    anchor = '    var deviceReturnPage by remember { mutableStateOf(AppPage.HOME) }'
    main_text = replace_unique(main_text, anchor, anchor + '\n    var groupReturnPage by remember { mutableStateOf(AppPage.HOME) }', "group return page")

# Keep each page's saveable scroll state alive while switching to detail screens.
if "val pageStateHolder = rememberSaveableStateHolder()" not in main_text:
    if "import androidx.compose.runtime.saveable.rememberSaveableStateHolder" not in main_text:
        import re
        first_import = re.search(r"(?m)^import ", main_text)
        package_match = re.search(r"(?m)^package [^\r\n]+", main_text)
        if first_import is not None:
            main_text = main_text[:first_import.start()] + "import androidx.compose.runtime.saveable.rememberSaveableStateHolder\n" + main_text[first_import.start():]
        elif package_match is not None:
            main_text = main_text[:package_match.end()] + "\n\nimport androidx.compose.runtime.saveable.rememberSaveableStateHolder\n" + main_text[package_match.end():]
        else:
            raise SystemExit("Could not safely place rememberSaveableStateHolder import")
    anchor = '    var groupReturnPage by remember { mutableStateOf(AppPage.HOME) }'
    main_text = replace_unique(main_text, anchor, anchor + '\n    val pageStateHolder = rememberSaveableStateHolder()', "saveable state holder state")
if "pageStateHolder.SaveableStateProvider(page.name)" not in main_text:
    home_screen_anchor = "AppPage.HOME -> HomeScreen("
    route_pos = main_text.find(home_screen_anchor)
    if route_pos < 0:
        raise SystemExit("HomeScreen route not found for SaveableStateProvider")
    when_anchor = "when (page) {"
    start = main_text.rfind(when_anchor, 0, route_pos)
    if start < 0:
        raise SystemExit("Page-content router not found for SaveableStateProvider")
    brace = main_text.index("{", start)
    depth = 0
    i = brace
    state = "code"
    while i < len(main_text):
        ch = main_text[i]
        nxt = main_text[i + 1] if i + 1 < len(main_text) else ""
        if state == "code":
            if ch == '"':
                if main_text[i:i+3] == '"""':
                    state = "triple"; i += 3; continue
                state = "string"
            elif ch == "'":
                state = "char"
            elif ch == "/" and nxt == "/":
                state = "line"; i += 2; continue
            elif ch == "/" and nxt == "*":
                state = "block"; i += 2; continue
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        elif state == "string":
            if ch == "\\": i += 2; continue
            if ch == '"': state = "code"
        elif state == "char":
            if ch == "\\": i += 2; continue
            if ch == "'": state = "code"
        elif state == "triple":
            if main_text[i:i+3] == '"""':
                state = "code"; i += 3; continue
        elif state == "line":
            if ch == "\n": state = "code"
        elif state == "block":
            if ch == "*" and nxt == "/":
                state = "code"; i += 2; continue
        i += 1
    else:
        raise SystemExit("Could not find matching end of page-content router")
    main_text = main_text[:start] + "pageStateHolder.SaveableStateProvider(page.name) {\n" + main_text[start:end] + "\n}" + main_text[end:]

# A single back action is shared by the toolbar and Android system Back gesture.
if "fun navigateBack()" not in main_text:
    pending = '    var pendingLocationAction by remember { mutableStateOf<((Location) -> Unit)?>(null) }'
    back = """\n\n    fun navigateBack() {\n        when (page) {\n            AppPage.GROUP_DETAILS -> { page = groupReturnPage; selectedGroupId = null }\n            AppPage.DEVICE -> { page = deviceReturnPage; selectedDeviceId = null }\n            AppPage.SETTINGS -> page = settingsReturnPage\n            else -> { page = AppPage.HOME; selectedDeviceId = null; selectedGroupId = null }\n        }\n    }\n    BackHandler(enabled = page != AppPage.HOME) { navigateBack() }"""
    main_text = replace_unique(main_text, pending, pending + back, "screen back handling")

# Remember the origin page for settings/device/group detail routes.
main_text = main_text.replace(
    'TextButton(onClick = { page = AppPage.SETTINGS },',
    'TextButton(onClick = { settingsReturnPage = page; page = AppPage.SETTINGS },'
)
main_text = main_text.replace(
    'onOpenDevice = { selectedDeviceId = it.id; page = AppPage.DEVICE }',
    'onOpenDevice = { deviceReturnPage = page; selectedDeviceId = it.id; page = AppPage.DEVICE }'
)
main_text = main_text.replace(
    'onOpenGroup = { selectedGroupId = it.id; page = AppPage.GROUP_DETAILS }',
    'onOpenGroup = { groupReturnPage = page; selectedGroupId = it.id; page = AppPage.GROUP_DETAILS }'
)

# Replace the old hard-coded Home destination with the remembered route.
old_back = """TextButton(onClick = {\n                            if (page == AppPage.GROUP_DETAILS) page = AppPage.GROUPS\n                            else { page = AppPage.HOME; selectedDeviceId = null; selectedGroupId = null }\n                        }) { Text(\"← Назад\") }"""
if old_back in main_text:
    main_text = main_text.replace(old_back, 'TextButton(onClick = { navigateBack() }) { Text("← Назад") }', 1)
main_text = main_text.replace(
    'Box(Modifier.size(32.dp).clip(CircleShape)',
    'Box(Modifier.size(36.dp).clip(CircleShape)',
    1
)
main_text = main_text.replace(
    'SmartGlyph(if (on) "off" else "power", Modifier.size(22.dp), Color.White)',
    'SmartGlyph(if (on) "off" else "power", Modifier.size(25.dp).padding(1.dp), Color.White)',
    1
)
main_text = main_text.replace(
    'Modifier.weight(1f).height(55.dp)',
    'Modifier.weight(1f).height(62.dp)',
    1
)

# Show a native system notification after successful cloud scenario runs.
if "HomeNotificationCenter.showScenarioRun(context, scenario.name)" not in main_text:
    import re
    pattern = r"((?:api|it)\.runScenario\(scenario\.id\))"
    main_text, count = re.subn(
        pattern,
        r"\1\n                                    HomeNotificationCenter.showScenarioRun(context, scenario.name)",
        main_text
    )
    if count == 0:
        # Some source revisions wrap the API action in a receiver lambda with a different name.
        pattern = r"(runScenario\(scenario\.id\))"
        main_text, count = re.subn(
            pattern,
            r"\1\n                                    HomeNotificationCenter.showScenarioRun(context, scenario.name)",
            main_text
        )
    if count == 0:
        print("No direct cloud scenario call matched; local automation notifications remain enabled")
# Explain which notification center is supported, without implying Xiaomi Home inbox integration.
if "Внутренний центр сообщений Xiaomi Home" not in main_text:
    anchor = 'Text("Уведомления", fontSize = 17.sp, fontWeight = FontWeight.Bold)'
    if anchor in main_text:
        main_text = main_text.replace(
            anchor,
            anchor + '\n                Text("События устройств и запуск сценариев выводятся в системные уведомления Android/HyperOS. Внутренний центр Xiaomi Home принимает события самой экосистемы Xiaomi.", fontSize = 11.sp, color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.78f))',
            1
        )
main_text = main_text.rstrip() + "\n\n" + marker + "\n"
main_activity.write_text(main_text, encoding="utf-8")

# Add a notification for local automations (manual and automatic triggers).
notifications_file = root / "app/src/main/java/ru/dislive/yandexhomewidgets/data/HomeNotifications.kt"
notifications_text = notifications_file.read_text(encoding="utf-8")
if "fun showScenarioRun(" not in notifications_text:
    helper = """    fun showScenarioRun(context: Context, scenarioName: String, automatic: Boolean = false) {\n        val options = HomeNotificationSettings.load(context)\n        if (!options.enabled || !options.groupScenarioChanges) return\n        if (Build.VERSION.SDK_INT >= 33 && context.checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) return\n        val manager = context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager\n        val channelId = \"scenario_notifications\"\n        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O && manager.getNotificationChannel(channelId) == null) {\n            manager.createNotificationChannel(NotificationChannel(channelId, \"Уведомления сценариев\", NotificationManager.IMPORTANCE_DEFAULT))\n        }\n        val intent = Intent(context, MainActivity::class.java).addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP or Intent.FLAG_ACTIVITY_SINGLE_TOP)\n        val notificationId = (System.currentTimeMillis() % Int.MAX_VALUE).toInt()\n        val pendingIntent = PendingIntent.getActivity(context, notificationId, intent, PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)\n        val title = if (automatic) \"Автоматизация выполнена\" else \"Сценарий выполнен\"\n        val message = scenarioName.ifBlank { \"Умный дом\" }\n        val builder = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) Notification.Builder(context, channelId) else Notification.Builder(context)\n        manager.notify(notificationId, builder.setSmallIcon(R.drawable.ic_home).setContentTitle(title).setContentText(message)\n            .setStyle(Notification.BigTextStyle().bigText(message)).setContentIntent(pendingIntent).setAutoCancel(true)\n            .setGroup(\"yandex_home_scenario_events\").build())\n    }\n\n"""
    anchor = "    fun showAutomationNotification("
    if anchor not in notifications_text:
        raise SystemExit("HomeNotifications: could not locate automation notification insertion point")
    notifications_text = notifications_text.replace(anchor, helper + anchor, 1)
    notifications_file.write_text(notifications_text, encoding="utf-8")

# Attach notifications to local automation completion, only on success.
automation_file = root / "app/src/main/java/ru/dislive/yandexhomewidgets/data/LocalAutomation.kt"
automation_text = automation_file.read_text(encoding="utf-8")
if "HomeNotificationCenter.showScenarioRun(context, automation.name, automatic = true)" not in automation_text:
    automatic_call = "runCatching { executeActions(context, api, home, automation.actions) }"
    if automatic_call in automation_text:
        automation_text = automation_text.replace(
            automatic_call,
            "runCatching { executeActions(context, api, home, automation.actions) }.onSuccess { HomeNotificationCenter.showScenarioRun(context, automation.name, automatic = true) }",
            1
        )
    else:
        # Older source versions execute directly inside the successful geofence/condition branch.
        claim = "LocalAutomationStore.claimAutomaticRun(context, automation.id, matches)"
        claim_pos = automation_text.find(claim)
        execute = "executeActions(context, api, home, automation.actions)"
        execute_pos = automation_text.find(execute, claim_pos if claim_pos >= 0 else 0)
        if execute_pos >= 0:
            line_end = automation_text.find("\n", execute_pos)
            if line_end < 0: line_end = execute_pos + len(execute)
            automation_text = automation_text[:line_end] + "\n                    HomeNotificationCenter.showScenarioRun(context, automation.name, automatic = true)" + automation_text[line_end:]
        else:
            print("Automatic local automation execution anchor not found; no automatic run notice added")

if "HomeNotificationCenter.showScenarioRun(context, automation.name, automatic = false)" not in automation_text:
    manual_anchor = "LocalAutomationStore.recordManualRun(context, automationId)"
    if manual_anchor in automation_text:
        automation_text = automation_text.replace(
            manual_anchor,
            manual_anchor + "\n        HomeNotificationCenter.showScenarioRun(context, automation.name, automatic = false)",
            1
        )
    else:
        print("Manual automation record anchor not found; no manual run notice added")
automation_file.write_text(automation_text, encoding="utf-8")

# Keep release metadata consistent with the workflow's version.
version_file = root / "VERSION.txt"
version_file.write_text("1.8.5\n", encoding="utf-8")
gradle_file = root / "app/build.gradle.kts"
gradle_text = gradle_file.read_text(encoding="utf-8")
import re
gradle_text, version_count = re.subn(r'(versionName\s*=\s*)["\'][^"\']+["\']', r'\g<1>"1.8.5"', gradle_text, count=1)
if version_count != 1:
    raise SystemExit("Could not update app versionName to 1.8.5")
gradle_file.write_text(gradle_text, encoding="utf-8")

notes = root / "PATCH_NOTES_1.8.5.txt"
notes.write_text(
    "Яндекс Дом 1.8.5\n"
    "- События устройств и успешные запуски облачных и локальных сценариев выводятся в системные уведомления Android/HyperOS.\n"
    "- Увеличена кнопка питания и добавлен внутренний отступ иконки, чтобы она не обрезалась.\n"
    "- При переходе к подробностям, настройкам и обратно сохраняется положение прокрутки каждого экрана.\n"
    "- Системная кнопка/жест «Назад» возвращает на предыдущий экран.\n"
    "- Внутренний центр сообщений Xiaomi Home остаётся отдельной функцией экосистемы Xiaomi; публичного API для публикации туда сторонних событий нет.\n",
    encoding="utf-8"
)
