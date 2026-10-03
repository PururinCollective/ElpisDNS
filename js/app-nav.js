/*
	ΕΛΠΙΣ DNS - the menu button

	On a phone the page links fold behind a button in the top bar. This
	opens and closes them, and gets out of the way when you pick one,
	press Escape, or tap anywhere else.
*/

document.addEventListener("DOMContentLoaded", () => {

	const button = document.getElementById("nav-btn");
	const nav = document.getElementById("nav");

	if(!button || !nav) return;

	const icon = button.querySelector("i");

	function set(open){

		nav.classList.toggle("is-open", open);

		button.setAttribute("aria-expanded", String(open));
		button.setAttribute("aria-label", open ? "Close menu" : "Menu");

		if(icon) icon.className = open ? "bi bi-x-lg" : "bi bi-list";
	}

	button.addEventListener("click", event => {

		event.stopPropagation();

		set(!nav.classList.contains("is-open"));
	});

	nav.addEventListener("click", event => {

		if(event.target.closest("a")) set(false);
	});

	document.addEventListener("click", event => {

		if(!nav.contains(event.target)) set(false);
	});

	document.addEventListener("keydown", event => {

		if(event.key === "Escape" && nav.classList.contains("is-open")){

			set(false);
			button.focus();
		}
	});
});
