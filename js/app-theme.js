/*
	ΕΛΠΙΣ DNS - theme control

	Three states: auto (follows the operating system), light, dark.
	The choice lives in localStorage, so the machine remembers.

	The very first paint is handled by the inline snippet in <head>,
	otherwise you get a white flash before this file even downloads.
*/

const THEME_KEY = "elpis-theme";

const THEME_ORDER = ["auto", "light", "dark"];

const THEME_ICON = {
	auto: "bi-circle-half",
	light: "bi-brightness-high",
	dark: "bi-moon-stars"
};

const THEME_LABEL = {
	auto: "Theme: system",
	light: "Theme: light",
	dark: "Theme: dark"
};

const systemDark =
	window.matchMedia("(prefers-color-scheme: dark)");

function storedTheme(){

	try{
		return localStorage.getItem(THEME_KEY) || "auto";
	}
	catch(err){
		return "auto";
	}
}

function resolvedTheme(choice){

	if(choice === "auto"){
		return systemDark.matches ? "dark" : "light";
	}

	return choice;
}

function applyTheme(choice){

	const theme = resolvedTheme(choice);

	document.documentElement.dataset.theme = theme;
	document.documentElement.dataset.themeChoice = choice;

	// Keeps Bootstrap components in step with the page.
	document.documentElement.setAttribute("data-bs-theme", theme);

	const meta = document.querySelector('meta[name="theme-color"]');

	if(meta){
		meta.setAttribute("content", theme === "dark" ? "#1b1e24" : "#ffffff");
	}

	const button = document.getElementById("theme-btn");

	if(button){

		const icon = button.querySelector("i");

		if(icon){
			icon.className = `bi ${THEME_ICON[choice]}`;
		}

		button.setAttribute("aria-label", THEME_LABEL[choice]);
		button.setAttribute("title", `${THEME_LABEL[choice]} - click to change`);
	}
}

function setTheme(choice){

	try{
		localStorage.setItem(THEME_KEY, choice);
	}
	catch(err){
		/* private browsing, nothing to remember */
	}

	applyTheme(choice);
}

function cycleTheme(){

	const next = THEME_ORDER[
		(THEME_ORDER.indexOf(storedTheme()) + 1) % THEME_ORDER.length
	];

	setTheme(next);
}

systemDark.addEventListener("change", () => {

	if(storedTheme() === "auto"){
		applyTheme("auto");
	}
});

document.addEventListener("DOMContentLoaded", () => {

	applyTheme(storedTheme());

	const button = document.getElementById("theme-btn");

	if(button){
		button.onclick = cycleTheme;
	}
});

applyTheme(storedTheme());
