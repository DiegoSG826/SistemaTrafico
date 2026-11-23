import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
const {SGT_ACADEMIC_NODE_MODULES, SGT_ACADEMIC_PYTHON, SGT_PRESENTATION_SKILL}=process.env;
if(!SGT_ACADEMIC_NODE_MODULES || !SGT_ACADEMIC_PYTHON || !SGT_PRESENTATION_SKILL){
 throw new Error('Configura las rutas del runtime documental y de la habilidad de presentaciones.');
}
process.env.RUNTIME_NODE_MODULES=SGT_ACADEMIC_NODE_MODULES;
const {Presentation,PresentationFile}=await import(pathToFileURL(path.join(
 SGT_ACADEMIC_NODE_MODULES,'@oai/artifact-tool/dist/artifact_tool.mjs')).href);
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
 text(s,`PRE_001 · ${String(slides.length+1).padStart(2,'0')} · Cuauhtémoc`,64,670,1100,28,15,false,'#607680');
 s.speakerNotes.text=notes; slides.push({title,lead,body,notes}); return s;
}
let s=add('Gestión inteligente de semáforos en Cuauhtémoc','Prototipo académico verificable','Cinco cruces sintéticos\nPronóstico de demanda\nControl con restricciones','Presentamos un gestor de semáforos simulados para Cuauhtémoc. La IA anticipa llegadas; el controlador reparte verde y el simulador aplica el plan. No controla semáforos físicos ni usa aforos oficiales.');
text(s,'120 s',590,205,550,130,112,true,teal); text(s,'Un ciclo con prioridad peatonal',550,360,610,80,30,true,navy);
text(s,'40/40 fijo → reparto adaptativo validado',550,470,610,100,28);
s=add('Control simulado y tráfico real','Dos vistas en el dashboard','Simulación: demanda, fases y planes.\nTomTom: consulta del tramo vial cercano.','El generador aporta observaciones al controlador simulado. El trabajador aplica los planes al inicio del ciclo. Para mostrar tráfico real, FastAPI consulta TomTom Traffic API por separado. Fuente: DOC_001, DEV_005 y FIG_005.'); image(s,'FIG_005_arquitectura.png');
s=add('Datos sintéticos y evaluación temporal','Noventa días reproducibles','Semilla 42; cinco cruces.\nEntrenamiento 54 días, validación 18 y prueba 18.\nPurga de etiquetas futuras.','El dataset incluye horario, día, clima, historial y velocidad. La etiqueta es el promedio de llegadas de cinco minutos futuros. El pipeline separa entrenamiento y prueba. Los datos no fueron calibrados con Cuauhtémoc. Fuente: reports/model_evaluation.json y REF_005.');
text(s,'X conocido → demanda futura',530,205,650,90,37,true,teal); text(s,'Random Forest de regresión\n\nLa IA estima veh/min.\nLas reglas calculan verde y rojo.',530,330,650,240,31);
s=add('Más demanda recibe más verde','Ejemplo controlado 30/10 veh/min','Plan anterior: 40/40.\nObjetivo proporcional: 60/20.\nLímite por ciclo: ±5 s.','Con demanda prevista de treinta vehículos por minuto en norte sur y diez en este oeste, el objetivo proporcional es sesenta veinte. Desde cuarenta cuarenta se limita a cuarenta y cinco treinta y cinco. El rojo se deriva del ciclo. Este es un ejemplo de las reglas, no un resultado medido de calle.');
text(s,'45 s NS',540,190,620,85,60,true,navy); rect(s,540,290,540,58,teal);
text(s,'35 s EO',540,385,620,85,60,true,navy); rect(s,540,485,420,58,'#4C8299');
text(s,'Rojo NS 72 s · rojo EO 82 s',540,575,650,45,24);
s=add('Las restricciones siempre prevalecen','80 s de verde vehicular total','Verdes entre 20 y 60 s.\nPeatones exclusivos 20 s.\nAmarillos y despejes obligatorios.','El ciclo conserva exclusión de movimientos y una oportunidad peatonal. Automático limita la variación. Si faltan datos o IA, prevalece un plan fijo cuarenta cuarenta. Manual tiene motivo y caducidad. Los tiempos son didácticos, no reglamentarios.');
let x=510; for(const [label,seconds,color] of [['NS',40,teal],['A',3,'#D6A230'],['D',2,'#AB4A4A'],['EO',40,'#4C8299'],['A',3,'#D6A230'],['D',2,'#AB4A4A'],['PEATÓN',20,'#726299'],['D',10,'#AB4A4A']]){const w=seconds*5.3;rect(s,x,285,w,90,color);if(w>50)text(s,label,x+3,310,w-6,40,19,true,'#FFFFFF');x+=w;}
text(s,'NS → EO → peatones → nuevo ciclo',520,430,650,110,30,true,navy);
s=add('Casos de uso y trazabilidad','Once casos especificados','Acceso para administrador y lector.\nConsulta TomTom con sesión válida.','DOC_002 y FIG_003 describen once casos y cinco actores. El lector consulta, supervisa y exporta. En CU_011, el backend solicita a TomTom el tramo cercano y muestra el resultado al usuario autenticado.');image(s,'FIG_003_casos_uso.png');
s=add('Persistencia que protege la decisión','Un solo plan activo por cruce','FK y ventanas únicas.\nVersiones contra solicitudes simultáneas.\nAuditoría de antes y después.','El esquema SQL contiene intersecciones, grupos, observaciones, predicciones, modelos y planes. Un índice parcial impide dos activos y los triggers comprueban todas las fases de un plan al confirmar. El modelo entidad relación completo está en FIG_004.');
image(s,'FIG_004_bd.png',485,165,735,470);
s=add('Plan base y ampliación TomTom','Calendarización estimada','Plan base: 45 días y 5 de reserva.\nTomTom: 8 días por P–Q–S–T.','El Gantt y PERT presentan dos órdenes de trabajo estimados. Git registra el mapa actualizado el dieciséis de noviembre y TomTom integrado el veintidós. Esas fechas acreditan hitos. Fuentes: reports/pert.json y DOC_001 CAL_001 y CAL_002.');image(s,'FIG_001_gantt.png');
s=add('El monitor de simulación','Mapa, colas y tiempos','Selección de un cruce.\nAnimación y fases simuladas.\nTiempos del plan activo.','La captura FIG_008 muestra la versión actual del dashboard en una instancia temporal. El mapa permite seleccionar un cruce y el monitor muestra la animación, las fases y los tiempos del plan.');image(s,'FIG_008_monitor.png',485,160,735,480);
s=add('El modelo supera la persistencia','Error predictivo en veh/min','Prueba temporal reservada.\nLa precisión no demuestra por sí sola menor demora.','En la prueba sintética reservada, el error absoluto medio fue uno punto diecinueve vehículos por minuto, frente a uno punto cuarenta y cinco de persistencia. Esto evalúa predicción; el control requiere otro experimento. Fuente: reports/model_evaluation.json.');
s.charts.add('bar',{position:{left:530,top:205,width:650,height:360},categories:['Persistencia','Random Forest'],series:[{name:'MAE veh/min',values:[model.metrics.test.persistence.mae,model.metrics.test.model.mae].map(v=>Number(v.toFixed(4))),fill:teal}],hasLegend:false,dataLabels:{showValue:true,position:'outEnd'}});
s=add('El beneficio depende del escenario','29.37% menos demora media','Resultado sintético, no vial real.\nValle y pico empeoran ligeramente.\nDesbalance concentra el beneficio.','La evaluación usó cincuenta pares con las mismas llegadas. En escenarios no sobresaturados la reducción media de demora fue veintinueve punto treinta y siete por ciento. El resultado no es uniforme ni representa una medición en calles de Cuauhtémoc. Fuente: reports/experiment.json.');
const scenarios=['valley','peak','imbalance','rain_incident'];
const values=scenarios.map(k=>{const r=experiment.runs.filter(x=>x.scenario===k);return Number((r.reduce((a,x)=>a+(x.fixed.delay_vehicle_s-x.adaptive.delay_vehicle_s)/x.fixed.delay_vehicle_s,0)/r.length*100).toFixed(2));});
s.charts.add('bar',{position:{left:530,top:205,width:650,height:360},categories:['Valle','Pico','Desbalance','Lluvia/incidente'],series:[{name:'Reducción %',values,fill:teal}],hasLegend:false,xAxis:{tickLabelPosition:'low'},dataLabels:{showValue:true,position:'outEnd'}});
s=add('Pruebas y resultados reproducibles','Resultados por ejecución','Línea base: 42 aprobadas con PostgreSQL.\nIntegración TomTom: 44 aprobadas, 4 omitidas.','La línea base incluyó PostgreSQL, carga y restauración. La verificación TomTom obtuvo datos para los cinco puntos y recorrió ambas vistas en Edge. En esa ejecución se omitieron las pruebas PostgreSQL por falta de una base de laboratorio. Fuentes: DOC_004 y DOC_005.');
text(s,'90% / 100%',510,210,700,120,70,true,teal);text(s,'Ramas: controlador / validaciones',510,350,700,75,28,true,navy);text(s,'Aceptación humana y firmas:\npendientes de personas reales',510,475,700,100,28);
s=add('Consulta de tráfico con TomTom','Tramo vial cercano','Velocidades y tiempos.\nConfianza y cierre reportado.\nActualización cada minuto.','La captura FIG_011 muestra una consulta en vivo en la rama actual. El usuario elige un punto y puede pulsar Actualizar ahora. El backend conserva la clave de TomTom. Los planes semafóricos siguen usando las llegadas del simulador. Fuente: DOC_003 MAN_013.');
image(s,'FIG_011_tomtom.png',485,160,735,480);
s=add('Entrega académica y límites','Documentación, código y evidencia','Memoria, diagramas y casos de uso.\nManual, guiones y resultados.\nPresentación y video reproducibles.','La entrega cubre la simulación y la consulta de tráfico real por tramo con TomTom. Las cifras de demora siguen siendo de un experimento sintético. La aceptación del docente, las pruebas con personas y la calibración territorial siguen pendientes.');
text(s,'La IA pronostica.\nEl controlador valida.\nEl simulador aplica.',520,220,660,260,42,true,navy);
await fs.writeFile(path.join(out,'PRE_001_Guion.json'),JSON.stringify(slides,null,2));
await fs.writeFile(path.join(out,'PRE_001_Guion.md'),'# PRE_001 Guion de presentación y narración\n\n'+slides.map((v,i)=>`## DIA_${String(i+1).padStart(3,'0')} ${v.title}\n\n${v.notes}`).join('\n\n'));
for(let i=0;i<presentation.slides.items.length;i++){
 const blob=await presentation.export({slide:presentation.slides.items[i],format:'png',scale:1});
 await fs.writeFile(path.join(out,'diapositivas',`DIA_${String(i+1).padStart(3,'0')}.png`),new Uint8Array(await blob.arrayBuffer()));
}
const staging=await fs.mkdtemp(path.join(build,'pre001-'));
const candidate=path.join(staging,'PRE_001_draft.pptx');await(await PresentationFile.exportPptx(presentation)).save(candidate);
const published=path.join(staging,'validated');
await fs.mkdir(published);
const validated=path.join(published,'PRE_001_Presentacion_v4.pptx');
const receipt=path.join(staging,'PRE_001_validation_v4.json');
const skill=SGT_PRESENTATION_SKILL;
const {finalizePresentation}=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')).href);
await finalizePresentation({workspaceDir:root,candidatePath:candidate,finalPath:validated,
 pythonExecutable:SGT_ACADEMIC_PYTHON,explicitTotalSlideCount:14,
 integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),
 layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),
 layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit'],
 fontPolicy:{basis:'design',families:['Arial','Aptos']},verifyArtifactToolImport:true,
 materializeLiteralChartWorkbooks:true,
 receiptPath:receipt});
await fs.copyFile(validated,path.join(out,'PRE_001_Presentacion_v4.pptx'));
await fs.copyFile(receipt,path.join(build,'PRE_001_validation_v4.json'));
console.log('Presentación y 14 vistas PNG generadas y validadas.');
