import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

function regenCoarse(relPath, cfg) {
  const filePath = path.join(ROOT, relPath);
  let content = fs.readFileSync(filePath, 'utf8');
  const { player, colonyTag, cdUnit, switchColonyLock, switchCoarseRoll } = cfg;

  const detailedPattern = new RegExp(
    `// ${colonyTag} detailed analysis anchor - ([^\\n]+)\\n` +
    `Trigger\\("${player}"\\)\\{\\nConditions:\\n((?:\\t[^\\n]+\\n)+?)Actions:\\n((?:\\t[^\\n]+\\n)+?)\\}`,
    'g'
  );

  const coarseParts = [];
  let m;
  while ((m = detailedPattern.exec(content)) !== null) {
    const label = m[1].trim();
    let conds = m[2];
    const atLeast = conds.match(new RegExp(`Deaths\\("Player 8", "${cdUnit}", At least, (\\d+)\\)`));
    const atMost = conds.match(new RegExp(`Deaths\\("Player 8", "${cdUnit}", At most, (\\d+)\\)`));
    if (!atLeast || !atMost) continue;
    const thresh = Number(atMost[1]) - 2039;

    conds = conds.replace(
      new RegExp(
        `\\tDeaths\\("Player 8", "${cdUnit}", At least, \\d+\\);\\n\\tDeaths\\("Player 8", "${cdUnit}", At most, \\d+\\);\\n`,
        'g'
      ),
      `\tDeaths("Player 8", "${cdUnit}", At least, ${thresh});\n`
    );
    conds = conds.replace(/\tSwitch\("Switch129", Set\);\n/g, '');
    conds = conds.replace(/\tSwitch\("Switch131", Set\);\n/g, '');
    conds = conds.replace(/\tSwitch\("Switch63", Not Set\);\n/g, '');
    conds = conds.replace(/\tSwitch\("Switch67", Not Set\);\n/g, '');
    if (!conds.includes(`Switch("${switchCoarseRoll}"`)) {
      conds = conds.replace(
        `Switch("${switchColonyLock}", Not Set);\n`,
        `Switch("${switchColonyLock}", Not Set);\n\tSwitch("${switchCoarseRoll}", Not Set);\n`
      );
    }

    coarseParts.push(
      `// ${colonyTag} coarse warning roll - ${label}\n` +
      `Trigger("${player}"){\nConditions:\n${conds}` +
      `Actions:\n\tSet Switch("${switchCoarseRoll}", set);\n\tPreserve Trigger();\n}\n`
    );
  }

  const coarseBlock = coarseParts.join('\n');
  content = content.replace(
    new RegExp(
      `// ${colonyTag} coarse warning roll - spawn-180s \\(cooldown T-2040\\)\\. At least threshold: no upper cap\\.\\n[\\s\\S]*?(?=// ${colonyTag} detailed analysis anchor - )`
    ),
    `// ${colonyTag} coarse warning roll - spawn-180s (cooldown T-2040). At least threshold: no upper cap.\n\n${coarseBlock}\n`
  );

  fs.writeFileSync(filePath, content, 'utf8');
  console.log(relPath, 'coarse count', coarseParts.length);
}

regenCoarse('Triggers/18_mission2_main_assaults_01_p6_rolls.txt', {
  player: 'Player 6', colonyTag: 'P6', cdUnit: 'Zerg Zergling',
  switchColonyLock: 'Switch31', switchCoarseRoll: 'Switch128',
});
regenCoarse('Triggers/18_mission2_main_assaults_02_p7_rolls.txt', {
  player: 'Player 7', colonyTag: 'P7', cdUnit: 'Zerg Hydralisk',
  switchColonyLock: 'Switch32', switchCoarseRoll: 'Switch130',
});
