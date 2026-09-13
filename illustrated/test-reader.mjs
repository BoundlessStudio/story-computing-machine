import assert from 'node:assert/strict';
import {chromium} from 'playwright';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
const directory = resolve(process.argv[2] || 'tmp/illustrated-review');
const browser = await chromium.launch({headless:true});
try {
 for (const width of [360,1280]) {
  const page = await browser.newPage({viewport:{width,height:900}});
  const failures=[];
  page.on('requestfailed', request=>failures.push(request.url()));
  await page.goto(pathToFileURL(resolve(directory,'web/illustrated/sample.html')).href);
  await page.evaluate(async()=>{await document.fonts.ready;await Promise.all([...document.images].map(i=>i.decode()));});
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true,'Horizontal overflow');
  const theme = page.getByRole('button',{name:/Switch to|Toggle color/});
  await theme.click();
  assert.equal(await page.locator('html').getAttribute('data-theme'),'dark');
  await theme.click();
  assert.equal(await page.locator('html').getAttribute('data-theme'),'light');
  assert.equal(await page.getByRole('link',{name:'Download PDF'}).count(),1);
  assert.equal(await page.getByRole('link',{name:'Original story'}).count(),1);
  assert.equal(await page.locator('figure img[alt]').count(),1);
  assert.equal(failures.length,0,failures.join('\n'));
  await page.screenshot({path:resolve(directory,`reader-${width}.png`),fullPage:true});
  await page.close();
 }
 console.log('PASS: mobile/desktop width, font/image loads, theme switching, navigation and alt text');
} finally {await browser.close();}
