// Renders assets/avatar.svg to assets/avatar.png (1024px) with headless Chromium.
const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const dir = path.resolve(__dirname, '..', 'assets');
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1024, height: 1024 } });
  await p.goto('file://' + dir + '/avatar.svg');
  await p.waitForTimeout(400);
  await p.screenshot({ path: dir + '/avatar.png' });
  await b.close();
})();
