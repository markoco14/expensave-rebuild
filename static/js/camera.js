const cameraButton = document.getElementById('cameraButton');

const cancelCaptureButton = document.getElementById('cancelCaptureButton');
const captureButton = document.getElementById('captureButton');

const submitButton = document.getElementById('submitButton');
const retryButton = document.getElementById('retryButton');
const finalCancelButton = document.getElementById('finalCancelButton');

const cameraStatus = document.getElementById('cameraStatus');
const noPhotoDisplay = document.getElementById('noPhotoDisplay');
const cameraImage = document.getElementById('cameraImage');
const captureContainer = document.getElementById('captureContainer');
const guidingRect = document.getElementById('guidingRect');
const videoElement = document.getElementById('cameraVideo');
const cameraInput = document.getElementById('cameraInput');

const capturePhotoButtons = document.getElementById('capturePhotoButtons');
const confirmPhotoButtons = document.getElementById('confirmPhotoButtons');

// Camera status functions
function updateCameraStatus(status) {
  cameraStatus.textContent = status;
}

// Base display functions
function hideBaseDisplay() {
  if (!noPhotoDisplay.classList.contains('hidden')) {
    noPhotoDisplay.classList.add('hidden');
  }
}

function showBaseDisplay() {
  if (!noPhotoDisplay.classList.contains('hidden')) return;
  noPhotoDisplay.classList.remove('hidden');
}

function hideBaseDisplayButtons() {
  if (!cameraButton.classList.contains('hidden')) {
    cameraButton.classList.add('hidden');
  }
}

function showBaseDisplayButtons() {
  if (!cameraButton.classList.contains('hidden')) return;
  cameraButton.classList.remove('hidden');
}

// Video display functions
function hideVideoFeed() {
  if (!videoElement.classList.contains('hidden')) {
    videoElement.classList.add('hidden');
  }
}

function showCaptureContainer() {
  captureContainer.classList.remove('hidden');
  captureContainer.classList.add('stacked');
}

function hideCaptureContainer() {
  if (captureContainer.classList.contains('hidden')) return
  captureContainer.classList.remove('stacked');
  captureContainer.classList.add('hidden');
}

function showGuidingRect() {
  if (guidingRect.classList.contains('hidden')) guidingRect.classList.remove('hidden');
}

function hideGuidingRect() {
  if (!guidingRect.classList.contains('hidden')) {
    guidingRect.classList.add('hidden');
  }
}

function showVideoFeed() {
  if (!videoElement.classList.contains('hidden')) return;
  videoElement.classList.remove('hidden');
}

function hideVideoFeedButtons() {
  if (!capturePhotoButtons.classList.contains('hidden')) {
    capturePhotoButtons.classList.add('hidden');
  }
}

function showVideoFeedButtons() {
  if (!capturePhotoButtons.classList.contains('hidden')) return;
  capturePhotoButtons.classList.remove('hidden');
}

// preview image display functions
function showPreviewImage() {
  if (!cameraImage.classList.contains('hidden')) return;
  cameraImage.classList.remove('hidden');
}

function hidePreviewImage() {
  if (!cameraImage.classList.contains('hidden')) {
    cameraImage.classList.add('hidden');
  }
}

function showPreviewImageButtons() {
  if (!confirmPhotoButtons.classList.contains('hidden')) return;
  confirmPhotoButtons.classList.remove('hidden');
}

function hidePreviewImageButtons() {
  if (!confirmPhotoButtons.classList.contains('hidden')) {
    confirmPhotoButtons.classList.add('hidden');
  }
}

// Activating the camera
async function startVideoStream() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: { ideal: 'environment'}},
      audio: false
    });

    videoElement.srcObject = stream
    videoElement.play();
  } catch (error) {
    console.error("Error starting video stream:", error);
    alert("Unable to access the environment camera: " + error.message);
  } 
}

async function stopVideoStream() {
  if (videoElement.srcObject && videoElement.srcObject.getTracks) {
    videoElement.srcObject.getTracks().forEach(track => track.stop());
  }
  videoElement.srcObject = null;
}

function handleStartCapture(){
  startVideoStream()
  showCaptureContainer();
  showGuidingRect();
  showVideoFeed()
  showVideoFeedButtons()
  hideBaseDisplay()
  hideBaseDisplayButtons()
  updateCameraStatus("Camera active")
}

function handleCancelCapture() {
  stopVideoStream();
  hideCaptureContainer();
  hideGuidingRect();
  showBaseDisplay();
  showBaseDisplayButtons();
  hideVideoFeed();
  hideVideoFeedButtons();
  updateCameraStatus("Camera inactive")
}

// Taking a photo
function captureStillImageAsFile() {
  try {
    const canvas = document.createElement('canvas');
    canvas.width = videoElement.videoWidth;
    canvas.height = videoElement.videoHeight;

    const ctx = canvas.getContext('2d');
    ctx.drawImage(videoElement, 0, 0, canvas.width, canvas.height);

    return new Promise((resolve) => {
      canvas.toBlob((blob) => {
        if (!blob) {
          throw new Error("Unable to capture still image as a blob");
        }
        const fileName =  `img-${Date.now()}.png`;
        const file = new File([blob], fileName, { type: "img/png" });
        resolve(file);
      }, "img/png");
    });
  } catch (error) {
    console.error("Error capturing still image:", error);
    alert("Unable to capture still image: " + error.message);
  }
}

async function handleCaptureImage() {
  try { 
    const imageFile = await captureStillImageAsFile();
  
    // create URL for imageFile
    const imageURL = URL.createObjectURL(imageFile);
    cameraImage.src = imageURL
    
    // Assign the File to the file input element
    const dataTransfer = new DataTransfer();
    dataTransfer.items.add(imageFile);
    cameraInput.files = dataTransfer.files;
    
    stopVideoStream();
    showPreviewImage();
    showPreviewImageButtons();
    hideVideoFeed();
    hideVideoFeedButtons();
    updateCameraStatus("Camera inactive")
  } catch (error) { 
    console.error("Error capturing still image:", error);
    alert("Unable to capture still image: " + error.message);
  }
}

function handleTryAgain() {
  URL.revokeObjectURL(cameraImage.src);
  // clear the input
  cameraInput.files = null;
  cameraInput.value = "";
  
  // clear the image
  cameraImage.src = "";
  startVideoStream();
  showVideoFeed();
  showVideoFeedButtons();
  hidePreviewImage();
  hidePreviewImageButtons();
  updateCameraStatus("Camera active")
}

function handleFinalStageCancelButton() {
  // clear the input
  URL.revokeObjectURL(cameraImage.src);
  cameraInput.files = null;
  cameraInput.value = "";
  
  // clear the image
  cameraImage.src = "";
  hideCaptureContainer();
  hideGuidingRect();
  hidePreviewImage();
  hidePreviewImageButtons();
  showBaseDisplay();
  showBaseDisplayButtons();
  updateCameraStatus("Camera inactive")
}

function cameraUploadSuccess() {
  URL.revokeObjectURL(cameraImage.src);
  cameraInput.value = '';
  cameraInput.files = null;
  // clear the image
  cameraImage.src = "";
  // hide image preview UI
  hidePreviewImage();
  hidePreviewImageButtons();

  // show video feed UI
  showVideoFeed();
  showVideoFeedButtons();
  startVideoStream();
  updateCameraStatus("Camera active")
}

function cameraUploadFailed() {
  alert("Image upload failed. Please try again.")
}

// base stage buttons
cameraButton.addEventListener('click', handleStartCapture);
// capture stage buttons
cancelCaptureButton.addEventListener('click', handleCancelCapture);
captureButton.addEventListener('click', handleCaptureImage);
// submit stage buttons
retryButton.addEventListener('click', handleTryAgain);
finalCancelButton.addEventListener('click', handleFinalStageCancelButton);

document.body.addEventListener('cameraUploadSuccess', cameraUploadSuccess);

document.body.addEventListener('cameraUploadFailed', cameraUploadFailed);