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
  const save = async name => {
    await page.locator('[data-stale="true"]:visible').first().waitFor({ state: 'hidden' });
    await page.screenshot({ path: path.join(env.SGT_DEMO_FIGURES, name), animations: 'disabled' });
  };
  const text = label => page.getByText(label, { exact: true });
  const tab = name => page.getByRole('tab', { name, exact: true });
  const map = page.frameLocator('.st-key-map-canvas iframe');
  await page.goto(env.SGT_DEMO_URL, { waitUntil: 'domcontentloaded' });
  await page.getByLabel('Correo', { exact: true }).waitFor();
  await save('FIG_007_acceso.png');
  await page.getByLabel('Correo', { exact: true }).fill(env.ADMIN_EMAIL);
  await page.getByLabel('Contraseña', { exact: true }).fill(env.ADMIN_PASSWORD);
  await page.getByRole('button', { name: 'Entrar', exact: true }).click();
  await page.getByRole('button', { name: 'Entrar', exact: true }).waitFor({ state: 'detached' });
  await text('Tiempos del plan en ejecución').waitFor();
  await map.locator('.leaflet-tile-loaded').first().waitFor();
  await save('FIG_008_monitor.png');

  await tab('Intervención y Modelo').click();
  await page.getByRole('slider', { name: 'Verde NS (s)', exact: true }).waitFor();
  await save('FIG_009_intervencion.png');

  await tab('Comparador y Auditoría').click();
  await text('Auditoría reciente').click();
  const audit = page.locator('details').filter({ hasText: 'Auditoría reciente' });
  await audit.getByRole('button', { name: 'Consultar auditoría' }).click();
  await audit.locator('[data-testid="stDataFrame"]').waitFor();
  await save('FIG_010_auditoria.png');

  await page.getByRole('combobox', { name: /Vista de tráfico/ }).click();
  await page.getByRole('option', { name: 'Tráfico real (TomTom)', exact: true }).click();
  await tab('Monitor en vivo').click();
  await text('Velocidad actual').waitFor();
  await map.locator('.leaflet-overlay-pane canvas').waitFor();
  await map.locator('.leaflet-control-attribution').filter({ hasText: 'Datos de tráfico © TomTom' }).waitFor();
  await map.locator('.leaflet-tile-loaded').first().waitFor();
  await save('FIG_011_tomtom.png');

  await tab('Comparador y Auditoría').click();
  await page.getByRole('button', { name: 'Comparar puntos', exact: true }).click();
  await page.getByRole('tabpanel', { name: 'Comparador y Auditoría' })
    .getByTestId('data-grid-canvas').waitFor();
  await save('FIG_012_comparador.png');
  console.log('Seis capturas verificadas, incluida la comparación con TomTom en vivo.');
} finally {
  await browser.close();
}
