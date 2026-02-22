// frontend/app.js
const map = L.map('map').setView([28.6448, 77.2167], 10); // Delhi center
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 19
}).addTo(map);

let marker;
function colorByCategory(cat) {
  switch(cat) {
    case 'Good': return 'green';
    case 'Moderate': return 'orange';
    case 'Unhealthy': return 'red';
    case 'Very Unhealthy': return 'purple';
    case 'Hazardous': return 'maroon';
    default: return 'gray';
  }
}

fetch('http://localhost:8000/aqi?lat=12.97&lon=77.59')
  .then(res => res.json())
  .then(data => {
    document.getElementById('result').innerText = JSON.stringify(data, null, 2);
  })
  .catch(err => console.error(err));

map.on('click', async function(e) {
  const lat = e.latlng.lat;
  const lon = e.latlng.lng;
  document.getElementById('info').innerText = 'Querying AQI...';
  try {
    const res = await fetch(`http://localhost:8000/aqi?lat=${lat}&lon=${lon}`);
    const json = await res.json();
    if (marker) map.removeLayer(marker);
    const cat = json.aqi_category || 'Unknown';
    marker = L.circleMarker([json.lat, json.lon], {
      radius: 12,
      color: colorByCategory(cat),
      fillOpacity: 0.6
    }).addTo(map);
    marker.bindPopup(`<b>PM2.5:</b> ${json.pm25.toFixed(1)} µg/m³<br><b>Category:</b> ${cat}<br>
      <b>Sources:</b><br>
      Stubble ${(json.source_contribution.stubble_frac*100).toFixed(0)}%,
      Traffic ${(json.source_contribution.traffic_frac*100).toFixed(0)}%,
      Industry ${(json.source_contribution.industry_frac*100).toFixed(0)}%`
    ).openPopup();
    document.getElementById('info').innerText = `Nearest station: ${json.lat.toFixed(4)},${json.lon.toFixed(4)} — PM2.5 ${json.pm25.toFixed(1)} µg/m³`;
  } catch (err) {
    document.getElementById('info').innerText = 'Error fetching AQI. Ensure backend is running on port 8000 (CORS allowed).';
    console.error(err);
  }
});

