const fileInput = document.getElementById('resume');
const fileNameDisplay = document.getElementById('file-name');

fileInput.addEventListener('change', function(e) {
    if (e.target.files.length > 0) {
        fileNameDisplay.textContent = "File Uploaded";
    } else {
        fileNameDisplay.textContent = "No file chosen";
    }
});