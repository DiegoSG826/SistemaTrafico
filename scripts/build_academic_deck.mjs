import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {Presentation,PresentationFile} from 'file:///C:/Users/diego/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs';
process.env.RUNTIME_NODE_MODULES='C:/Users/diego/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules';
const root=process.cwd(), out=path.join(root,'entrega_academica'), build=path.join(root,'data/academic-build');
await fs.mkdir(build,{recursive:true}); await fs.mkdir(path.join(out,'diapositivas'),{recursive:true});
const model=JSON.parse(await fs.readFile('reports/model_evaluation.json','utf8'));
const experiment=JSON.parse(await fs.readFile('reports/experiment.json','utf8'));
const presentation=Presentation.create({slideSize:{width:1280,height:720}});
const figureBytes=new Map();
for(const name of await fs.readdir(path.join(out,'figuras')))if(name.endsWith('.png'))figureBytes.set(name,new Uint8Array(await fs.readFile(path.join(out,'figuras',name))));
const navy='#13394D', teal='#087F82', ink='#172B3A';
function text(s,label,x,y,w,h,size=28,bold=false,color=ink){
 const sh=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
 sh.text=label; sh.text.style={typeface:'Arial',fontSize:size,bold,color}; return sh;
}
function rect(s,x,y,w,h,fill){return s.shapes.add({geometry:'rect',position:{left:x,top:y,width:w,height:h},fill,line:{fill:'none',width:0}});}
function image(s,name,x=500,y=180,w=720,h=450){s.images.add({blob:figureBytes.get(name),contentType:'image/png',alt:name,fit:'contain',position:{left:x,top:y,width:w,height:h}});}
const slides=[];
function add(title,lead,body,notes){
 const s=presentation.slides.add(); s.background.fill='#FFFFFF';
 rect(s,0,0,1280,12,teal); text(s,title,64,50,1150,105,42,true,navy);
 if(lead)text(s,lead,64,170,400,110,30,true,teal);
 if(body)text(s,body,64,300,400,310,24);
 text(s,`PRE_001 · ${String(slides.length+1).padStart(2,'0')} · Cuauhtémoc simulado`,64,670,1100,28,15,false,'#607680');
 s.speakerNotes.text=notes; slides.push({title,lead,body,notes}); return s;
}
let s=add('Gestión inteligente de semáforos en Cuauhtémoc','Prototipo académico verificable','Cinco cruces sintéticos\nPronóstico de demanda\nControl con restricciones','Presentamos un gestor de semáforos simulados para Cuauhtémoc. La IA anticipa llegadas; el controlador reparte verde y el simulador aplica el plan. No controla semáforos físicos ni usa aforos oficiales.');
text(s,'120 s',590,205,550,130,112,true,teal); text(s,'Un ciclo con prioridad peatonal',550,360,610,80,30,true,navy);
text(s,'40/40 fijo → reparto adaptativo validado',550,470,610,100,28);
s=add('Del dato al plan confirmado','Separar pronóstico de actuación','La propuesta no cambia colores.\nEl trabajador confirma el plan al siguiente ciclo.','El generador registra observaciones por minuto. La API consulta la IA, valida tiempos y guarda una propuesta. Solo el trabajador aplica al inicio del ciclo. El dashboard presenta estados confirmados. Fuente: memoria DOC_001, COMP_001 a COMP_008.'); image(s,'FIG_005_arquitectura.png');
s=add('Datos sintéticos y evaluación temporal','Noventa días reproducibles','Semilla 42; cinco cruces.\nEntrenamiento 54 días, validación 18 y prueba 18.\nPurga de etiquetas futuras.','El dataset incluye horario, día, clima, historial y velocidad. La etiqueta es el promedio de llegadas de cinco minutos futuros. El pipeline separa entrenamiento y prueba. Los datos no fueron calibrados con Cuauhtémoc. Fuente: reports/model_evaluation.json y REF_005.');
text(s,'X conocido → demanda futura',530,205,650,90,37,true,teal); text(s,'Random Forest de regresión\n\nLa IA estima veh/min.\nLas reglas calculan verde y rojo.',530,330,650,240,31);
s=add('Más demanda recibe más verde','Ejemplo controlado 30/10 veh/min','Plan anterior: 40/40.\nObjetivo proporcional: 60/20.\nLímite por ciclo: ±5 s.','Con demanda prevista de treinta vehículos por minuto en norte sur y diez en este oeste, el objetivo proporcional es sesenta veinte. Desde cuarenta cuarenta se limita a cuarenta y cinco treinta y cinco. El rojo se deriva del ciclo. Este es un ejemplo de las reglas, no un resultado medido de calle.');
text(s,'45 s NS',540,190,620,85,60,true,navy); rect(s,540,290,540,58,teal);
text(s,'35 s EO',540,385,620,85,60,true,navy); rect(s,540,485,420,58,'#4C8299');
text(s,'Rojo NS 72 s · rojo EO 82 s',540,575,650,45,24);
s=add('Las restricciones siempre prevalecen','80 s de verde vehicular total','Verdes entre 20 y 60 s.\nPeatones exclusivos 20 s.\nAmarillos y despejes obligatorios.','El ciclo conserva exclusión de movimientos y una oportunidad peatonal. Automático limita la variación. Si faltan datos o IA, prevalece un plan fijo cuarenta cuarenta. Manual tiene motivo y caducidad. Los tiempos son didácticos, no reglamentarios.');
let x=510; for(const [label,seconds,color] of [['NS',40,teal],['A',3,'#D6A230'],['D',2,'#AB4A4A'],['EO',40,'#4C8299'],['A',3,'#D6A230'],['D',2,'#AB4A4A'],['PEATÓN',20,'#726299'],['D',10,'#AB4A4A']]){const w=seconds*5.3;rect(s,x,285,w,90,color);if(w>50)text(s,label,x+3,310,w-6,40,19,true,'#FFFFFF');x+=w;}
text(s,'NS → EO → peatones → nuevo ciclo',520,430,650,110,30,true,navy);
s=add('Casos de uso y trazabilidad','Diez casos especificados','Administrador, proveedor y evaluador.\nPrecondiciones, alternativas y criterios ligados a pruebas.','El diagrama UML y las diez especificaciones están en DOC_002 y FIG_003. Los actores tienen identificadores ACT y los casos CU. La nota de identificación de todos los elementos se materializa también en requisitos, tablas y figuras.');image(s,'FIG_003_casos_uso.png');
s=add('Persistencia que protege la decisión','Un solo plan activo por cruce','FK y ventanas únicas.\nVersiones contra solicitudes simultáneas.\nAuditoría de antes y después.','El esquema SQL contiene intersecciones, grupos, observaciones, predicciones, modelos y planes. Un índice parcial impide dos activos y los triggers comprueban todas las fases de un plan al confirmar. El modelo entidad relación completo está en FIG_004.');
for(const [label,y] of [['Intersección → grupos → observaciones',205],['Modelo → predicción → plan',335],['Plan → detalles → aplicación auditada',465]]){text(s,label,510,y,700,110,29,true,navy);}
s=add('Plan de trabajo con cuatro integrantes','45 días y 5 de reserva','Líder / Backend\nFrontend\nIA / Data Science\nQA / Soporte','La línea base estima mil doscientas ochenta horas persona y diez semanas. PERT calcula cuarenta y cinco días hábiles más reserva. Es planificación, no un registro de horas ejecutadas. Fuentes: reports/pert.json y DOC_001 CAL_001.');image(s,'FIG_001_gantt.png');
s=add('El monitor muestra lo confirmado','Demanda, colas y tiempos','Verde, amarillo y rojo por dirección.\nModo y antigüedad visibles.\nIntervención temporal validada.','Esta captura procede de una instancia real temporal del dashboard con datos sintéticos y credenciales efímeras. Permite observar demanda, colas y tiempos, y distinguir una solicitud pendiente de un plan activo.');image(s,'FIG_008_monitor.png',500,160,720,470);
s=add('El modelo supera la persistencia','Error predictivo en veh/min','Prueba temporal reservada.\nLa precisión no demuestra por sí sola menor demora.','En la prueba sintética reservada, el error absoluto medio fue uno punto diecinueve vehículos por minuto, frente a uno punto cuarenta y cinco de persistencia. Esto evalúa predicción; el control requiere otro experimento. Fuente: reports/model_evaluation.json.');
s.charts.add('bar',{position:{left:530,top:205,width:650,height:360},categories:['Persistencia','Random Forest'],series:[{name:'MAE veh/min',values:[model.metrics.test.persistence.mae,model.metrics.test.model.mae].map(v=>Number(v.toFixed(4))),fill:teal}],hasLegend:false,dataLabels:{showValue:true,position:'outEnd'}});
s=add('El beneficio depende del escenario','29.37% menos demora media','Resultado sintético, no vial real.\nValle y pico empeoran ligeramente.\nDesbalance concentra el beneficio.','La evaluación usó cincuenta pares con las mismas llegadas. En escenarios no sobresaturados la reducción media de demora fue veintinueve punto treinta y siete por ciento. El resultado no es uniforme ni representa una medición en calles de Cuauhtémoc. Fuente: reports/experiment.json.');
const scenarios=['valley','peak','imbalance','rain_incident'];
const values=scenarios.map(k=>{const r=experiment.runs.filter(x=>x.scenario===k);return Number((r.reduce((a,x)=>a+(x.fixed.delay_vehicle_s-x.adaptive.delay_vehicle_s)/x.fixed.delay_vehicle_s,0)/r.length*100).toFixed(2));});
s.charts.add('bar',{position:{left:530,top:205,width:650,height:360},categories:['Valle','Pico','Desbalance','Lluvia/incidente'],series:[{name:'Reducción %',values,fill:teal}],hasLegend:false,xAxis:{tickLabelPosition:'low'},dataLabels:{showValue:true,position:'outEnd'}});
s=add('Pruebas y resultados reproducibles','42 pruebas aprobadas','Unidad, integración y sistema.\nPostgreSQL real.\nCarga y recuperación con evidencia.','La batería actual aprobó cuarenta y dos pruebas, incluyendo PostgreSQL real. Se entregan guiones de trece familias y resultados de carga y restauración. La latencia de predicción aún no cumple la meta y permanece reportada. La evaluación humana no se sustituye por pruebas automáticas. Fuentes: reports/academico y DOC_004/DOC_005.');
text(s,'90% / 100%',510,210,700,120,70,true,teal);text(s,'Ramas: controlador / validaciones',510,350,700,75,28,true,navy);text(s,'Aceptación humana y firmas:\npendientes de personas reales',510,475,700,100,28);
s=add('Demostración en tres pasos','Instalar → entrar → observar','Ejecutar scripts.run_local.\nAbrir localhost:8501.\nElegir cruce y revisar plan confirmado.','El manual contiene instalación, acceso, interpretación de modos, intervención, exportación y solución de errores. El lanzador requiere permanecer abierto y evita dos ejecuciones sobre los mismos puertos. No se muestran contraseñas en el material audiovisual.');image(s,'FIG_009_intervencion.png',500,160,720,470);
s=add('Entrega académica y límites','Documentación, código y evidencia','Memoria, diagramas y casos de uso.\nManual, guiones y resultados.\nPresentación y video reproducibles.','La entrega incluye memoria completa, casos de uso, manual, documento de pruebas, figuras, presentación y video. Sigue siendo un prototipo académico de simulación. La aceptación del docente, pruebas con personas, calibración real y despliegue municipal requieren trabajo y decisiones externas.');
text(s,'La IA pronostica.\nEl controlador valida.\nEl simulador aplica.',520,220,660,260,42,true,navy);
await fs.writeFile(path.join(out,'PRE_001_Guion.json'),JSON.stringify(slides,null,2));
await fs.writeFile(path.join(out,'PRE_001_Guion.md'),'# PRE_001 Guion de presentación y narración\n\n'+slides.map((v,i)=>`## DIA_${String(i+1).padStart(3,'0')} ${v.title}\n\n${v.notes}`).join('\n\n'));
for(let i=0;i<presentation.slides.items.length;i++){
 const blob=await presentation.export({slide:presentation.slides.items[i],format:'png',scale:1});
 await fs.writeFile(path.join(out,'diapositivas',`DIA_${String(i+1).padStart(3,'0')}.png`),new Uint8Array(await blob.arrayBuffer()));
}
const candidate=path.join(build,'PRE_001_draft.pptx');await(await PresentationFile.exportPptx(presentation)).save(candidate);
const skill='C:/Users/diego/.codex/plugins/cache/openai-primary-runtime/presentations/26.1026.10807/skills/presentations';
const {finalizePresentation}=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')).href);
await finalizePresentation({workspaceDir:root,candidatePath:candidate,finalPath:path.join(out,'PRE_001_Presentacion_v4.pptx'),
 pythonExecutable:'C:/Users/diego/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe',
 integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),
 layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),
 layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit'],
 fontPolicy:{basis:'design',families:['Arial','Aptos']},verifyArtifactToolImport:true,
 materializeLiteralChartWorkbooks:true,
 receiptPath:path.join(build,'PRE_001_validation_v4.json')});
console.log('Presentación y 14 vistas PNG generadas y validadas.');
