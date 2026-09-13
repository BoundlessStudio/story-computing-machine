// Reproducible HTML layout using the repository-pinned Playwright Chromium.
import {chromium} from 'playwright';
import {pathToFileURL} from 'node:url';
import {resolve} from 'node:path';
import {mkdir} from 'node:fs/promises';
import {dirname} from 'node:path';
const [source, destination] = process.argv.slice(2);
if (!source || !destination) throw new Error('Usage: node illustrated/export.mjs INPUT.html OUTPUT.pdf');
if (!destination.toLowerCase().endsWith('.pdf')) throw new Error('Output must be a PDF');
const browser = await chromium.launch({headless:true});
try {
  const page = await browser.newPage();
  // Editions have local fonts/assets; export must never depend on a remote service.
  await page.route(/^https?:/, route => route.abort());
  await page.goto(pathToFileURL(resolve(source)).href, {waitUntil:'load'});
  await page.emulateMedia({media:'print'});
  await page.evaluate(async () => {
    await document.fonts.ready;
    await Promise.all([...document.images].map(image => {image.loading='eager'; return image.decode();}));
    for (const font of document.fonts) if (font.status !== 'loaded') await font.load();
    if (!document.fonts.check('12px "Source Serif"') || !document.fonts.check('12px "Source Sans"')) throw new Error('Edition fonts failed to load');
  });
  await mkdir(dirname(resolve(destination)), {recursive:true});
  await page.pdf({path:destination,preferCSSPageSize:true,printBackground:true,tagged:true,outline:true});
  process.stdout.write(`Exported ${destination}\n`);
} finally {await browser.close();}
