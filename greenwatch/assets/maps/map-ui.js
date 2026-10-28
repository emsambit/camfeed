'use strict';
(async function(){
  const status=document.getElementById('map-status');
  if(typeof L==='undefined'){status.textContent='Offline map library unavailable.';return;}
  const map=L.map('offline-map',{preferCanvas:true,minZoom:4,maxZoom:17,attributionControl:true,fadeAnimation:false,zoomAnimation:false}).setView([12.9716,77.5946],11);
  L.control.scale({imperial:false}).addTo(map);
  map.attributionControl.setPrefix('Leaflet');
  map.attributionControl.addAttribution('© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a> · Natural Earth');
  const countries=L.layerGroup().addTo(map),roads=L.layerGroup().addTo(map),labels=L.layerGroup().addTo(map);
  let india=null,bengaluru=null,mode='bengaluru',camera=null,range=null;
  const safe=text=>{const span=document.createElement('span');span.textContent=text;return span;};
  function style(f){const k=f.properties.kind;if(k==='country')return{color:'#7da660',weight:1,fillColor:f.properties.name==='India'?'#213d26':'#10281b',fillOpacity:.8};if(k==='water')return{color:'#57a7a3',weight:.5,fillColor:'#245f5c',fillOpacity:.7};const main=/motorway|trunk|primary/.test(k);return{color:main?'#d3db81':/secondary/.test(k)?'#96be65':'#4e7954',weight:main?2:1,opacity:.85};}
  function render(){
    countries.clearLayers();roads.clearLayers();labels.clearLayers();
    if(india)L.geoJSON(india.features.filter(f=>f.geometry.type!=='Point'),{style}).addTo(countries);
    const data=mode==='bengaluru'?bengaluru:india;
    if(!data)return;
    const zoom=map.getZoom();
    const lineFeatures=data.features.filter(f=>f.geometry.type!=='Point'&&f.properties.kind!=='country');
    L.geoJSON(lineFeatures,{style,onEachFeature:(f,l)=>{if(f.properties.name)l.bindTooltip(safe(f.properties.name));}}).addTo(roads);
    for(const f of data.features){
      if(f.geometry.type!=='Point')continue;
      if(mode==='india'&&(f.properties.population||0)<(zoom<6?5000000:zoom<7?1000000:0))continue;
      if(mode==='bengaluru'&&zoom<12&&f.properties.name!=='Bengaluru'&&f.properties.name!=='Bangalore')continue;
      const [lng,lat]=f.geometry.coordinates;
      L.circleMarker([lat,lng],{radius:mode==='india'?2:1,color:'#c0e883',weight:1,fillOpacity:1}).bindTooltip(safe(f.properties.name),{permanent:true,direction:'right',className:'map-label'}).addTo(labels);
    }
    status.textContent=mode==='bengaluru'?'OFFLINE / Bengaluru road map / 12.80–13.20 N, 77.40–77.82 E':'OFFLINE / India overview / generalized boundaries and city labels';
  }
  try{
    const responses=await Promise.all([fetch('/assets/maps/india.geojson'),fetch('/assets/maps/bengaluru.geojson')]);
    if(responses.some(r=>!r.ok))throw Error('Missing map data');
    [india,bengaluru]=await Promise.all(responses.map(r=>r.json()));render();
  }catch(e){status.textContent='Offline map data could not load. Check the Pi connection.';}
  document.getElementById('bengaluru-view').onclick=()=>{mode='bengaluru';map.setView([12.9716,77.5946],11);render();};
  document.getElementById('india-view').onclick=()=>{mode='india';map.fitBounds([[5.5,67],[37.7,98.5]]);render();};
  map.on('zoomend',render);
  const field=document.getElementById('coordinates');
  field.oninput=()=>field.setCustomValidity('');
  document.getElementById('location').onsubmit=e=>{
    e.preventDefault();const parts=field.value.split(',').map(s=>s.trim()),nums=parts.map(Number);
    if(parts.length!==2||parts.some(s=>!s)||nums.some(n=>!Number.isFinite(n))||Math.abs(nums[0])>90||Math.abs(nums[1])>180){field.setCustomValidity('Enter valid latitude, longitude.');field.reportValidity();return;}
    if(camera)map.removeLayer(camera);if(range)map.removeLayer(range);
    camera=L.circleMarker(nums,{radius:6,color:'#f4ffd9',fillColor:'#b5ff63',fillOpacity:1}).bindTooltip('Camera / manual pin',{permanent:true,direction:'top'}).addTo(map);
    range=L.circle(nums,{radius:50,color:'#b5ff63',weight:1,fillOpacity:.1}).bindTooltip('50 m reference radius / detection range uncalibrated').addTo(map);
    mode='bengaluru';map.setView(nums,15);render();
  };
})();
