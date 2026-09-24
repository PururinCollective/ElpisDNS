/*
	ΕΛΠΙΣ DNS - setup page helpers

	1. Drops the endpoint the visitor picked on the front page into
	   every example, so nobody has to copy hostnames by hand.
	2. Gives every code block a copy button.
*/

const FALLBACK_ENDPOINT = "https://b.hitoha.moe/dns-query";
const FALLBACK_HOST = "b.hitoha.moe";
const FALLBACK_STAMP =
	"sdns://AgMAAAAAAAAAAAAMYi5oaXRvaGEubW9lCi9kbnMtcXVlcnk";

function picked(key, fallback){

	try{
		return localStorage.getItem(key) || fallback;
	}
	catch(err){
		return fallback;
	}
}

function fillPicked(){

	const endpoint = picked("elpis-endpoint", FALLBACK_ENDPOINT);
	const host = picked("elpis-host", FALLBACK_HOST);

	const tls = endpoint.startsWith("tls://")
		? endpoint
		: `tls://${host}`;

	const https = endpoint.startsWith("https://")
		? endpoint
		: `https://${host}/dns-query`;

	const values = {
		endpoint,
		host,
		tls,
		https,
		stamp: picked("elpis-stamp", FALLBACK_STAMP)
	};

	document.querySelectorAll("[data-picked]").forEach(node => {

		const key = node.dataset.picked;

		if(values[key]){
			node.textContent = values[key];
		}
	});
}

function addCopyButtons(){

	document.querySelectorAll(".code-block").forEach(block => {

		const pre = block.querySelector("pre");

		// Blocks built by app-resolvers.js bring their own button.
		if(!pre || block.querySelector(".copy-code")) return;

		const button = document.createElement("button");

		button.type = "button";
		button.className = "copy-code";
		button.innerHTML = '<i class="bi bi-clipboard"></i> Copy';

		button.onclick = async () => {

			try{

				await navigator.clipboard.writeText(pre.innerText);

				button.innerHTML = '<i class="bi bi-check2"></i> Copied';
			}
			catch(err){

				button.innerHTML = '<i class="bi bi-x-lg"></i> Blocked';
			}

			setTimeout(() => {
				button.innerHTML = '<i class="bi bi-clipboard"></i> Copy';
			}, 1400);
		};

		block.appendChild(button);
	});
}

document.addEventListener("DOMContentLoaded", () => {

	fillPicked();

	addCopyButtons();
});
