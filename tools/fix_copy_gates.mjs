import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

function fixCopy(relPath, colonyTag, player, cdUnit, phaseDc, switchColonyLock, switchDetActive, waveS1) {
  const filePath = path.join(ROOT, relPath);
  let content = fs.readFileSync(filePath, 'utf8');
  const start = content.indexOf(`// ${colonyTag} wave copy at detailed-analysis timing`);
  const end = content.indexOf(`// ${colonyTag} consume at contact-warning timing`);
  if (start < 0 || end < 0) throw new Error(`markers not found in ${relPath}`);
  let section = content.slice(start, end);
  section = section.replaceAll('At least, 15120', 'At least, 14160');
  section = section.replaceAll('At least, 15480', 'At least, 14520');
  section = section.replaceAll('At least, 15840', 'At least, 14880');
  section = section.replace(
    new RegExp(`\\tSwitch\\("${switchDetActive}", Set\\);\\n\\tSwitch\\("${waveS1}"`, 'g'),
    `\tSwitch("${waveS1}"`
  );
  content = content.slice(0, start) + section + content.slice(end);
  fs.writeFileSync(filePath, content, 'utf8');
  console.log(relPath, 'copy section fixed');
}

fixCopy('Triggers/18_mission2_main_assaults_01_p6_rolls.txt', 'P6', 'Player 6', 'Zerg Zergling', 'Zerg Lurker', 'Switch31', 'Switch63', 'Switch61');
fixCopy('Triggers/18_mission2_main_assaults_02_p7_rolls.txt', 'P7', 'Player 7', 'Zerg Hydralisk', 'Zerg Mutalisk', 'Switch32', 'Switch67', 'Switch65');
