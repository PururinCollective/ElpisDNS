/*
	ΕΛΠΙΣ DNS - the road to 2.5.0

	On the resolver page, the rail down the release timeline fills with
	the flame as you scroll past it, and each release comes up as it
	reaches the screen.

	Without this file, or for visitors who ask for reduced motion, the
	rail is full and every release is simply there.
*/

document.addEventListener("DOMContentLoaded", () => {

	const timeline = document.getElementById("timeline");

	if(!timeline) return;

	if(window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

	if(!("IntersectionObserver" in window)) return;

	timeline.classList.add("journey-live");

	const seen = new IntersectionObserver(entries => {

		entries.forEach(entry => {

			if(!entry.isIntersecting) return;

			entry.target.classList.add("is-in");
			seen.unobserve(entry.target);
		});

	}, { rootMargin: "0px 0px -10% 0px" });

	timeline.querySelectorAll(".tl").forEach(item => seen.observe(item));

	// The flame reaches whatever sits 60% of the way down the screen.
	let queued = false;

	function fill(){

		queued = false;

		const box = timeline.getBoundingClientRect();
		const reach = window.innerHeight * 0.6 - box.top;
		const share = Math.min(1, Math.max(0, reach / box.height));

		timeline.style.setProperty("--fill", share.toFixed(4));
	}

	function queue(){

		if(queued) return;

		queued = true;
		requestAnimationFrame(fill);
	}

	window.addEventListener("scroll", queue, { passive: true });
	window.addEventListener("resize", queue);

	fill();
});
