// 导出本目录的四个演示画面；不修改论文或科研图。
const fs = require('fs');
const path = require('path');
const {pathToFileURL} = require('url');
const {spawnSync} = require('child_process');
const {chromium} = require('playwright');
const args = Object.fromEntries(process.argv.slice(2).reduce((out, x, i, a) => {
  if (i % 2 === 0) out.push([x, a[i+1]]); return out;
}, []));
const root = __dirname;
const repo = path.resolve(root, '../..');
if (!args['--browser']) throw new Error('请用 --browser 指定 Chrome / Chromium 可执行文件');
const assets = path.join(root, 'assets');
fs.mkdirSync(assets, {recursive:true});
const paper = fs.readFileSync(path.join(root, 'index.html'), 'utf8').includes('<title>PaperCraft');
if (paper) {
  if (!args['--pdftoppm']) throw new Error('PaperCraft 预览需用 --pdftoppm 指定 Poppler');
  for (const kind of ['clean', 'review']) {
    const r = spawnSync(args['--pdftoppm'], ['-f','1','-singlefile','-scale-to','920','-png',
      path.join(repo, 'examples/clamp-timing',kind+'.pdf'), path.join(assets,kind+'-page')], {encoding:'utf8'});
    if (r.error || r.status !== 0) throw new Error('PDF 预览失败：'+(r.error || r.stderr));
  }
}
(async () => {
  const browser = await chromium.launch({executablePath:args['--browser'],headless:true,
    args:['--no-first-run','--disable-extensions']});
  try {
    const page = await browser.newPage({viewport:{width:1120,height:760},deviceScaleFactor:1});
    await page.goto(pathToFileURL(path.join(root,'index.html')).href+'?export=1', {waitUntil:'load'});
    await page.evaluate(async()=>{await document.fonts.ready;await Promise.all([...document.images].map(i=>i.decode()));});
    const checks=[];
    for(let i=0;i<4;i++){
      await page.evaluate(n=>window.showSlide(n),i);
      const slide=page.locator('.slide.active');
      const result=await slide.evaluate(el=>{
        const b=el.getBoundingClientRect();
        const overflow=[...el.querySelectorAll('p,h1,h2,img,.quote,.rail,.body')].filter(c=>{
          const r=c.getBoundingClientRect();return r.right>b.right+.5||r.left<b.left-.5||r.bottom>b.bottom-48;
        }).map(e=>e.tagName+': '+(e.textContent||e.alt||'').slice(0,60));
        return {width:b.width,height:b.height,overflow,images:[...el.querySelectorAll('img')].map(e=>({src:e.getAttribute('src'),width:e.naturalWidth,height:e.naturalHeight}))};
      });
      if(result.overflow.length)throw new Error('画面 '+(i+1)+' 越界：'+JSON.stringify(result.overflow));
      await slide.screenshot({path:path.join(assets,`step-${i+1}.png`)});
      checks.push(result);
    }
    // 检查本地导览可暂停切换，默认不会自动播放。
    await page.goto(pathToFileURL(path.join(root,'index.html')).href);
    await page.locator('[data-step="2"]').click();
    if(await page.locator('#status').innerText()!=='第 3 / 4 步')throw new Error('数字按钮未切换');
    await page.keyboard.press('ArrowLeft');
    if(await page.locator('#status').innerText()!=='第 2 / 4 步')throw new Error('方向键未切换');
    await page.locator('#play').click();
    if(await page.locator('#play').innerText()!=='暂停')throw new Error('播放按钮异常');
    await page.locator('#play').click();
    console.log(JSON.stringify({scenes:checks,manual_navigation:'passed',duration_seconds:32}));
  } finally {await browser.close();}
})().catch(e=>{console.error(e.message);process.exitCode=1;});
