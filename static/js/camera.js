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