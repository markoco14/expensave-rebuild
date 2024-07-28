gsap.registerPlugin(Flip);
window.listInitialState = Flip.getState("#today-purchases .purchase");
document.body.addEventListener("htmx:beforeSwap", function (event) {
	let listContainer = document.getElementById("today-purchases");
	window.startHeight = listContainer.offsetHeight;
	window.listInitialState = Flip.getState("#today-purchases .purchase");
});

document.body.addEventListener("htmx:afterSwap", function (event) {
	let listContainer = document.getElementById("today-purchases");
	requestAnimationFrame(() => {
		const endHeight = listContainer.scrollHeight + "px";

		// Animate from startHeight to endHeight using GSAP
		gsap.fromTo(
			listContainer,
			{ height: window.startHeight + "px" },
			{
				height: endHeight,
				duration: 0.25, // Adjust duration as needed
				ease: "sine.inOut",
			}
		);

		// Now, animate the list items to their new positions using Flip
		Flip.from(window.listInitialState, {
			duration: 0.25, // Animation duration; adjust as needed for smoothness
			ease: "sine.inOut",
			absolute: true, // Use absolute positioning for the animation
			onComplete: () => (listContainer.style.height = ""), // Cleanup after animation
		});

		// Specifically target the newly added item for a fade-in effect
		const newPurchase = listContainer.querySelector(".new-purchase");
		if (newPurchase) {
			// Reset any styles that might conflict with the fade-in animation
			gsap.set(newPurchase, { opacity: 0, y: -100, x: 0 });

			// Animate the opacity from 0 to 1 for the fade-in effect
			gsap.to(newPurchase, {
				x: 0,
				y: 0,
				opacity: 1,
				duration: 0.5, // Match the duration of the Flip animation for consistency
				ease: "sine.out",
				clearProps: "opacity", // Clear inline opacity style after animation completes
				onComplete: () => {
					// Optionally, remove the 'new-item' class to reset the state
					newPurchase.classList.remove("new-item");
				},
			});
		}
	});
});
