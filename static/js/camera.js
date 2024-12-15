const cameraButton = document.getElementById('cameraButton');

const cancelCaptureButton = document.getElementById('cancelCaptureButton');
const captureButton = document.getElementById('captureButton');

const submitButton = document.getElementById('submitButton');
const retryButton = document.getElementById('retryButton');
const finalCancelButton = document.getElementById('finalCancelButton');

const cameraStatus = document.getElementById('cameraStatus');
const noPhotoDisplay = document.getElementById('noPhotoDisplay');
const cameraImage = document.getElementById('cameraImage');
const videoElement = document.getElementById('cameraVideo');
const cameraInput = document.getElementById('cameraInput');


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

// STEP 2 Take a photo
// have the option to approve
// try again (back to video view)
// or cancel completely (back to base view)

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
    
    toggleCaptureViewSubmitView()
  } catch (error) { 
    console.error("Error capturing still image:", error);
    alert("Unable to capture still image: " + error.message);
  }
}

function toggleCaptureViewSubmitView() {
  alert('changing view')
  videoElement.classList.toggle('hidden');
  cameraImage.classList.toggle('hidden');
  captureButton.classList.toggle('hidden');
  cancelCaptureButton.classList.toggle('hidden');
  submitButton.classList.toggle('hidden');
  retryButton.classList.toggle('hidden');
  finalCancelButton.classList.toggle('hidden');
}
captureButton.addEventListener('click', handleCaptureImage);



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