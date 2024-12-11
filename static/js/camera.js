`
Contains all camera related functions
`

const devicesButton = document.getElementById("devicesButton");
window.addEventListener("load", listAvailableDevices);

if ('mediaDevices' in navigator && 'getUserMedia' in navigator.mediaDevices) {
    navigator.mediaDevices.getUserMedia({video: {facingMode: "environment"}})
}

async function listAvailableDevices() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.enumerateDevices) {
        console.log("enumerateDevices() not supported.");
        return;
    } 
    const devices = await navigator.mediaDevices.enumerateDevices();
    if (!devices) {
        devicesList.innerHTML = "Unable to load device list. Try restarting the page.";
        return
    }
    setTimeout(() => {
        devicesList.innerHTML = "";
        devices.forEach(device => {
            const deviceItem = `<li>Device: ${device.kind}</li>`;
            devicesList.innerHTML += deviceItem;
        });
    }, 1000)
}

const video = document.querySelector('video');
const canvas = document.querySelector('canvas');
const screenshotImage = document.querySelector('img');
const buttons = [...document.querySelectorAll('.js-controls')];
let streamStarted = false;

// isolate buttons
const [play, pause, screenshot] = buttons;

const constraints = {
    video: {
      width: {
        min: 1280,
        ideal: 1920,
        max: 2560,
      },
      height: {
        min: 720,
        ideal: 1080,
        max: 1440
      },
    }
  };
