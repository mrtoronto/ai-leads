document.addEventListener('DOMContentLoaded', function () {

	const dynamicText = $('.hero-dynamic-text')[0];
	const textArray = [
			"Lightweight",
			"Low Cost",
			"Usage-based",
			"On-Demand",
			"AI-Augmented",
	];
	let currentIndex = 0;

	function changeText() {
		// First, add the fade-out animation class
		dynamicText.classList.add("hero-fade-out");

		// After the fade-out animation ends, change the text and add the fade-in animation
		setTimeout(() => {
			dynamicText.innerHTML = textArray[currentIndex];
			dynamicText.classList.remove("hero-fade-out");
			dynamicText.classList.add("hero-fade-in");

			// Remove the fade-in class after animation completes to reset
			setTimeout(() => {
				dynamicText.classList.remove("hero-fade-in");
			}, 500); // Match with the duration of fade-in animation

			// Update the index to the next value
			currentIndex = (currentIndex + 1) % textArray.length;
		}, 500); // Match with the duration of fade-out animation
	}

	// Set an interval to change the text every 3 seconds (3000 milliseconds)
	setInterval(changeText, 3000);

});
