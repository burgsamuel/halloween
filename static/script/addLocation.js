const saveLocationButton = document.getElementById('save-location-button');
const statusSpan = document.getElementById('status-span');
const trackerButton = document.getElementById('tacker-button');
const deleteButton = document.getElementById('delete-button');
deleteButton.style.visibility = 'hidden';

const spotCounterSpan = document.getElementById('spot-counter-span');

let saveLocationFlag = true;
let autoTracking = true;

let spotCounter = 0;

let wakeLock = null;


//////////////////////////////////////////////////
// Set Up Icon Informaiton
// ///////////////////////////////////////////////
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

let id; // geolocation id




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

    statusSpan.innerText = "Locating you - Stand outside for best results "

    autoTracking = true;

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
      statusSpan.innerText = "If Location is **NOT** correct click the map in the correct spot'"
}

getLocation();



//////////////////////////////////////////////////
// Selecting ICONs
// ///////////////////////////////////////////////

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



//////////////////////////////////////////////////
// Updating total Spots and display
// ///////////////////////////////////////////////


function spotCounterAdd() {

  // Keeping track of total spots for each user
  if (localStorage.getItem("spotCounter") == null) {
    localStorage.setItem("spotCounter", JSON.stringify(spotCounter));
    spotCounter++;
    localStorage.setItem("spotCounter", JSON.stringify(spotCounter));
  } else {
    spotCounter = JSON.parse(localStorage.getItem("spotCounter"));
    spotCounter++;
    localStorage.setItem("spotCounter", JSON.stringify(spotCounter));
  }

}

function updateSpotSpan(){

  if (localStorage.getItem("spotCounter") == null) {
    localStorage.setItem("spotCounter", JSON.stringify(spotCounter));
  } 
  else {
    let counter = JSON.parse(localStorage.getItem("spotCounter"));

    if (counter > 0) {
      spotCounterSpan.innerText = `Your Spots: ${counter}`;
    }
    else {
      spotCounterSpan.innerText = '';
    }
  }

}

updateSpotSpan();

//////////////////////////////////////////////////
// Saving the Users Location
// ///////////////////////////////////////////////

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


      //persist icon on saved locations
      let newIcon = L.icon({
        iconUrl: userIconUrl,
        iconSize: [25, 25],
        iconAnchor: [10, 10],
        popupAnchor: [-3, -76],
      });
      savedMarker = new L.marker([lat, lon], {
        icon: newIcon,
        title: `${userId}`,
      }).addTo(map);

      popup.removeFrom(map);

      // Udpating to spot counters for user to see;
      spotCounterAdd();
      updateSpotSpan();

      if (spotCounter > 0) {
        deleteButton.style.visibility = 'visible';
      }
      

  } catch(err) {
      console.error(`ERROR: ${err}`);
  }
  }
  else{
    saveLocationButton.textContent ="Please Wait";
    setTimeout(() => {
    saveLocationButton.textContent ="Save My Spot";
    }, 3000)

  }


  saveLocationFlag = false;
}




//////////////////////////////////////////////////
// Adding spots manuallay to map
// ///////////////////////////////////////////////

let popup = L.popup();

function onMapClick(e) {

    navigator.geolocation.clearWatch(id);
    autoTracking = false;
    trackerButton.textContent = "Auto Tracking OFF/on"
    statusSpan.innerText = "AUTO Tracking is OFF, manually add your location"

    popup
        .setLatLng(e.latlng)
        .setContent("If you are Happy with this location Click Save My Spot below")
        .openOn(map);
        lat = e.latlng.lat
        lon = e.latlng.lng
        addMarker(lat, lon);
}

map.on('click', onMapClick);



//////////////////////////////////////////////////
// Adding markers to map
// ///////////////////////////////////////////////


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



//////////////////////////////////////////////////
// Auto tracking button
// ///////////////////////////////////////////////



function autoButton() {
  if (autoTracking) {
    autoTracking = false;

    navigator.geolocation.clearWatch(id);
    trackerButton.textContent = "Auto Tracking OFF/on"

    statusSpan.innerText = "AUTO Tracking is OFF, manually add your location"

  }
  else {
    getLocation();
    popup.removeFrom(map)
    autoTracking = true;
    trackerButton.textContent = "Auto Tracking off/ON"
  }
}





//////////////////////////////////////////////////
// delete Button Functions 
// ///////////////////////////////////////////////

setTimeout(()=>{

  let spotting = JSON.parse(localStorage.getItem("spotCounter"));

  if (spotting > 0) {
    deleteButton.style.visibility = 'visible';
  }
},2000);


async function deleteSpots(){



    let answer = prompt("Type: 'YES' to confirm DELETE");

    if (answer.trim().toUpperCase() === 'YES'){

          deleteButton.textContent = "Deleting";

          // Create request to api
          const req = await fetch('/RemoveUserSpots', {
            method: 'POST',
            headers: { 'Content-Type':'application/json' },
            // data
            body: JSON.stringify({
                id: userId,
            }),
        });
        
        const response = await req.json();
        deleteButton.textContent = "Spots Deleted";
      
        setTimeout(() => {
          deleteButton.textContent = "Remove My Spots";   
          deleteButton.style.visibility = 'hidden';
        }, 5000);
      
        localStorage.setItem("spotCounter", JSON.stringify(0));
        spotCounterSpan.innerText = `Your Spots: 0`;
        map.removeLayer(marker_new);

        map.removeLayer(savedMarker);
    }
}





async function keepScreenOn() {

  try {
    wakeLock = await navigator.wakeLock.request("screen");

  } catch (err) {
    // The Wake Lock request has failed - usually system related, such as battery.
    console.log(`${err.name}, ${err.message}`);
  }
}

keepScreenOn();