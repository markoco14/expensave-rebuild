const cameraButton = document.getElementById('cameraButton');
const cameraInput = document.getElementById('cameraInput');
const cameraImage = document.getElementById('cameraImage');

cameraButton.addEventListener('click', () => {
  cameraInput.click();
});

cameraInput.addEventListener('change', () => {
  const file = cameraInput.files[0];
  const url = URL.createObjectURL(file);
  cameraImage.src = url;
  cameraImage.classList.toggle('hidden');
});
