const fs = require("fs");
const path = require("path");

const files = ["KargasIV_Briefing.txt", "카르가스IV_캠페인_소개.md"];
for (const root of ["Triggers", "TestTriggers", "TestTriggersForBuild"]) {
  for (const name of fs.readdirSync(root)) {
    if (name.endsWith(".txt")) files.push(path.join(root, name));
  }
}

for (const file of files) {
  const source = fs.readFileSync(file, "utf8");
  const updated = source
    .replaceAll("노바", "엘리아")
    .replaceAll("호크", "발렌")
    .replaceAll("작전 정보장교 엘리아", "전선분석장교 엘리아")
    .replaceAll("작전정보장교 엘리아", "전선분석장교 엘리아");
  if (updated !== source) fs.writeFileSync(file, updated, "utf8");
}

console.log(`updated character names in ${files.length} files`);
