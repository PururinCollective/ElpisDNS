/*
	ΕΛΠΙΣ DNS - footer quotes

	Three sources:
	  "voices" - real people, quoted as they said it
	  "concierge" - house lines written in the cadence of a certain
	                fedora-wearing concierge of crime
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

	/* ---- the concierge ---- */

	{ text: "I'm a criminal. Criminals are notorious liars.", by: "Raymond Reddington" },

	{ text: "Trust is a fragile thing. Once earned, it affords us tremendous freedom.", by: "Raymond Reddington" },

	{ text: "Everyone wants to know where you are going. Very few have earned the right to ask.", by: "The Concierge" },

	{ text: "The man who controls the answers never has to bother censoring the questions.", by: "The Concierge" },

	{ text: "A closed door is only an opinion. I have never been especially moved by opinions.", by: "The Concierge" },

	{ text: "Never let a stranger hold your keys, and never let your ISP hold your curiosity.", by: "The Concierge" },

	{ text: "They do not need your secrets. They only need to know which doors you knock on.", by: "The Concierge" },

	{ text: "Surveillance is rarely announced. It arrives quietly, dressed as convenience.", by: "The Concierge" },

	{ text: "Pick your resolver the way you pick your friends. Carefully, and with an exit in mind.", by: "The Concierge" },

	{ text: "There are two kinds of networks: the ones that answer you, and the ones that answer about you.", by: "The Concierge" },

	{ text: "I have no interest in your browsing history. That is precisely why you can use mine.", by: "The Concierge" },

	{ text: "Freedom is not granted by the people holding the ledger. It is taken back, one query at a time.", by: "The Concierge" },

	/* ---- house lines ---- */

	{ text: "By the community, for the community." },

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
