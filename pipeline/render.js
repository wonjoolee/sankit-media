// 사용: node pipeline/render.js <kit.html 경로> <출력폴더>
// kit.html 안의 #s1..#s5 카드를 01.jpg..05.jpg(1080x1350)로 저장
const {chromium}=require('playwright');const path=require('path');const fs=require('fs');
const [html,out]=process.argv.slice(2);(async()=>{const b=await chromium.launch();const p=await b.newPage();
await p.goto('file://'+path.resolve(html));await p.waitForLoadState('networkidle');fs.mkdirSync(out,{recursive:true});
for(let i=1;i<=5;i++){await p.locator('#s'+i).screenshot({path:`${out}/0${i}.png`});}
await b.close();})();
