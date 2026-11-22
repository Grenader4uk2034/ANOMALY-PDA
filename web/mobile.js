(() => {
 const menu = document.getElementById("mobile-menu");
 const objects = document.getElementById("mobile-objects");
 const dossier = document.getElementById("mobile-dossier");
 const overlay = document.getElementById("mobile-overlay");
 const panels = [
  document.querySelector(".filters-panel"),
  document.querySelector(".list-panel"),
  document.querySelector(".detail-panel")
 ];

 function closePanels(){
  panels.forEach(p=>p?.classList.remove("mobile-open"));
  overlay.classList.remove("active");
 }

 function openPanel(panel){
  closePanels();
  if(!panel)return;
  panel.classList.add("mobile-open");
  overlay.classList.add("active");
 }

 menu?.addEventListener("click",()=>openPanel(panels[0]));
 objects?.addEventListener("click",()=>openPanel(panels[1]));
 dossier?.addEventListener("click",()=>openPanel(panels[2]));
 overlay?.addEventListener("click",closePanels);

 document.addEventListener("keydown",e=>{
  if(e.key==="Escape")closePanels();
 });

 document.querySelector("#level")?.addEventListener("change",closePanels);
})();
