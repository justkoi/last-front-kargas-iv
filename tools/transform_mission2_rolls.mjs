import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

function buildCoarseTriggers(content, colony, cdUnit, switchColonyLock, switchCoarseRoll) {
  const pattern = new RegExp(
    `// ${colony} detailed analysis anchor - ([^\\n]+)\\n` +
    `Trigger\\("${colony}"\\)\\{\\nConditions:\\n((?:\\t[^\\n]+\\n)+?)Actions:\\n((?:\\t[^\\n]+\\n)+?)\\}`,
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
      `// ${colony} coarse warning roll - ${label}\n` +
      `Trigger("${colony}"){\nConditions:\n${conds}` +
      `Actions:\n\tSet Switch("${switchCoarseRoll}", set);\n\tPreserve Trigger();\n}\n`
    );
  }
  return parts.join('\n');
}

function transformRolls(content, cfg) {
  const {
    colony, cdUnit, waveS1, waveS2, spawnS1, spawnS2,
    switchColonyLock, switchDetActive, switchCoarseShown,
    switchCoarseRoll,
  } = cfg;

  content = content.replace(
    `//-----------------------------------------------------------------//\n` +
    `//  ${colony} main-assault roll with safe wave-only pre-roll\n` +
    `//  Pre-roll stores only the upcoming wave in dedicated switches.\n` +
    `//  Route, Hunt target, and assault state are decided at the original warning timing.\n` +
    `//-----------------------------------------------------------------//\n\n` +
    `// ${colony} wave-only pre-rolls fire 80 seconds before the original warning timing.`,
    `//-----------------------------------------------------------------//\n` +
    `//  ${colony} main-assault roll with pre-seeded wave type and 3-stage warnings\n` +
    `//  Wave type (${waveS1}/${waveS2}) is seeded at game start and re-rolled after each consume.\n` +
    `//  Coarse air/ground warning at spawn-180s, detailed analysis at spawn-90s,\n` +
    `//  route/Hunt target and assault state at consume (spawn-10s).\n` +
    `//-----------------------------------------------------------------//\n\n` +
    `// ${colony} coarse warning roll - spawn-180s (cooldown T-2040). At least threshold: no upper cap.\n` +
    `COARSE_BLOCK_PLACEHOLDER`
  );

  content = content.replaceAll(`// ${colony} pre-roll wave - `, `// ${colony} detailed analysis anchor - `);
  content = content.replace(
    `// ${colony} pre-roll wave copy. This runs only when the selected roll threshold is reached.`,
    `// ${colony} wave copy at detailed-analysis timing (spawn-90s). Idempotent; copies pre-seeded ${waveS1}/${waveS2} to ${spawnS1}/${spawnS2}.`
  );
  content = content.replace(
    `// ${colony} confirmed pre-rolls reach the original warning state.\n// ${colony} consume pre-roll -`,
    `// ${colony} consume at contact-warning timing (spawn-10s).\n// ${colony} consume -`
  );
  content = content.replaceAll(`// ${colony} consume pre-roll -`, `// ${colony} consume -`);
  content = content.replace(
    `// ${colony} fallback rolls: if cooldown acceleration skips the pre-roll window, decide at the selected timing.`,
    `// ${colony} fallback rolls: if acceleration skips the detailed-analysis window, consume at spawn-10s with pre-seeded wave.`
  );
  content = content.replaceAll(`// ${colony} roll random wave -`, `// ${colony} fallback consume -`);

  const coarseBlock = buildCoarseTriggers(content, colony, cdUnit, switchColonyLock, switchCoarseRoll);
  content = content.replace('COARSE_BLOCK_PLACEHOLDER', coarseBlock + '\n');

  content = content.replaceAll(
    `\tSet Switch("${waveS1}", randomize);\n\tSet Switch("${waveS2}", randomize);\n`,
    ''
  );

  content = content.replace(
    new RegExp(
      `(// ${colony} detailed analysis anchor[^\\n]*\\nTrigger\\("${colony}"\\)\\{\\nConditions:\\n(?:[^\\n]+\\n)+?\\tSwitch\\("${switchColonyLock}", Not Set\\);\\n)` +
      `\\tSwitch\\("${switchDetActive}", Not Set\\);`,
      'g'
    ),
    `$1\tSwitch("${switchCoarseShown}", Set);\n\tSwitch("${switchDetActive}", Not Set);`
  );

  content = content.replace(
    new RegExp(`// ${colony} copy Wave[^\\n]*\\nTrigger\\("${colony}"\\)\\{[\\s\\S]*?\\n\\}`, 'g'),
    (block) => {
      block = block.replace(new RegExp(`\\tSwitch\\("${switchDetActive}", Set\\);\\n`, 'g'), '');
      return block
        .replaceAll('At least, 15120', 'At least, 14160')
        .replaceAll('At least, 15480', 'At least, 14520')
        .replaceAll('At least, 15840', 'At least, 14880');
    }
  );

  content = content.replaceAll(
    `\tSet Switch("${waveS1}", clear);\n\tSet Switch("${waveS2}", clear);\n\tSet Switch("${switchDetActive}", clear);`,
    `\tSet Switch("${waveS1}", randomize);\n\tSet Switch("${waveS2}", randomize);\n\tSet Switch("${switchCoarseRoll}", clear);\n\tSet Switch("${switchCoarseShown}", clear);\n\tSet Switch("${switchDetActive}", clear);`
  );

  content = content.replace(
    new RegExp(`// ${colony} fallback consume[^\\n]*\\nTrigger\\("${colony}"\\)\\{[\\s\\S]*?\\n\\}`, 'g'),
    (block) => {
      block = block.replace(
        new RegExp(`\\tSet Switch\\("${spawnS1}", randomize\\);\\n\\tSet Switch\\("${spawnS2}", randomize\\);\\n`, 'g'),
        ''
      );
      if (!block.includes(switchCoarseRoll)) {
        block = block.replace(
          `\tSet Deaths("Player 8", "${cdUnit}", Subtract,`,
          `\tSet Switch("${waveS1}", randomize);\n\tSet Switch("${waveS2}", randomize);\n\tSet Switch("${switchCoarseRoll}", clear);\n\tSet Switch("${switchCoarseShown}", clear);\n\tSet Deaths("Player 8", "${cdUnit}", Subtract,`
        );
      }
      return block;
    }
  );

  return content;
}

const p6Path = path.join(ROOT, 'Triggers/18_mission2_main_assaults_01_p6_rolls.txt');
const p7Path = path.join(ROOT, 'Triggers/18_mission2_main_assaults_02_p7_rolls.txt');

const p6 = transformRolls(fs.readFileSync(p6Path, 'utf8'), {
  colony: 'P6', cdUnit: 'Zerg Zergling', waveS1: 'Switch61', waveS2: 'Switch62',
  spawnS1: 'Switch9', spawnS2: 'Switch10', switchColonyLock: 'Switch31',
  switchDetActive: 'Switch63', switchCoarseShown: 'Switch129', switchCoarseRoll: 'Switch128',
});
fs.writeFileSync(p6Path, p6, 'utf8');

const p7 = transformRolls(fs.readFileSync(p7Path, 'utf8'), {
  colony: 'P7', cdUnit: 'Zerg Hydralisk', waveS1: 'Switch65', waveS2: 'Switch66',
  spawnS1: 'Switch11', spawnS2: 'Switch12', switchColonyLock: 'Switch32',
  switchDetActive: 'Switch67', switchCoarseShown: 'Switch131', switchCoarseRoll: 'Switch130',
});
fs.writeFileSync(p7Path, p7, 'utf8');

console.log('P6:', p6.includes('coarse warning roll'), !p6.includes('Switch9", randomize'));
console.log('P7:', p7.includes('coarse warning roll'), !p7.includes('Switch11", randomize'));
