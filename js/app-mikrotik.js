/*
	ΕΛΠΙΣ DNS - MikroTik script generator

	Resolves the chosen endpoint through a public resolver, then writes a
	RouterOS .rsc that pins those addresses and switches DoH on. The static
	entry matters: without it the router cannot look up the name of the
	resolver it is about to start using.
*/

async function resolveDomain(domain, type){

	try{

		const response = await fetch(
			`https://dns.google/resolve?name=${encodeURIComponent(domain)}&type=${type}`
		);

		const data = await response.json();

		if(!data.Answer) return [];

		return data.Answer
			.filter(x => x.type === type)
			.map(x => x.data);

	} catch(err){

		console.error(err);

		return [];
	}
}

async function generateMikrotikRSC(event){

	const button = event ? event.currentTarget : null;
	const original = button ? button.innerHTML : "";

	if(button){
		button.innerHTML = '<i class="bi bi-hourglass-split"></i> Resolving';
		button.disabled = true;
	}

	const endpoint =
		document.getElementById("endpoint").innerText.trim();

	let domain;

	try{
		domain = new URL(endpoint).hostname;
	}
	catch(err){

		alert("That endpoint is not a DoH URL, so there is nothing to script.");

		if(button){
			button.innerHTML = original;
			button.disabled = false;
		}

		return;
	}

	const entry = window.ElpisDNS ? window.ElpisDNS.entry : null;

	// An IP address endpoint has no name for the router to look up.
	const literal = /^\d{1,3}(\.\d{1,3}){3}$/.test(domain);

	const [ipv4, ipv6] = literal ? [[], []] : await Promise.all([
		resolveDomain(domain, 1),
		resolveDomain(domain, 28)
	]);

	let rsc =
		`# ΕΛΠΙΣ DNS - RouterOS configuration for ${domain}\n` +
		`# Generated ${new Date().toLocaleString()} at https://elpis.violetnetworks.xyz/\n` +
		(entry
			? `# Profile: ${entry.provider} / ${entry.region} / ${entry.filter} / ${entry.feature}\n`
			: "") +
		`#\n` +
		`# This overwrites the current DoH setting on the router.\n` +
		`# Import a certificate store first, or verify-doh-cert will fail:\n` +
		`#   /tool fetch url="https://curl.se/ca/cacert.pem"\n` +
		`#   /certificate import file-name=cacert.pem passphrase=""\n\n` +
		(literal ? "" : `/ip dns static remove [ find name="${domain}" ]\n\n`);

	if(!literal && !ipv4.length && !ipv6.length){

		rsc +=
			`# WARNING: no addresses came back for ${domain}.\n` +
			`# Add the static entry by hand before relying on this script.\n\n`;
	}

	ipv4.forEach(ip => {
		rsc += `/ip dns static add name="${domain}" type=A address="${ip}"\n`;
	});

	ipv6.forEach(ip => {
		rsc += `/ip dns static add name="${domain}" type=AAAA address="${ip}"\n`;
	});

	rsc +=
		`\n/ip dns set use-doh-server="${endpoint}" ` +
		`allow-remote-requests=yes verify-doh-cert=yes\n`;

	const blob = new Blob([rsc], { type: "text/plain" });

	const link = document.createElement("a");

	link.href = URL.createObjectURL(blob);
	link.download = `elpis-${domain}.rsc`;

	document.body.appendChild(link);
	link.click();
	document.body.removeChild(link);

	URL.revokeObjectURL(link.href);

	if(button){
		button.innerHTML = original;
		button.disabled = false;
	}
}

const rscButton = document.getElementById("download-rsc-btn");

if(rscButton){
	rscButton.onclick = generateMikrotikRSC;
}
