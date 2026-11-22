(() => {
"use strict";
const $ = id => document.getElementById(id);
const canvas=$("map"),ctx=canvas.getContext("2d");
const state={data:null,level:"",categories:new Set(),selected:null,zoom:1,panX:0,panY:0,drag:null,view:null,baseImage:null,baseImageLevel:null,imageUrl:null,imageBounds:{minX:-600,maxX:600,minZ:-600,maxZ:600},uiBound:false,referenceEntities:null};
const autoMapCatalog={
fake_start:"map_fake_start.png",
jupiter:"map_jupiter.png",
jupiter_underground:"map_jupiter_underground.png",
k00_marsh:"map_marsh.png",
k01_darkscape:"map_k01_darkscape.png",
k02_trucks_cemetery:"map_k02_trucks_cemetery.png",
l01_escape:"map_escape.png",
l02_garbage:"map_garbage.png",
l03_agroprom:"map_agroprom.png",
l03u_agr_underground:"map_l03u_agr_underground.png",
l04_darkvalley:"map_l04_darkvalley.png",
l04u_labx18:"map_l04u_labx18.png",
l05_bar:"map_l05_bar.png",
l06_rostok:"map_l06_rostok.png",
l07_military:"map_l07_military.png",
l08_yantar:"map_l08_yantar.png",
l08u_brainlab:"map_l08u_brainlab.png",
l09_deadcity:"map_l09_deadcity.png",
l10_limansk:"map_limansk.png",
l10_radar:"map_l10_radar.png",
l10_red_forest:"map_red_forest.png",
l11_hospital:"map_hospital.png",
l11_pripyat:"map_l11_pripyat.png",
l12_stancia:"map_l12_stancia.png",
l12_stancia_2:"map_stancia_2.png",
l12u_control_monolith:"map_l12u_control_monolith.png",
l13_generators:"map_l13_generators.png",
labx8:"map_labx8.png",
pripyat:"map_pripyat.png",
y04_pole:"map_y04_pole.png",
zaton:"map_zaton.png"
};

let autoMapRequestId=0;
function loadAutoMap(){
 const requestId=++autoMapRequestId;
 const file=autoMapCatalog[state.level];
 if(!file){
  state.baseImage=null;
  state.baseImageLevel=null;
  draw();
  return;
 }
 const img=new Image();
 img.onload=()=>{
  if(requestId!==autoMapRequestId)return;
  state.baseImage=img;
  state.baseImageLevel=state.level;
  const v=extent(levelFeatures());
  state.imageBounds={minX:v.minX,maxX:v.maxX,minZ:v.minZ,maxZ:v.maxZ};
  draw();
 };
 img.onerror=()=>{
  if(requestId!==autoMapRequestId)return;
  state.baseImage=null;
  state.baseImageLevel=null;
  draw();
 };
 img.src="./maps/"+file;
}
const colors={stash:"#d5b36d",anomaly:"#d96d55",population:"#7ea9c8",mutant:"#bd7bc4",npc:"#91bd83",camp:"#e0a45f",transition:"#71c6b4",poi:"#aab4a7"};
const fmt=n=>Number(n).toLocaleString("ru-RU",{maximumFractionDigits:2});
function resize(){const r=canvas.getBoundingClientRect(),dpr=window.devicePixelRatio||1;canvas.width=Math.max(1,Math.round(r.width*dpr));canvas.height=Math.max(1,Math.round(r.height*dpr));ctx.setTransform(dpr,0,0,dpr,0,0);draw()}
function levelFeatures(){return state.data.features.filter(f=>f.properties.level===state.level)}
function visibleFeatures(){const q=$("search").value.trim().toLowerCase();return levelFeatures().filter(f=>state.categories.has(f.properties.category)&&(!q||[f.properties.name,f.properties.section,f.properties.category_label].join(" ").toLowerCase().includes(q)))}
function extent(items){let xs=items.map(f=>f.properties.x),zs=items.map(f=>f.properties.z);let minX=Math.min(...xs),maxX=Math.max(...xs),minZ=Math.min(...zs),maxZ=Math.max(...zs);if(minX===maxX){minX-=1;maxX+=1}if(minZ===maxZ){minZ-=1;maxZ+=1}const dx=maxX-minX,dz=maxZ-minZ;return{minX:minX-dx*.06,maxX:maxX+dx*.06,minZ:minZ-dz*.06,maxZ:maxZ+dz*.06}}
function transform(){const w=canvas.clientWidth,h=canvas.clientHeight,cx=w/2+state.panX,cy=h/2+state.panY;if(state.baseImage&&state.baseImageLevel===state.level){const scale=Math.min(w/state.baseImage.width,h/state.baseImage.height)*state.zoom;return{w,h,scale,cx,cy,image:true}}const v=state.view||extent(levelFeatures());const scale=Math.min(w/(v.maxX-v.minX),h/(v.maxZ-v.minZ))*state.zoom;return{w,h,scale,cx,cy,centerX:(v.minX+v.maxX)/2,centerZ:(v.minZ+v.maxZ)/2}}
function point(f,t){if(t.image){const b=state.imageBounds,px=(f.properties.x-b.minX)/(b.maxX-b.minX)*state.baseImage.width,py=(b.maxZ-f.properties.z)/(b.maxZ-b.minZ)*state.baseImage.height;return{x:t.cx+(px-state.baseImage.width/2)*t.scale,y:t.cy+(py-state.baseImage.height/2)*t.scale}}return{x:t.cx+(f.properties.x-t.centerX)*t.scale,y:t.cy-(f.properties.z-t.centerZ)*t.scale}}
function draw(){if(!ctx)return;const w=canvas.clientWidth,h=canvas.clientHeight;ctx.clearRect(0,0,w,h);if(!state.data||!state.level)return;const all=levelFeatures();if(!all.length){ctx.fillStyle="#a5b39f";ctx.textAlign="center";ctx.fillText("Для этой локации нет объектов в наборе данных",w/2,h/2);return}
const t=transform();if(t.image){ctx.save();ctx.imageSmoothingEnabled=true;ctx.drawImage(state.baseImage,t.cx-state.baseImage.width*t.scale/2,t.cy-state.baseImage.height*t.scale/2,state.baseImage.width*t.scale,state.baseImage.height*t.scale);ctx.restore()}ctx.save();ctx.strokeStyle="#344737";ctx.lineWidth=1;ctx.setLineDash([3,7]);for(let x=0;x<w;x+=48){ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,h);ctx.stroke()}for(let y=0;y<h;y+=48){ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(w,y);ctx.stroke()}ctx.setLineDash([]);
for(const f of visibleFeatures()){const p=point(f,t),cat=f.properties.category;ctx.beginPath();ctx.arc(p.x,p.y,f===state.selected?7:4.2,0,Math.PI*2);ctx.fillStyle=colors[cat]||colors.poi;ctx.globalAlpha=.88;ctx.fill();ctx.globalAlpha=1;if(f===state.selected){ctx.strokeStyle="#f0f5e8";ctx.lineWidth=2;ctx.stroke();ctx.beginPath();ctx.arc(p.x,p.y,11,0,Math.PI*2);ctx.strokeStyle=colors[cat]||colors.poi;ctx.stroke()}}
ctx.restore();$("count").textContent=visibleFeatures().length.toLocaleString("ru-RU")+" / "+all.length.toLocaleString("ru-RU")+" объектов";$("map-title").textContent=state.level.toUpperCase().replaceAll("_"," ")}
function renderList(){const list=$("object-list"),items=visibleFeatures();list.replaceChildren();if(!items.length){list.innerHTML='<div class="empty">По заданным условиям ничего не найдено.</div>';return}const frag=document.createDocumentFragment();for(const f of items){const p=f.properties,el=document.createElement("div");el.className="item"+(f===state.selected?" active":"");const name=document.createElement("div");name.className="item-name";name.textContent=p.name||p.section;const meta=document.createElement("div");meta.className="item-meta";meta.textContent=(p.category_label||p.category)+" · X "+fmt(p.x)+" / Z "+fmt(p.z);el.append(name,meta);el.addEventListener("click",()=>select(f,true));frag.append(el)}list.append(frag);}
function select(f,center=false){state.selected=f;const p=f.properties;$("detail").replaceChildren();const h=document.createElement("h2");h.textContent=p.name||p.section;const tag=document.createElement("span");tag.className="tag";tag.textContent=p.category_label||p.category;$("detail").append(h,tag);const kv=document.createElement("div");kv.className="kv";const values=[["Секция",p.section],["Локация",p.level],["Координата X",fmt(p.x)],["Высота Y",fmt(p.y)],["Координата Z",fmt(p.z)],["Game vertex",p.game_vertex_id??"—"],["Level vertex",p.level_vertex_id??"—"]];for(const [k,v] of values){const d=document.createElement("div"),s=document.createElement("small"),b=document.createElement("b");s.textContent=k;b.textContent=v;d.append(s,b);kv.append(d)}$("detail").append(kv);renderList();if(center){state.panX=0;state.panY=0;state.zoom=Math.max(1.5,state.zoom);draw()}}
function init(data){if(!data||!Array.isArray(data.features))throw Error("Неверный формат карты: ожидался массив features.");state.data=data;state.categories.clear();state.selected=null;const levels=Object.keys(data.metadata?.levels||{}).sort((a,b)=>a.localeCompare(b,"ru"));if(!levels.length)throw Error("В наборе нет локаций.");const level=$("level");level.replaceChildren();for(const name of levels){const o=document.createElement("option");o.value=name;o.textContent=name.replaceAll("_"," ");level.append(o)}state.level=levels.includes("jupiter")?"jupiter":levels[0];level.value=state.level;loadAutoMap();level.disabled=false;$("search").disabled=false;const counts=data.metadata?.categories||{};const filters=$("filters");filters.replaceChildren();for(const cat of Object.keys(counts).sort()){state.categories.add(cat);const label=document.createElement("label");label.className="filter";const cb=document.createElement("input");cb.type="checkbox";cb.checked=true;cb.value=cat;cb.addEventListener("change",()=>{cb.checked?state.categories.add(cat):state.categories.delete(cat);renderList();draw()});const span=document.createElement("span");span.textContent=(data.metadata?.category_labels||{})[cat]||cat;label.append(cb,span);filters.append(label)}if(!state.uiBound){bindUi();state.uiBound=true}$("detail").innerHTML='<div class="empty">Выберите точку на карте или объект в списке.</div>';renderList();draw()}
function bindUi(){const level=$("level");level.addEventListener("change",()=>{state.level=level.value;loadAutoMap();state.selected=null;state.zoom=1;state.panX=0;state.panY=0;state.view=null;$("detail").innerHTML='<div class="empty">Выберите точку на карте или объект в списке.</div>';renderList();draw()});$("search").addEventListener("input",()=>{renderList();draw()});$("zoom-in").onclick=()=>{state.zoom=Math.min(20,state.zoom*1.25);draw()};$("zoom-out").onclick=()=>{state.zoom=Math.max(.5,state.zoom/1.25);draw()};$("reset").onclick=()=>{state.zoom=1;state.panX=0;state.panY=0;draw()}}
function readBundledJson(path){return new Promise((resolve,reject)=>{const xhr=new XMLHttpRequest();xhr.open("GET",path,true);xhr.responseType="text";xhr.onload=()=>{if(xhr.status!==200&&xhr.status!==0){reject(Error("HTTP "+xhr.status+" при чтении "+path));return}try{resolve(JSON.parse(xhr.responseText))}catch(error){reject(Error("Повреждён JSON "+path+": "+error.message))}};xhr.onerror=()=>reject(Error("Не удалось прочитать встроенный файл "+path));xhr.onabort=()=>reject(Error("Чтение встроенного файла отменено: "+path));xhr.send()})}
async function getReferenceEntities(){if(Array.isArray(state.referenceEntities))return state.referenceEntities;state.referenceEntities=await readBundledJson("./data/reference/stashes_and_poi.json");if(!Array.isArray(state.referenceEntities)||!state.referenceEntities.length)throw Error("Встроенный справочник пуст или имеет неверный формат");return state.referenceEntities}
function buildReferenceFallback(records){const labels={stash:"Тайники и контейнеры",quest:"Квестовые точки",weapon:"Оружие и уникальные предметы",special:"Особые точки",vehicle:"Транспорт",poi:"Другие объекты"};const categories={},levels={},features=[];for(let i=0;i<records.length;i++){const r=records[i],type=String(r.type||"special").toLowerCase(),category=type==="treasure"||type==="secret"?"stash":["quest","weapon","special"].includes(type)?type:"poi";categories[category]=(categories[category]||0)+1;levels[r.level]=(levels[r.level]||0)+1;features.push({type:"Feature",id:"reference-"+i,geometry:{type:"Point",coordinates:[r.x,r.z]},properties:{id:"reference-"+i,name:r.name,section:category==="stash"?"inventory_box":"reference_"+type,level:r.level,category,category_label:labels[category]||labels.poi,source_kind:"reference_export",reference_type:type,x:r.x,y:r.y,z:r.z}})}return{type:"FeatureCollection",metadata:{source:"stashes_and_poi.json (reference-only fallback)",entity_count:features.length,levels,categories,category_labels:labels},features}}
function classifySpawn(section,name){section=String(section||"").toLowerCase();name=String(name||"").toLowerCase();if(["inventory_box","hidden_box","inv_backpack"].includes(section))return"stash";if(section==="anomal_zone"||section.startsWith("zone_")||section.includes("anomal"))return"anomaly";if(section==="smart_terrain")return"population";if(["campfire","campfire_burn"].includes(section))return"camp";if(section==="level_changer")return"transition";if(["m_trader","m_lesnik"].includes(section)||["stalker","actor","trader","squad"].some(x=>section.startsWith(x)))return"npc";if(section==="m_car")return"vehicle";if(section.startsWith("m_")||["bloodsucker","pseudodog","snork","controller","chimera","boar","flesh","dog","zombie","tushkano","poltergeist","gigant","fracture","burer","cat"].some(x=>section.includes(x)))return"mutant";if(["stash","treasure","secret","inventory_box"].some(x=>name.includes(x)))return"stash";return"poi"}
function buildMapDataFromSpawn(source,references){if(!source||!Array.isArray(source.entities))throw Error("В JSON отсутствует массив entities.");const labels={stash:"Тайники и контейнеры",anomaly:"Аномалии",population:"Точки симуляции",mutant:"Мутанты",npc:"Персонажи",camp:"Лагеря и костры",transition:"Переходы между уровнями",quest:"Квестовые точки",weapon:"Оружие и уникальные предметы",special:"Особые точки",vehicle:"Транспорт",poi:"Другие объекты"};const features=[],seen=new Set(),categories={},levels={};let skipped=0,spawnCount=0,referenceCount=0;const add=f=>{const p=f.properties,key=[p.level,p.name,p.x,p.y,p.z].map((v,i)=>i>1?Number(v).toFixed(3):v).join("|");if(seen.has(key))return;seen.add(key);features.push(f);categories[p.category]=(categories[p.category]||0)+1;levels[p.level]=(levels[p.level]||0)+1;if(p.source_kind==="spawn")spawnCount++;else referenceCount++};for(let i=0;i<source.entities.length;i++){const e=source.entities[i];if(!e||typeof e!=="object"||!Array.isArray(e.position)||e.position.length<3||typeof e.level!=="string"||!e.level||typeof e.section!=="string"||!e.section){skipped++;continue}const xyz=e.position.slice(0,3).map(Number);if(!xyz.every(Number.isFinite)){skipped++;continue}const name=typeof e.name==="string"&&e.name?e.name:e.section,category=classifySpawn(e.section,name),[x,y,z]=xyz,id="spawn-"+i;add({type:"Feature",id,geometry:{type:"Point",coordinates:[x,z]},properties:{id,name,section:e.section,level:e.level,category,category_label:labels[category],source_kind:"spawn",x,y,z,game_vertex_id:e.game_vertex_id??null,level_vertex_id:e.level_vertex_id??null}})}const refs=buildReferenceFallback(references||[]);for(const f of refs.features)add(f);features.sort((a,b)=>a.properties.level.localeCompare(b.properties.level)||a.properties.category.localeCompare(b.properties.category)||a.properties.name.localeCompare(b.properties.name));return{type:"FeatureCollection",metadata:{source:"all_entities.json + stashes_and_poi.json",entity_count:features.length,spawn_entity_count:spawnCount,reference_entity_count:referenceCount,skipped_count:skipped,levels,categories,category_labels:labels},features}}
async function load(){try{const data=await readBundledJson("./data/map-data.json");init(data);$("load-error").style.display="none";return}catch(primaryError){try{const records=await getReferenceEntities();const data=buildReferenceFallback(records);init(data);$("load-error").style.display="none";$("count").textContent=records.length.toLocaleString("ru-RU")+" справочных объектов · сокращённый набор";$("map-title").textContent=state.level.toUpperCase().replaceAll("_"," ")}catch(fallbackError){const box=$("load-error");box.style.display="block";box.textContent="Не удалось прочитать встроенную базу объектов. "+fallbackError.message;$("map-title").textContent="НЕТ ДАННЫХ";$("count").textContent="База объектов недоступна"}}}
// ===== MOBILE_PINCH_ZOOM =====
const mobilePointers = new Map();
let mobilePinch = null;

canvas.addEventListener("pointerdown", e => {
    if (e.pointerType !== "touch") return;

    mobilePointers.set(e.pointerId, {x:e.clientX, y:e.clientY});

    if (mobilePointers.size === 2) {
        const pts = [...mobilePointers.values()];
        const rect = canvas.getBoundingClientRect();
        const cx = (pts[0].x + pts[1].x) / 2 - rect.left;
        const cy = (pts[0].y + pts[1].y) / 2 - rect.top;

        mobilePinch = {
            distance: Math.hypot(pts[1].x - pts[0].x, pts[1].y - pts[0].y),
            zoom: state.zoom,
            panX: state.panX,
            panY: state.panY,
            cx, cy
        };

        state.drag = null;
        canvas.classList.remove("dragging");
        e.preventDefault();
        e.stopImmediatePropagation();
    }
}, true);

canvas.addEventListener("pointermove", e => {
    if (!mobilePointers.has(e.pointerId)) return;

    mobilePointers.set(e.pointerId, {x:e.clientX, y:e.clientY});

    if (!mobilePinch || mobilePointers.size < 2) return;

    const pts = [...mobilePointers.values()];
    const rect = canvas.getBoundingClientRect();
    const distance = Math.max(1, Math.hypot(
        pts[1].x - pts[0].x,
        pts[1].y - pts[0].y
    ));

    const cx = (pts[0].x + pts[1].x) / 2 - rect.left;
    const cy = (pts[0].y + pts[1].y) / 2 - rect.top;

    const ratio = distance / mobilePinch.distance;
    const oldZoom = mobilePinch.zoom;
    const newZoom = Math.max(0.5, Math.min(20, oldZoom * ratio));
    const actualRatio = newZoom / oldZoom;
    const centerX = rect.width / 2;
    const centerY = rect.height / 2;

    state.zoom = newZoom;
    state.panX = mobilePinch.panX + (cx - mobilePinch.cx)
        + (mobilePinch.cx - centerX - mobilePinch.panX) * (1 - actualRatio);
    state.panY = mobilePinch.panY + (cy - mobilePinch.cy)
        + (mobilePinch.cy - centerY - mobilePinch.panY) * (1 - actualRatio);

    draw();
    e.preventDefault();
    e.stopImmediatePropagation();
}, true);

canvas.addEventListener("pointerup", e => {
    if (!mobilePointers.has(e.pointerId)) return;

    mobilePointers.delete(e.pointerId);

    if (mobilePinch) {
        mobilePinch = null;
        state.drag = null;
        canvas.classList.remove("dragging");
        e.preventDefault();
        e.stopImmediatePropagation();
    }
}, true);

canvas.addEventListener("pointercancel", e => {
    mobilePointers.delete(e.pointerId);
    mobilePinch = null;
    state.drag = null;
    canvas.classList.remove("dragging");
}, true);
// ===== END MOBILE_PINCH_ZOOM =====
canvas.addEventListener("pointerdown",e=>{state.drag={x:e.clientX,y:e.clientY,px:state.panX,py:state.panY};canvas.setPointerCapture(e.pointerId);canvas.classList.add("dragging")});
canvas.addEventListener("pointermove",e=>{if(!state.drag)return;state.panX=state.drag.px+e.clientX-state.drag.x;state.panY=state.drag.py+e.clientY-state.drag.y;draw()});
canvas.addEventListener("pointerup",e=>{if(!state.drag)return;const moved=Math.hypot(e.clientX-state.drag.x,e.clientY-state.drag.y);state.drag=null;canvas.classList.remove("dragging");if(moved>5)return;const rect=canvas.getBoundingClientRect(),t=transform(),x=e.clientX-rect.left,y=e.clientY-rect.top;let best=null,dist=15;for(const f of visibleFeatures()){const p=point(f,t),d=Math.hypot(p.x-x,p.y-y);if(d<dist){dist=d;best=f}}if(best)select(best)});
canvas.addEventListener("wheel",e=>{e.preventDefault();state.zoom=Math.max(.5,Math.min(20,state.zoom*(e.deltaY<0?1.12:.89)));draw()},{passive:false});
window.addEventListener("resize",resize);resize();load();
})();



