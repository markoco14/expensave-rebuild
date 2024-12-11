const cameraButton = document.getElementById('cameraButton');
const deleteImgButton = document.getElementById('deleteImgButton');
const cameraInput = document.getElementById('cameraInput');
const cameraImage = document.getElementById('cameraImage');
const noPhotoDisplay = document.getElementById('noPhotoDisplay');

cameraButton.addEventListener('click', () => {
  cameraInput.click();
});

cameraInput.addEventListener('change', () => {
  const file = cameraInput.files[0];
  const url = URL.createObjectURL(file);
  cameraImage.src = url;
  cameraImage.classList.toggle('hidden');
  cameraImage.scrollIntoView();
  deleteImgButton.classList.toggle('hidden');
  cameraButton.classList.toggle('hidden');
});

deleteImgButton.addEventListener('click', () => {
  URL.revokeObjectURL(cameraImage.src);
  cameraImage.classList.toggle('hidden');
  noPhotoDisplay.scrollIntoView();
  deleteImgButton.classList.toggle('hidden');
  cameraButton.classList.toggle('hidden');
});