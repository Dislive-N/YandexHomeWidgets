#!/usr/bin/env python3
"""Show every automation action as an ordered, readable list."""
from pathlib import Path
import re
import sys

source = Path(sys.argv[1])
content = source.read_text(encoding="utf-8")
marker = "// SCENARIO-ACTIONS-LIST-1.0"

if marker in content:
    print("Scenario action lists are already refined.")
    raise SystemExit(0)

card_anchor = '''                    Row(horizontalArrangement = Arrangement.spacedBy(5.dp)) {
                        Button(onClick = { onRunAutomation(automation.id) }'''
card_replacement = '''                    AutomationActionList(
                        actions = automation.actions,
                        devices = devices,
                        variables = variables,
                        cloudScenarios = cloudScenarios,
                        compact = true
                    )
                    Row(horizontalArrangement = Arrangement.spacedBy(5.dp)) {
                        Button(onClick = { onRunAutomation(automation.id) }'''
if content.count(card_anchor) != 1:
    raise SystemExit("Could not locate the automation card action-button row")
content = content.replace(card_anchor, card_replacement, 1)

detail_pattern = re.compile(
    r'(?m)^(\s*)Text\(detail\.actions\.joinToString\(separator = "\\n"\).*?'
    r'actionDescription\(it, devices, variables, cloudScenarios\).*?'
    r'fontSize = 13\.sp, color = MaterialTheme\.colorScheme\.onSurface\)\s*$'
)
detail_replacement = '''\\1AutomationActionList(
\\1    actions = detail.actions,
\\1    devices = devices,
\\1    variables = variables,
\\1    cloudScenarios = cloudScenarios,
\\1    compact = false
\\1)'''
content, detail_count = detail_pattern.subn(detail_replacement, content, count=1)
if detail_count != 1:
    raise SystemExit("Could not replace the detail dialog's plain-text actions block")

helper = r'''
@Composable
private fun AutomationActionList(
    actions: List<AutomationAction>,
    devices: List<HomeDevice>,
    variables: List<GlobalVariable>,
    cloudScenarios: List<HomeScenario>,
    compact: Boolean
) {
    if (actions.isEmpty()) {
        Text(
            "Действия не добавлены",
            fontSize = 11.sp,
            color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.58f)
        )
        return
    }

    Column(
        Modifier
            .fillMaxWidth()
            .background(
                MaterialTheme.colorScheme.surfaceVariant.copy(alpha = if (compact) 0.38f else 0.55f),
                RoundedCornerShape(14.dp)
            )
            .padding(horizontal = 10.dp, vertical = if (compact) 5.dp else 7.dp),
        verticalArrangement = Arrangement.spacedBy(0.dp)
    ) {
        actions.forEachIndexed { index, action ->
            Row(
                Modifier.fillMaxWidth().padding(vertical = if (compact) 5.dp else 8.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(9.dp)
            ) {
                Box(
                    Modifier
                        .size(if (compact) 23.dp else 27.dp)
                        .background(MaterialTheme.colorScheme.secondaryContainer, RoundedCornerShape(8.dp)),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        (index + 1).toString(),
                        fontSize = 10.sp,
                        fontWeight = FontWeight.Bold,
                        color = MaterialTheme.colorScheme.onSecondaryContainer
                    )
                }
                Text(
                    actionDescription(action, devices, variables, cloudScenarios),
                    Modifier.weight(1f),
                    fontSize = if (compact) 11.sp else 13.sp,
                    color = MaterialTheme.colorScheme.onSurface
                )
            }
            if (index != actions.lastIndex) {
                Divider(
                    Modifier.padding(start = if (compact) 32.dp else 36.dp),
                    color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.10f)
                )
            }
        }
    }
}

'''
helper_anchor = "private fun actionDescription("
if content.count(helper_anchor) != 1:
    raise SystemExit("Could not locate actionDescription helper")
content = content.replace(helper_anchor, helper + helper_anchor, 1)
content = content.rstrip() + "\n\n" + marker + "\n"
source.write_text(content, encoding="utf-8")
print("Automation cards and details now render their actions as ordered list rows.")
