const cameraButton = document.getElementById('cameraButton');
const deleteImgButton = document.getElementById('deleteImgButton');
const cameraInput = document.getElementById('cameraInput');
const cameraImage = document.getElementById('cameraImage');
const noPhotoDisplay = document.getElementById('noPhotoDisplay');
const submitButton = document.getElementById('submitButton');

cameraButton.addEventListener('click', () => {
  cameraInput.click();
});

cameraInput.addEventListener('change', () => {
  const file = cameraInput.files[0];
  const url = URL.createObjectURL(file);
  cameraImage.src = url;
  cameraImage.classList.toggle('hidden');
  noPhotoDisplay.classList.toggle('hidden');
  deleteImgButton.classList.toggle('hidden');
  cameraButton.classList.toggle('hidden');
  submitButton.classList.toggle('hidden');
});

deleteImgButton.addEventListener('click', () => {
  URL.revokeObjectURL(cameraImage.src);
  cameraInput.value = '';
  cameraInput.files = null;
  cameraImage.classList.toggle('hidden');
  noPhotoDisplay.classList.toggle('hidden');
  deleteImgButton.classList.toggle('hidden');
  cameraButton.classList.toggle('hidden');
  submitButton.classList.toggle('hidden');
});
