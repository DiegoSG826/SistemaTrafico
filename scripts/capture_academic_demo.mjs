import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const env = process.env;
const { chromium } = await import(pathToFileURL(path.join(
  env.SGT_ACADEMIC_NODE_MODULES, 'playwright/index.mjs')).href);
const browser = await chromium.launch({
  headless: true,
  executablePath: env.SGT_ACADEMIC_EDGE || 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
});

try {
  await fs.mkdir(env.SGT_DEMO_FIGURES, { recursive: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 }, deviceScaleFactor: 1 });
  page.setDefaultTimeout(30000);
  const save = name => page.screenshot({ path: path.join(env.SGT_DEMO_FIGURES, name) });
  const position = async locator => {
    await locator.evaluate(node => node.scrollIntoView({ block: 'start' }));
    await page.evaluate(() => window.scrollBy(0, -70));
  };
  const text = label => page.getByText(label, { exact: true });
  const map = page.frameLocator('iframe[title="st.iframe"]').first();
  await page.goto(env.SGT_DEMO_URL, { waitUntil: 'domcontentloaded' });
  await page.getByLabel('Correo', { exact: true }).waitFor();
  await save('FIG_007_acceso.png');
  await page.getByLabel('Correo', { exact: true }).fill(env.ADMIN_EMAIL);
  await page.getByLabel('Contraseña', { exact: true }).fill(env.ADMIN_PASSWORD);
  await page.getByRole('button', { name: 'Entrar', exact: true }).click();
  await text('Tiempos del plan en ejecución').waitFor();
  await map.locator('.leaflet-tile-loaded').first().waitFor();
  await save('FIG_008_monitor.png');

  await position(text('Intervención del administrador'));
  await save('FIG_009_intervencion.png');
  await text('Auditoría reciente').click();
  const audit = page.locator('details').filter({ hasText: 'Auditoría reciente' });
  await audit.getByRole('button', { name: 'Consultar auditoría' }).click();
  await audit.locator('[data-testid="stDataFrame"]').waitFor();
  await position(text('Auditoría reciente'));
  await save('FIG_010_auditoria.png');

  await text('Tráfico real (TomTom)').click();
  await text('Velocidad actual').waitFor();
  await map.locator('.leaflet-overlay-pane canvas').waitFor();
  await map.locator('.leaflet-control-attribution').filter({ hasText: 'Datos de tráfico © TomTom' }).waitFor();
  await map.locator('.leaflet-tile-loaded').first().waitFor();
  await position(text('Tráfico real · TomTom'));
  await save('FIG_011_tomtom.png');
  console.log('Cinco capturas verificadas en el dashboard actual.');
} finally {
  await browser.close();
}
