//////////////////////////////////////////////////
// Setup Map
// ///////////////////////////////////////////////

const map = L.map("map").setView([-32.709833, 151.465124], 8);

L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 19,
  attribution:
    '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>',
}).addTo(map);



//////////////////////////////////////////////////
// Load points from server onto map for each user
// ///////////////////////////////////////////////

async function onload() {

    let response = await fetch("/mapData")
    let data = await response.json()

    console.log(data)

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
}

onload();