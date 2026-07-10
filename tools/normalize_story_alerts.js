const fs = require("fs");

const files = [
  "Triggers/10b_mission1_p5_air_tech_alerts.txt",
  "Triggers/18_mission2_main_assaults_03_warnings.txt",
];

for (const file of files) {
  const source = fs.readFileSync(file, "utf8");
  const updated = source.replaceAll("<1B>엘리아:", "<06>전술 경보:");
  fs.writeFileSync(file, updated, "utf8");
}

const outerFile = "Triggers/11b_mission1_outer_colony_penalty.txt";
let outer = fs.readFileSync(outerFile, "utf8");
outer = outer.replace(
  /\tDisplay Text Message\(Always Display, "<03>발렌: <04>선봉대, 이곳이 아니다\. 북서쪽 <11>주황색 저그<04> 군락으로 병력을 돌려 공격해라\."\);\r?\n\tDisplay Text Message\(Always Display, "<06>경고: 미션1 진행중 <11>주황색 저그<06>를 제외한 적을 공격할 경우 해당 적이 깨어납니다\."\);/g,
  '\tDisplay Text Message(Always Display, "<06>경고: <04>현재 목표는 북서쪽 <11>주황색 저그<04> 군락입니다. 다른 군락을 공격하면 해당 전선이 즉시 활성화됩니다.");',
);
outer = outer.replace(
  /\tDisplay Text Message\(Always Display, "<1B>엘리아: <04>미확인 군락의 자원 흐름이 열렸습니다\. 생체 반응이 급격히 증가합니다\."\);\r?\n\tDisplay Text Message\(Always Display, "<03>발렌: <04>방금 선을 넘었다\. 저 군락은 이제 우리를 향해 전력을 모을 거다\."\);\r?\n\tDisplay Text Message\(Always Display, "<06>경고: 이 군락이 깨어났습니다\. 공격을 계속하면 미션2에 시작되는 공세가 미션1에 시작됩니다\."\);/g,
  '\tDisplay Text Message(Always Display, "<06>[전선 활성화] <04>외곽 군락이 깨어났습니다. 해당 군락의 공세가 미션 1부터 시작됩니다.");',
);
outer = outer.replace(
  /\tDisplay Text Message\(Always Display, "<1B>엘리아: <04>미확인 군락의 자원 흐름이 열렸습니다\. 생체 반응이 급격히 증가합니다\."\);\r?\n\tDisplay Text Message\(Always Display, "<03>발렌: <04>방금 선을 넘었다\. 두 군락이 동시에 전력을 모을 거다\."\);\r?\n\tDisplay Text Message\(Always Display, "<06>경고: 두 외곽 군락이 깨어났습니다\. 공격을 계속하면 미션2에 시작되는 양쪽 공세가 미션1에 시작됩니다\."\);/g,
  '\tDisplay Text Message(Always Display, "<06>[전선 활성화] <04>두 외곽 군락이 깨어났습니다. 양쪽 공세가 미션 1부터 시작됩니다.");',
);
outer = outer.replace(
  /\tDisplay Text Message\(Always Display, "<03>발렌: <04>선봉대, 병력 분산하지 마라\. 목표는 <11>주황색 저그<04> 군락이다\."\);\r?\n\tDisplay Text Message\(Always Display, "<06>경고: <04>미션1에 <11>주황색 저그<04>가 아닌 다른 적을 공격하면 난이도가 상승합니다\."\);/g,
  '\tDisplay Text Message(Always Display, "<06>경고: <04>다른 군락을 공격하면 전선이 추가로 활성화되어 난이도가 상승합니다.");',
);
fs.writeFileSync(outerFile, outer, "utf8");

console.log(`normalized repeated tactical alerts in ${files.length + 1} files`);
