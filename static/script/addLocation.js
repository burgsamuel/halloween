const locateMeButton = document.getElementById('locate-me-button');
const saveLocationButton = document.getElementById('save-location-button')
const statusSpan = document.getElementById('status-span')

let saveLocationFlag = true;


let iconName = "candy-icon";
const hatIcon = document.getElementById("hat-icon");
const pumpkinIcon = document.getElementById("pumpkin-icon");
const witchIcon = document.getElementById("witch-icon");
const candyIcon = document.getElementById("candy-icon");
candyIcon.style.backgroundColor = 'red';

const iconArray = [
  {
    name: "hat-icon",
    url: "https://cdn-icons-png.flaticon.com/128/1235/1235127.png",
  },
  {
    name: "pumpkin-icon",
    url: "https://cdn-icons-png.flaticon.com/128/685/685842.png",
  },
  {
    name: "witch-icon",
    url: "https://cdn-icons-png.flaticon.com/128/218/218200.png",
  },
  {
    name: "candy-icon",
    url: "https://cdn-icons-png.flaticon.com/128/6433/6433176.png",
  },
  {
    name: "blob-icon",
    url: "https://cdn-icons-png.flaticon.com/128/238/238296.png",
  },
];

iconSelect(iconName);

let timeStamp = null;
let userIconUrl = "https://cdn-icons-png.flaticon.com/128/6433/6433176.png";
let lat = null;
let lon = null;

let id;

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
// Load user location
// ///////////////////////////////////////////////

function getLocation() {
    locateMeButton.textContent = "Loading";
    statusSpan.innerText = "Locating you - Stand outside for best results "


  if (navigator.geolocation) {
    id = navigator.geolocation.watchPosition(showPosition);
  } else {
    x.innerHTML = "Geolocation is not supported by this browser.";
  }
}

async function showPosition(position) {
  lat = position.coords.latitude;
  lon = position.coords.longitude;

  timeStamp = position.timestamp / 1000;

  map.flyTo(new L.LatLng(lat, lon), 17);

  locateMeButton.textContent = "Please Wait"

  for (let i = 0; i < iconArray.length; i++) {
    if (iconArray[i].name == iconName) {
      userIconUrl = iconArray[i].url;
    }
  }

  try {
    map.removeLayer(marker_new);
  } catch {}

  let newIcon = L.icon({
    iconUrl: userIconUrl,
    iconSize: [25, 25],
    iconAnchor: [10, 10],
    popupAnchor: [-3, -76],
  });
  marker_new = new L.marker([lat, lon], {
    icon: newIcon,
    title: `${userId}`,
  }).addTo(map);
      locateMeButton.textContent = "Located"
      statusSpan.innerText = "Located - Check for Accuracy and click 'Save My Spot - Adjust by clicking on map'"
}




function iconSelect(imageId) {
  for (let i = 0; i < iconArray.length; i++) {
    if (iconArray[i].name == imageId) {

        iconName = iconArray[i].name;
        let iconSelected = document.getElementById(iconArray[i].name);
        iconSelected.style.backgroundColor = "red";

    } else {
        let iconUnSelected = document.getElementById(iconArray[i].name);
        iconUnSelected.style.backgroundColor = "rgba(250, 250, 250, 0)";
    }
  }
}

//////////////////////////////////////////////////
// Load a user id if not already loaded
// ///////////////////////////////////////////////

let userId = null;

if (localStorage.getItem("id343445432") == null) {
  userId = generateId();
  localStorage.setItem("id343445432", JSON.stringify(userId));
} else {
  userId = JSON.parse(localStorage.getItem("id343445432"));
}

function generateId() {
  const id = Math.floor(Math.random() * 999999999999);
  return id;
}



async function saveLocation() {
  
  
  if (saveLocationFlag && lat !== null && lon !== null) {
    
    saveLocationButton.textContent ="Saving"
    // Set icon name and url for database
    for (let i = 0; i < iconArray.length; i++) {
      if (iconArray[i].name == iconName) {
        userIconUrl = iconArray[i].url;
      }
    }
  
    try {
      // Create request to api
      const req = await fetch('/locationData', {
          method: 'POST',
          headers: { 'Content-Type':'application/json' },
          
          // data
          body: JSON.stringify({
              id: userId,
              time_stamp: timeStamp,
              lat: lat,
              lon: lon,
              iconUrl: userIconUrl,
          }),
      });
      
      const res = await req.json();
  
      // Log success message
      saveLocationButton.textContent =" Saved 👍"  
      setTimeout(() => {
        saveLocationButton.textContent ="Save My Spot" 
        saveLocationFlag = true;
      }, 4000)
      setTimeout(() => {
        statusSpan.innerText = `Click View Map at the top for locations` 
      }, 3000)
      statusSpan.innerText = `${res.Status}`            
  } catch(err) {
      console.error(`ERROR: ${err}`);
  }
  }
  else{
    saveLocationButton.textContent ="Click ☝️ First"
    setTimeout(() => {
    saveLocationButton.textContent ="Save My Spot"
    }, 3000)

  }

  saveLocationFlag = false;
}


let popup = L.popup();

function onMapClick(e) {
    popup
        .setLatLng(e.latlng)
        .setContent("If you Happy with location Click Save My Spot below")
        .openOn(map);
        lat = e.latlng.lat
        lon = e.latlng.lng
        addMarker(lat, lon);
}

map.on('click', onMapClick);




function addMarker(lat, lon) {


  for (let i = 0; i < iconArray.length; i++) {
    if (iconArray[i].name == iconName) {
      userIconUrl = iconArray[i].url;
    }
  }

  try {
    map.removeLayer(marker_new);
  } catch {}

  let newIcon = L.icon({
    iconUrl: userIconUrl,
    iconSize: [25, 25],
    iconAnchor: [10, 10],
    popupAnchor: [-3, -76],
  });
  marker_new = new L.marker([lat, lon], {
    icon: newIcon,
    title: `${userId}`,
  }).addTo(map);
}