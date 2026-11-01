document.getElementById("resume-form").addEventListener("submit", function(event) {
    event.preventDefault();
    
    document.getElementById("loading").style.display = "block";
    document.getElementById("results-container").style.display = "none";

    const formData = new FormData(this);

    fetch("/", {
        method: "POST",
        body: formData
    }).then(response => response.json())  // Expecting JSON response
    .then(data => {
        document.getElementById("loading").style.display = "none";
        
        if (data.success) {
            document.getElementById("ats-score").textContent = data.ats_score;
           
            document.getElementById("results-container").style.display = "block";
        } else {
            alert('An error occurred: ' + (data.message || 'Unknown error'));
        }
    }).catch(err => {
        document.getElementById("loading").style.display = "none";
        alert('Error: ' + err.message);
    });
    
    
});
function clearResults() {
    // Hide the results container
    document.getElementById("results-container").style.display = "none";
    
    // Reset the form fields (optional, but helpful if you want to clear the inputs)
    document.getElementById("resume-form").reset();
    
    // Hide the loading message
    document.getElementById("loading").style.display = "none";
}

