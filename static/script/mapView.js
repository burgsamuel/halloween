//////////////////////////////////////////////////
// Setup Map
// ///////////////////////////////////////////////

const map = L.map("map").setView([-30.000, 135.0000], 4);

L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 20,
  attribution:
    '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>',
}).addTo(map);



//////////////////////////////////////////////////
// Load user location
// ///////////////////////////////////////////////

function getLocation() {


  if (navigator.geolocation) {
    id = navigator.geolocation.getCurrentPosition(showPosition);
  } else {
    x.innerHTML = "Geolocation is not supported by this browser.";
  }
}

async function showPosition(position) {
  lat = position.coords.latitude;
  lon = position.coords.longitude;

  timeStamp = position.timestamp / 1000;

  map.flyTo(new L.LatLng(lat, lon), 15);


}



//////////////////////////////////////////////////
// Load points from server onto map for each user
// ///////////////////////////////////////////////

let totalSpotCounter = 0;

async function onload() {

    let response = await fetch("/mapData")
    let data = await response.json()

    totalSpotCounter = data.length;
    updateSpotSpan();

    for (let i = 0; i < data.length - 1; i++) {
        let dataIconUrl = data[i].iconurl;
        let timeof = new Date(data[i].timestamp * 1000);
        let userIcon = L.icon({
        iconUrl: dataIconUrl,
        iconSize: [25, 25],
        iconAnchor: [10, 10],
        popupAnchor: [-3, -76],
        });

    marker = new L.marker([data[i].latitude, data[i].longitude], {
    icon: userIcon,
    title: `User:${data[i].userid} Time:${timeof}`,
    }).addTo(map);
}

getLocation();

}

onload();



//////////////////////////////////////////////////
// load users spot count
// ///////////////////////////////////////////////

const spotCounterSpan = document.getElementById('spot-counter-span');

function updateSpotSpan(){

        spotCounterSpan.innerText = `Total Spots: ${totalSpotCounter}`;
  
  }
  
