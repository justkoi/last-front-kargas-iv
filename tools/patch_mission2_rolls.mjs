import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

function buildCoarseFromDetailed(content, player, colonyTag, cdUnit, switchColonyLock, switchCoarseRoll) {
  const pattern = new RegExp(
    `// ${colonyTag} detailed analysis anchor - ([^\\n]+)\\n` +
    `Trigger\\("${player}"\\)\\{\\nConditions:\\n((?:\\t[^\\n]+\\n)+?)Actions:`,
    'g'
  );
  const parts = [];
  const seen = new Set();
  let m;
  while ((m = pattern.exec(content)) !== null) {
    const label = m[1].trim();
    if (seen.has(label)) continue;
    seen.add(label);
    let conds = m[2];
    let thresh;
    if (label.includes('cooldown 21m -')) thresh = 13080;
    else if (label.includes('cooldown 22m -')) thresh = 13800;
    else thresh = 13440;

    conds = conds.replace(
      /\tDeaths\("Player 8", "[^"]+", At least, \d+\);\n\tDeaths\("Player 8", "[^"]+", At most, \d+\);\n/,
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
    parts.push(
      `// ${colonyTag} coarse warning roll - ${label}\n` +
      `Trigger("${player}"){\nConditions:\n${conds}` +
      `Actions:\n\tSet Switch("${switchCoarseRoll}", set);\n\tPreserve Trigger();\n}\n`
    );
  }
  return parts.join('\n');
}

function patchFile(relPath, cfg) {
  const filePath = path.join(ROOT, relPath);
  let content = fs.readFileSync(filePath, 'utf8');
  const {
    player, colonyTag, cdUnit, phaseDc, waveS1, waveS2, spawnS1, spawnS2,
    switchColonyLock, switchDetActive, switchCoarseShown, switchCoarseRoll,
  } = cfg;

  const coarse = buildCoarseFromDetailed(content, player, colonyTag, cdUnit, switchColonyLock, switchCoarseRoll);
  content = content.replace(
    new RegExp(`// ${colonyTag} coarse warning roll - spawn-180s \\(cooldown T-2040\\)\\. At least threshold: no upper cap\\.\\n\\n+`),
    `// ${colonyTag} coarse warning roll - spawn-180s (cooldown T-2040). At least threshold: no upper cap.\n\n${coarse}\n`
  );

  for (const atMost of ['15119', '15479', '15839']) {
    content = content.replaceAll(
      `\tDeaths("Player 8", "${cdUnit}", At most, ${atMost});\n\tDeaths("Player 8", "${phaseDc}", Exactly, 0);\n\tSwitch("${switchColonyLock}", Not Set);\n\tSwitch("${switchDetActive}", Not Set);`,
      `\tDeaths("Player 8", "${cdUnit}", At most, ${atMost});\n\tDeaths("Player 8", "${phaseDc}", Exactly, 0);\n\tSwitch("${switchColonyLock}", Not Set);\n\tSwitch("${switchCoarseShown}", Set);\n\tSwitch("${switchDetActive}", Not Set);`
    );
  }

  content = content.replace(
    new RegExp(
      `(// ${colonyTag} fallback consume[^\\n]*\\nTrigger\\("${player}"\\)\\{[\\s\\S]*?)(\\tSet Deaths\\("Player 8", "${cdUnit}", Subtract,)`,
      'g'
    ),
    (all, head, subtractLine) => {
      if (head.includes(`Set Switch("${waveS1}", randomize)`)) return all;
      return head +
        `\tSet Switch("${waveS1}", randomize);\n\tSet Switch("${waveS2}", randomize);\n` +
        `\tSet Switch("${switchCoarseRoll}", clear);\n\tSet Switch("${switchCoarseShown}", clear);\n` +
        subtractLine;
    }
  );

  fs.writeFileSync(filePath, content, 'utf8');
  console.log(relPath, 'patched');
  console.log('  coarse triggers:', (content.match(new RegExp(`// ${colonyTag} coarse warning roll - cooldown`, 'g')) || []).length);
  console.log('  coarse shown gate:', (content.match(new RegExp(`Switch\\("${switchCoarseShown}", Set\\)`, 'g')) || []).length);
}

patchFile('Triggers/18_mission2_main_assaults_01_p6_rolls.txt', {
  player: 'Player 6', colonyTag: 'P6', cdUnit: 'Zerg Zergling', phaseDc: 'Zerg Lurker',
  waveS1: 'Switch61', waveS2: 'Switch62', spawnS1: 'Switch9', spawnS2: 'Switch10',
  switchColonyLock: 'Switch31', switchDetActive: 'Switch63',
  switchCoarseShown: 'Switch129', switchCoarseRoll: 'Switch128',
});

patchFile('Triggers/18_mission2_main_assaults_02_p7_rolls.txt', {
  player: 'Player 7', colonyTag: 'P7', cdUnit: 'Zerg Hydralisk', phaseDc: 'Zerg Mutalisk',
  waveS1: 'Switch65', waveS2: 'Switch66', spawnS1: 'Switch11', spawnS2: 'Switch12',
  switchColonyLock: 'Switch32', switchDetActive: 'Switch67',
  switchCoarseShown: 'Switch131', switchCoarseRoll: 'Switch130',
});
