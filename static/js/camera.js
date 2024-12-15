const cameraButton = document.getElementById('cameraButton');
const cancelCaptureButton = document.getElementById('cancelCaptureButton');
const captureButton = document.getElementById('captureButton');
const deleteImgButton = document.getElementById('deleteImgButton');
const cameraInput = document.getElementById('cameraInput');
const cameraImage = document.getElementById('cameraImage');
const noPhotoDisplay = document.getElementById('noPhotoDisplay');
const submitButton = document.getElementById('submitButton');
const cameraStatus = document.getElementById('cameraStatus');
const videoElement = document.getElementById('cameraVideo');


// STEP 1: Start the video stream
// we want to reveal the video element
// hide the no photo display element
// we want to hide the camera button
// and show the capture/cancel buttons


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

function toggleBaseViewCaptureView() {
  videoElement.classList.toggle('hidden');
  noPhotoDisplay.classList.toggle('hidden');
  captureButton.classList.toggle('hidden');
  if (cameraStatus.textContent === "") {
    cameraStatus.textContent = "Camera active"
  } else {
    cameraStatus.textContent = ""
  }

  cancelCaptureButton.classList.toggle('hidden');
  cameraButton.classList.toggle('hidden');
}

function handleStartVideoStream(){
  startVideoStream()
  toggleBaseViewCaptureView()
}

cameraButton.addEventListener('click', handleStartVideoStream);
cancelCaptureButton.addEventListener('click', toggleBaseViewCaptureView);

// function cancelTakePhoto() {

// }


// function stopVideoStream() {
//   try {
//       // Access the video element by its ID
//       const videoElement = document.getElementById('cameraVideo');
//       if (!videoElement) {
//           throw new Error(`Element with ID "${videoElementId}" not found`);
//       }
      
//       // Get the video stream from the video element's srcObject
//       const stream = videoElement.srcObject;
//       if (stream && stream.getTracks) {
//         // Stop all tracks in the stream
//         stream.getTracks().forEach(track => track.stop());
//       }
      
//       // Clear the video element's srcObject
//       videoElement.srcObject = null;
//       videoElement.classList.toggle('hidden');
//       noPhotoDisplay.classList.toggle('hidden');
//       captureButton.classList.toggle('hidden');
//       cameraStatus.textContent = ""
//   } catch (error) {
//       console.error("Error stopping video stream:", error);
//       alert("Unable to stop the video stream: " + error.message);
//   }
// }

// function captureStillImage() {
//   try {
//     const videoElement = document.getElementById('cameraVideo');
//     const imgElement = document.getElementById('cameraImage');
//     if (!videoElement || !imgElement) {
//       throw new Error(`Unable to find video or image elements.`);
//     }

//     const canvas = document.createElement('canvas');
//     canvas.width = videoElement.videoWidth;
//     canvas.height = videoElement.videoHeight;

//     const ctx = canvas.getContext('2d');
//     ctx.drawImage(videoElement, 0, 0, canvas.width, canvas.height);

//     const dataUrl = canvas.toDataURL('image/png');

//     imgElement.src = dataUrl;
//     imgElement.classList.toggle('hidden');
//     videoElement.classList.toggle('hidden');
//     cameraStatus.textContent = "Camera inactive"
//     return
//   } catch (error) {
//     console.error("Error capturing still image:", error);
//     alert("Unable to capture still image: " + error.message);
//   }
// }

// cameraButton.addEventListener('click', () => {
//   if (videoElement.srcObject !== null) {
//     stopVideoStream();
//     return;
//   } else {
//     startVideoStream();
//     return;
//   }
// });

// captureButton.addEventListener('click', captureStillImage);
// cancelButton.addEventListener('click', stopVideoStream);

// cameraButton.addEventListener('click', () => {
//   cameraInput.click();
// });

// cameraInput.addEventListener('change', () => {
//   const file = cameraInput.files[0];
//   const url = URL.createObjectURL(file);
//   cameraImage.src = url;
//   cameraImage.classList.toggle('hidden');
//   noPhotoDisplay.classList.toggle('hidden');
//   deleteImgButton.classList.toggle('hidden');
//   cameraButton.classList.toggle('hidden');
//   submitButton.classList.toggle('hidden');
// });

// function cameraUploadSuccess() {
//   URL.revokeObjectURL(cameraImage.src);
//   cameraInput.value = '';
//   cameraInput.files = null;
//   cameraImage.classList.toggle('hidden');
//   noPhotoDisplay.classList.toggle('hidden');
//   deleteImgButton.classList.toggle('hidden');
//   cameraButton.classList.toggle('hidden');
//   submitButton.classList.toggle('hidden');
//   alert("Image saved!")
// }

// function resetCameraForm() {
//   URL.revokeObjectURL(cameraImage.src);
//   cameraInput.value = '';
//   cameraInput.files = null;
//   cameraImage.classList.toggle('hidden');
//   noPhotoDisplay.classList.toggle('hidden');
//   deleteImgButton.classList.toggle('hidden');
//   cameraButton.classList.toggle('hidden');
//   submitButton.classList.toggle('hidden');
// }

// function cameraUploadFailed() {
//   alert("Image upload failed. Please try again.")
// }

// deleteImgButton.addEventListener('click', resetCameraForm);

// document.body.addEventListener('cameraUploadSuccess', cameraUploadSuccess);

// document.body.addEventListener('cameraUploadFailed', cameraUploadFailed);