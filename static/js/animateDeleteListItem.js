document.addEventListener('htmx:afterSwap', function (event) {
    // Check if this was a delete request
    if (event.detail.elt && event.detail.elt.getAttribute('hx-delete')) {
        const item = event.detail.elt.closest('li');
        const height = item.offsetHeight;
        const siblings = Array.from(item.parentNode.children);

        // Remove the item from the DOM
        item.parentNode.removeChild(item);

        // Slide up the remaining items
        siblings.forEach(sibling => {
            if (sibling !== item) {
                gsap.fromTo(sibling, 
                    { y: height + parseInt(window.getComputedStyle(sibling).marginBottom) }, 
                    { y: 0, duration: 0.5, clearProps: "transform" }
                );
            }
        });
    }
});
