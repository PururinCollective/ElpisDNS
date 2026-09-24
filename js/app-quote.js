/*
	ΕΛΠΙΣ DNS - footer quotes

	Two sources:
	  "voices" - real people, quoted as they said it
	  "house" - ΕΛΠΙΣ house lines

	Click the quote to draw another one.
*/

const footerQuotes = [

	/* ---- voices of the open internet ---- */

	{ text: "If you use technology, this fight is yours.", by: "EFF" },

	{ text: "Privacy is not something that I'm merely entitled to, it's an absolute prerequisite.", by: "Marlon Brando" },

	{ text: "Arguing that you don't care about privacy because you have nothing to hide is like saying you don't care about free speech because you have nothing to say.", by: "Edward Snowden" },

	{ text: "The internet interprets censorship as damage and routes around it.", by: "John Gilmore" },

	{ text: "If privacy is outlawed, only outlaws will have privacy.", by: "Phil Zimmermann" },

	{ text: "Privacy is an inherent human right, and a requirement for maintaining the human condition with dignity and respect.", by: "Bruce Schneier" },

	{ text: "Information is power. But like all power, there are those who want to keep it for themselves.", by: "Aaron Swartz" },

	{ text: "The universe believes in encryption.", by: "Julian Assange" },

	{ text: "We reject: kings, presidents and voting. We believe in: rough consensus and running code.", by: "David Clark, IETF" },

	{ text: "This is for everyone.", by: "Tim Berners-Lee" },

	/* ---- house lines ---- */

	{ text: "A network built upon strong foundations shall not falter." },

	{ text: "Defend privacy. Preserve freedom. Protect the open internet." },

	{ text: "Blessed are the peacemakers of the network." },

	{ text: "A heavenly guardian against corrupted routes and digital darkness." },

	{ text: "Truth travels faster upon open networks." },

	{ text: "The gates shall remain open to all who seek knowledge." },

	{ text: "Privacy is sacred. Freedom is foundational." },

	{ text: "Encryption is not a weapon. It is a closed curtain." },

	{ text: "Every blocked domain is somebody's opinion enforced with a hammer." },

	{ text: "Resolve freely. Answer to no one." },

	{ text: "ΕΛΠΙΣ - hope, and the last thing left in the box." }
];

function renderQuote(){

	const node = document.getElementById("footer-quote");

	if(!node) return;

	const quote = footerQuotes[
		Math.floor(Math.random() * footerQuotes.length)
	];

	const attribution = quote.by
		? `<span class="quote-by">&mdash; ${quote.by}</span>`
		: "";

	node.innerHTML =
		`<span class="quote-text">&ldquo;${quote.text}&rdquo;</span>${attribution}`;
}

document.addEventListener("DOMContentLoaded", () => {

	const node = document.getElementById("footer-quote");

	if(!node) return;

	renderQuote();

	node.title = "Another one";

	node.onclick = () => {

		node.style.opacity = "0";

		setTimeout(() => {

			renderQuote();

			node.style.opacity = "";

		}, 220);
	};
});
