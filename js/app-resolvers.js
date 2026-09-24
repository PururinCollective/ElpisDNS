/*
	ΕΛΠΙΣ DNS - resolver addresses

	The public ΕΛΠΙΣ Resolver instances all come out of resolvers.json:
	the table on the resolver page, and the ready-made upstream lists for
	AdGuard Home and Pi-hole on the resolver and setup pages. Add a server
	to the JSON and every page follows.

	Mount points, any of which a page may leave out:

		[data-resolver-table]    the server table
		[data-resolver-notice]   the notice line from the JSON
		[data-resolver-updated]  when the JSON was last touched
		[data-upstream-builder]  app and network pickers, and the lists

	copy() comes from app-copy.js, loaded ahead of this file.
*/

const RESOLVER_ROLES = {
	active: { label: "Active", pill: "pill-ok" },
	backup: { label: "Backup", pill: "pill-warn" }
};

// How each app wants an IPv4 address that is not on port 53. IPv6 is
// always served directly on 53, so it is written bare everywhere.
const UPSTREAM_APPS = [
	{
		key: "adguard",
		label: "AdGuard Home",
		v4: (host, port) => `${host}:${port}`,
		main: "Paste into <b>Settings → DNS settings → Upstream DNS servers</b>.",
		backup: "Optional: paste into <b>Fallback DNS servers</b>, used only if the ones above stop answering."
	},
	{
		key: "pihole",
		label: "Pi-hole",
		v4: (host, port) => `${host}#${port}`,
		main: "Paste into <b>Settings → DNS → Custom DNS servers</b>, one per line, and untick the built-in providers.",
		backup: "Optional: add these below the others as extra cover."
	},
	{
		key: "other",
		label: "Other",
		v4: (host, port) => `${host}:${port}`,
		main: "For Technitium, Blocky, Unbound, a router, or anything else that takes an upstream with a port.",
		backup: "Standby backups, if you want extra cover."
	}
];

// IPv6 first and the default: it reaches the resolver directly, with no
// NAT in between.
const UPSTREAM_FAMILIES = [
	{ key: "v6",   label: "IPv6" },
	{ key: "v4",   label: "IPv4" },
	{ key: "both", label: "IPv6 + IPv4" }
];

const UPSTREAM_KEY = "elpis-upstream";

let resolverData = null;

/* ---------- helpers ---------- */

function resolverEscape(value){

	return String(value).replace(/[&<>"']/g, ch => ({
		"&": "&amp;",
		"<": "&lt;",
		">": "&gt;",
		'"': "&quot;",
		"'": "&#39;"
	}[ch]));
}

function splitIPv4(value){

	const [host, port] = String(value).split(":");

	return { host, port: Number(port) || 53 };
}

function eachMount(selector, render){

	document.querySelectorAll(selector).forEach(node => render(node));
}

/* ---------- table ---------- */

function addressButtons(list){

	if(!list.length){
		return '<span class="none">&mdash;</span>';
	}

	return `<div class="addr-list">${list.map(addr => `
		<button class="addr" type="button" data-addr="${resolverEscape(addr)}" title="Copy ${resolverEscape(addr)}">
			${resolverEscape(addr)} <i class="bi bi-clipboard"></i>
		</button>`).join("")}
	</div>`;
}

function renderResolverTable(node){

	const engines = resolverData.engines || {};

	const rows = resolverData.servers.map(server => {

		const engine = engines[server.engine] || { label: server.engine };
		const role = RESOLVER_ROLES[server.role] || RESOLVER_ROLES.active;

		const engineCell = engine.url
			? `<a href="${resolverEscape(engine.url)}" target="_blank" rel="noopener">${resolverEscape(engine.label)}</a>`
			: resolverEscape(engine.label);

		const mldsa = server.mldsa44
			? '<span class="yes"><i class="bi bi-check-lg"></i> Yes</span>'
			: '<span class="no">No</span>';

		return `
			<tr class="${server.role === "backup" ? "is-backup" : ""}">
				<td class="server-name" data-label="Server">${resolverEscape(server.name)}</td>
				<td data-label="IPv4 (NAT)">${addressButtons(server.ipv4 ? [server.ipv4] : [])}</td>
				<td data-label="IPv6 (direct)">${addressButtons(server.ipv6 || [])}</td>
				<td data-label="Software">${engineCell}</td>
				<td data-label="ML-DSA-44">${mldsa}</td>
				<td data-label="Status"><span class="pill ${role.pill}">${role.label}</span></td>
			</tr>`;
	}).join("");

	node.innerHTML = `
		<table class="servers">
			<thead>
				<tr>
					<th scope="col">Server</th>
					<th scope="col">IPv4 (NAT)</th>
					<th scope="col">IPv6 (direct)</th>
					<th scope="col">Software</th>
					<th scope="col">ML-DSA-44</th>
					<th scope="col">Status</th>
				</tr>
			</thead>
			<tbody>${rows}</tbody>
		</table>`;

	node.onclick = event => {

		const button = event.target.closest(".addr");

		if(button){
			copy(button.dataset.addr, button, "Copied");
		}
	};
}

function renderResolverNotice(node){

	if(!resolverData.notice){

		node.hidden = true;

		return;
	}

	const text = node.querySelector("[data-notice-text]") || node;

	text.textContent = resolverData.notice;

	node.hidden = false;
}

function renderResolverUpdated(node){

	if(!resolverData.updated) return;

	const date = new Date(`${resolverData.updated}T00:00:00Z`);

	node.textContent = isNaN(date)
		? resolverData.updated
		: date.toLocaleDateString("en-GB", {
			day: "numeric",
			month: "long",
			year: "numeric",
			timeZone: "UTC"
		});
}

/* ---------- upstream builder ---------- */

function upstreamChoice(){

	const fallback = { app: "adguard", family: "v6" };

	try{

		const saved = JSON.parse(localStorage.getItem(UPSTREAM_KEY) || "null");

		return {
			app: UPSTREAM_APPS.some(a => a.key === saved?.app) ? saved.app : fallback.app,
			family: UPSTREAM_FAMILIES.some(f => f.key === saved?.family) ? saved.family : fallback.family
		};
	}
	catch(err){
		return fallback;
	}
}

function rememberUpstream(choice){

	try{
		localStorage.setItem(UPSTREAM_KEY, JSON.stringify(choice));
	}
	catch(err){
		/* private browsing, nothing to remember */
	}
}

// IPv6 first: it goes straight out without a NAT in the way.
function upstreamLines(servers, app, family){

	const v6 = family === "v4"
		? []
		: servers.flatMap(server => server.ipv6 || []);

	const v4 = family === "v6"
		? []
		: servers
			.filter(server => server.ipv4)
			.map(server => {

				const { host, port } = splitIPv4(server.ipv4);

				return port === 53 ? host : app.v4(host, port);
			});

	return [...v6, ...v4];
}

function segmentButtons(options, selected, group){

	return options.map(option => `
		<button type="button" class="option-btn${option.key === selected ? " active" : ""}"
			data-group="${group}" data-value="${option.key}"
			aria-pressed="${option.key === selected}">${option.label}</button>`).join("");
}

function codeBlock(lines){

	const text = lines.length
		? lines.join("\n")
		: "# nothing on this network - try another option above";

	return `
		<div class="code-block">
			<pre>${resolverEscape(text)}</pre>
			<button type="button" class="copy-code"><i class="bi bi-clipboard"></i> Copy</button>
		</div>`;
}

function renderUpstreamBuilder(node, choice){

	const app = UPSTREAM_APPS.find(a => a.key === choice.app);

	const active = resolverData.servers.filter(s => s.role !== "backup");
	const backup = resolverData.servers.filter(s => s.role === "backup");

	// Both families list every server twice. Load-balancing asks one
	// upstream per query, so that is only failover; Parallel requests asks
	// them all, so each resolver would get every question twice.
	const twiceNote = choice.family === "both" && app.key === "adguard"
		? `<div class="note"><i class="bi bi-info-circle"></i><div>
			This list names each server twice, once per address. Use
			<b>Load-balancing</b>, not <b>Parallel requests</b>, or every server
			gets each question twice.</div></div>`
		: "";

	const backupPart = backup.length
		? `<p class="builder-caption">${app.backup}</p>${codeBlock(upstreamLines(backup, app, choice.family))}`
		: "";

	node.innerHTML = `
		<div class="builder">
			<div class="builder-controls">
				<div class="builder-group">
					<span class="builder-label" id="upstream-app-label">You use</span>
					<div class="seg" role="group" aria-labelledby="upstream-app-label">
						${segmentButtons(UPSTREAM_APPS, choice.app, "app")}
					</div>
				</div>
				<div class="builder-group">
					<span class="builder-label" id="upstream-family-label">Connect over</span>
					<div class="seg" role="group" aria-labelledby="upstream-family-label">
						${segmentButtons(UPSTREAM_FAMILIES, choice.family, "family")}
					</div>
				</div>
			</div>
			<p class="builder-caption">${app.main}</p>
			${codeBlock(upstreamLines(active, app, choice.family))}
			${twiceNote}
			${backupPart}
		</div>`;

	node.onclick = event => {

		const option = event.target.closest(".option-btn");

		if(option){

			const next = { ...choice, [option.dataset.group]: option.dataset.value };

			rememberUpstream(next);

			// Every builder on the page follows, so two never disagree.
			eachMount("[data-upstream-builder]", other => renderUpstreamBuilder(other, next));

			return;
		}

		const button = event.target.closest(".copy-code");

		if(button){
			copy(button.parentElement.querySelector("pre").innerText, button, "Copied");
		}
	};
}

/* ---------- loading ---------- */

async function loadResolvers(){

	try{

		const response = await fetch("resolvers.json?hash=799fe164", { cache: "no-cache" });

		if(!response.ok){
			throw new Error(`resolvers.json responded ${response.status}`);
		}

		resolverData = await response.json();

		resolverData.servers = (resolverData.servers || []).filter(server =>
			server && server.name && (server.ipv4 || (server.ipv6 && server.ipv6.length))
		);

	} catch(err){

		console.error("Unable to load resolvers.json", err);

		eachMount("[data-resolver-table], [data-upstream-builder]", node => {
			node.innerHTML =
				'<div class="note note-warn"><i class="bi bi-exclamation-triangle"></i>' +
				'<div>The address list could not be loaded. ' +
				'<a href="resolvers.json?hash=799fe164">Open resolvers.json</a> to see it directly.</div></div>';
		});

		return;
	}

	const choice = upstreamChoice();

	eachMount("[data-resolver-table]", renderResolverTable);
	eachMount("[data-resolver-notice]", renderResolverNotice);
	eachMount("[data-resolver-updated]", renderResolverUpdated);
	eachMount("[data-upstream-builder]", node => renderUpstreamBuilder(node, choice));
}

loadResolvers();
