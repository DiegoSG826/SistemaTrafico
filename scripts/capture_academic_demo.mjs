import { chromium } from 'file:///C:/Users/diego/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs';
import fs from 'node:fs/promises';
const out='entrega_academica/figuras'; await fs.mkdir(out,{recursive:true});
const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
try {
 const page=await browser.newPage({viewport:{width:1440,height:1000},deviceScaleFactor:1});
 await page.goto('http://127.0.0.1:29501',{waitUntil:'domcontentloaded'});
 await page.getByLabel('Correo',{exact:true}).waitFor({timeout:40000});
 await page.screenshot({path:`${out}/FIG_007_acceso.png`});
 await page.getByLabel('Correo',{exact:true}).fill(process.env.ADMIN_EMAIL);
 await page.getByLabel('Contraseña',{exact:true}).fill(process.env.DEMO_PASSWORD);
 await page.getByRole('button',{name:'Entrar',exact:true}).click();
 await page.getByText('Intervención del administrador',{exact:true}).waitFor({timeout:40000});
 await page.getByText('Modo confirmado',{exact:true}).waitFor({timeout:40000});
 await page.waitForFunction(()=>document.querySelectorAll('[data-stale="true"]').length===0,{},{timeout:20000}).catch(()=>{});
 await page.screenshot({path:`${out}/FIG_008_monitor.png`});
 await page.getByText('Intervención del administrador',{exact:true}).scrollIntoViewIfNeeded();
 await page.waitForFunction(()=>document.querySelectorAll('[data-stale="true"]').length===0,{},{timeout:10000}).catch(()=>{});
 await page.screenshot({path:`${out}/FIG_009_intervencion.png`});
 await page.getByText('Auditoría reciente',{exact:true}).click();
 await page.getByRole('button',{name:'Consultar auditoría',exact:true}).click();
 await page.waitForTimeout(1500);
 await page.getByText('Auditoría reciente',{exact:true}).scrollIntoViewIfNeeded();
 await page.screenshot({path:`${out}/FIG_010_auditoria.png`});
 console.log('Capturas reales de acceso, monitor, intervención y auditoría guardadas.');
} finally {await browser.close();}
