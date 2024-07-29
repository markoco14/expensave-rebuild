	document.addEventListener('htmx:beforeRequest', (event) => {
		const target = event.target;
		if (target.matches('button')) {
			const container = target.closest('.detail-card');
			container.classList.add('animate-pulse');
		}

		if (target.matches('form')) {
			const container = target.closest('.detail-card');
			if (container) {
				container.classList.add('animate-pulse');
			}
		}
	});

	document.addEventListener('htmx:afterRequest', (event) => {
		const target = event.target;
		if (target.matches('.detail-card')) {
			target.classList.remove('animate-pulse');
		}
		if (target.matches('button')) {
			target.closest('.detail-card').classList.remove('animate-pulse');
		}
		if (target.matches('form')) {
			target.closest('.detail-card').classList.remove('animate-pulse');
		}
	});

	document.addEventListener('htmx:beforeSwap', (event) => {
		const target = event.target;
		if (target.matches('.detail-card')) {
			const height = target.offsetHeight;
			target.style.height = height + 'px';
		}
	});

	document.addEventListener('htmx:afterSwap', (event) => {
		const target = event.target;
		if (target.matches('.detail-card')) {
			gsap.fromTo(target,
				{ height: target.offsetHeight + 'px' },
				{ height: 'auto', duration: 0.4, ease: 'power2.inOut' }
			);
		}
	});

