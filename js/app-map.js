/*
	ΕΛΠΙΣ DNS - network map

	The land is img/sea-map.svg, pulled in with <use> and coloured by the
	stylesheet. This file draws everything on top of it: the AS sites that
	answer, the cities that ask, and dotted traffic running between them.

	Projection numbers come from data-proj on the <svg>, which is what
	tools/make-graphics.py printed when it drew the land. Keep the two in
	step or the markers drift off their cities.

	Want your city on the map? Add a line to MAP_CITIES. A new AS site goes
	in MAP_SITES, with a callout spot that does not sit on land.
*/

const MAP_SITES = [
	{
		place: "Kuala Lumpur, MY",
		lon: 101.6865, lat: 3.1412,
		networks: [
			["AS153334", "Origin TechLab"],
			["AS204535", "kevin.moe"]
		]
	},
	{
		place: "Semenyih, MY",
		lon: 101.843, lat: 2.9516,
		networks: [
			["AS154516", "Perfect Network"]
		]
	},
	{
		place: "Singapore",
		lon: 103.8516, lat: 1.2904,
		networks: [
			["AS135134", "Shana Network"]
		]
	}
];

// Where the label boxes sit, in map pixels, and which sites they explain.
// Both spots are open sea at every width the labels are shown.
const MAP_CALLOUTS = [
	{ x: 16, y: 484, sites: [0, 1], width: 196 },
	{ x: 378, y: 288, sites: [2], width: 176 }
];

// [name, longitude, latitude, label side]. No side means no label: the
// dot and its traffic are enough, and forty labels would be a mess.
const MAP_CITIES = [
	["Pekanbaru", 101.4478, 0.5071, "left"],
	["Depok", 106.7942, -6.4025, "right"],
	["Medan", 98.6722, 3.5952, "left"],
	["Banda Aceh", 95.3238, 5.5483],
	["Padang", 100.4172, -0.9471],
	["Palembang", 104.7754, -2.9761, "right"],
	["Batam", 104.0305, 1.0456],
	["Bandung", 107.6191, -6.9175],
	["Semarang", 110.4167, -6.9667],
	["Yogyakarta", 110.3695, -7.7956],
	["Surabaya", 112.7521, -7.2575, "right"],
	["Denpasar", 115.2126, -8.6705, "right"],
	["Pontianak", 109.3425, -0.0263, "right"],
	["Balikpapan", 116.8529, -1.2379],
	["Makassar", 119.4327, -5.1477, "right"],
	["Manado", 124.8421, 1.4748],
	["Dili", 125.5603, -8.5569],
	["Penang", 100.3288, 5.4141, "left"],
	["Ipoh", 101.0901, 4.5975],
	["Kota Bharu", 102.2381, 6.1254],
	["Kuantan", 103.326, 3.8077],
	["Kuching", 110.3593, 1.5535, "right"],
	["Kota Kinabalu", 116.0735, 5.9804, "right"],
	["Bandar Seri Begawan", 114.9398, 4.9031],
	["Hat Yai", 100.4747, 7.0086],
	["Phuket", 98.3923, 7.8804],
	["Bangkok", 100.5018, 13.7563, "right"],
	["Ho Chi Minh City", 106.6297, 10.8231, "right"],
	["Phnom Penh", 104.9282, 11.5564, "left"],
	["Da Nang", 108.2022, 16.0544],
	["Hanoi", 105.8342, 21.0278, "right"],
	["Vientiane", 102.6331, 17.9757],
	["Yangon", 96.1735, 16.8409, "right"],
	["Manila", 120.9842, 14.5995, "right"],
	["Cebu", 123.8854, 10.3157],
	["Davao", 125.4553, 7.1907]
];

// What a phone shows: the middle of the region, close enough to read.
const MAP_PHONE = { lon0: 94, lon1: 123, top: 15, bottom: -9.5 };

const MAP_NS = "http://www.w3.org/2000/svg";

function mapEl(name, attrs, text){

	const node = document.createElementNS(MAP_NS, name);

	Object.entries(attrs || {}).forEach(([key, value]) => {
		node.setAttribute(key, value);
	});

	if(text) node.textContent = text;

	return node;
}

function mercator(lat){

	const phi = Math.max(-85, Math.min(85, lat)) * Math.PI / 180;

	return Math.log(Math.tan(Math.PI / 4 + phi / 2)) * 180 / Math.PI;
}

function drawMap(svg){

	const [lon0, lon1, top] = svg.dataset.proj.split(" ").map(Number);
	const width = svg.viewBox.baseVal.width;
	const scale = width / (lon1 - lon0);

	const project = (lon, lat) => [
		(lon - lon0) * scale,
		(mercator(top) - mercator(lat)) * scale
	];

	const traffic = svg.querySelector("#map-traffic");
	const cities = svg.querySelector("#map-cities");
	const hubs = svg.querySelector("#map-hubs");
	const callouts = svg.querySelector("#map-callouts");

	const sites = MAP_SITES.map(site => ({
		...site,
		at: project(site.lon, site.lat)
	}));

	// A gentle arc rather than a ruler line, always bowing upwards, so
	// the traffic reads like routes on a flight map.
	function arc([x1, y1], [x2, y2]){

		const dx = x2 - x1;
		const dy = y2 - y1;
		const len = Math.hypot(dx, dy) || 1;

		let nx = -dy / len;
		let ny = dx / len;

		if(ny > 0){
			nx = -nx;
			ny = -ny;
		}

		const bend = len * .18;
		const cx = (x1 + x2) / 2 + nx * bend;
		const cy = (y1 + y2) / 2 + ny * bend;

		return `M${x1.toFixed(1)} ${y1.toFixed(1)} Q${cx.toFixed(1)} ${cy.toFixed(1)} ${x2.toFixed(1)} ${y2.toFixed(1)}`;
	}

	// Every city talks to its nearest site; every other one also talks
	// to a second, the way a client with two upstreams does.
	MAP_CITIES.forEach(([name, lon, lat, side], i) => {

		const at = project(lon, lat);

		const ranked = sites
			.map((site, s) => ({ s, d: Math.hypot(site.at[0] - at[0], site.at[1] - at[1]) }))
			.sort((a, b) => a.d - b.d);

		const targets = [ranked[0].s];

		// The two Malaysian sites are a few pixels apart, so "second
		// nearest" for a Malaysian city would be its own neighbour.
		const other = ranked.find(r =>
			Math.hypot(sites[r.s].at[0] - sites[ranked[0].s].at[0],
				sites[r.s].at[1] - sites[ranked[0].s].at[1]) > 20);

		if(i % 2 === 0 && other) targets.push(other.s);

		targets.forEach((s, n) => {

			traffic.append(mapEl("path", {
				class: "traffic",
				d: arc(at, sites[s].at),
				style: `--dur:${(2.6 + ((i * 7 + n * 3) % 10) / 10).toFixed(1)}s;` +
					`--delay:-${((i * 13 + n * 5) % 30) / 10}s`
			}));
		});

		cities.append(mapEl("circle", {
			class: "city",
			cx: at[0].toFixed(1),
			cy: at[1].toFixed(1),
			r: 3.2
		}));

		if(side){

			const left = side === "left";

			cities.append(mapEl("text", {
				class: "city-label",
				x: (at[0] + (left ? -8 : 8)).toFixed(1),
				y: (at[1] + 4).toFixed(1),
				"text-anchor": left ? "end" : "start"
			}, name));
		}
	});

	sites.forEach(site => {

		const [x, y] = site.at;

		hubs.append(
			mapEl("circle", { class: "hub-ring", cx: x, cy: y, r: 7 }),
			mapEl("circle", { class: "hub-ring late", cx: x, cy: y, r: 7 }),
			mapEl("circle", { class: "hub-core", cx: x, cy: y, r: 6 })
		);
	});

	MAP_CALLOUTS.forEach(callout => {

		const rows = callout.sites.flatMap(s =>
			MAP_SITES[s].networks.map(([asn, name]) => ({ asn, name, place: MAP_SITES[s].place, s }))
		);

		const height = 18 + rows.length * 44;
		const group = mapEl("g", { class: "callout" });

		// Leader lines from the box edge nearest the site.
		callout.sites.forEach(s => {

			const [x, y] = sites[s].at;

			const ex = x < callout.x ? callout.x : callout.x + callout.width;
			const ey = Math.max(callout.y + 14, Math.min(callout.y + height - 14, y));

			group.append(mapEl("path", {
				class: "callout-line",
				d: `M${ex} ${ey} L${x} ${y}`
			}));
		});

		group.append(mapEl("rect", {
			class: "callout-box",
			x: callout.x,
			y: callout.y,
			width: callout.width,
			height,
			rx: 12
		}));

		rows.forEach((row, n) => {

			const y = callout.y + 30 + n * 44;

			group.append(
				mapEl("text", { class: "callout-name", x: callout.x + 14, y }, row.name),
				mapEl("text", { class: "callout-asn", x: callout.x + 14, y: y + 18 }, row.asn),
				mapEl("text", { class: "callout-where", x: callout.x + 86, y: y + 18 }, row.place)
			);
		});

		callouts.append(group);
	});

	// On a phone the whole region is too small to read, so zoom in on
	// the middle of it. The land, the sea and the dots all follow.
	const full = svg.getAttribute("viewBox");

	const [px0] = project(MAP_PHONE.lon0, 0);
	const [px1] = project(MAP_PHONE.lon1, 0);
	const [, py0] = project(0, MAP_PHONE.top);
	const [, py1] = project(0, MAP_PHONE.bottom);

	const phone = [px0, py0, px1 - px0, py1 - py0].map(v => v.toFixed(0)).join(" ");

	const narrow = window.matchMedia("(max-width: 640px)");

	const fit = () => svg.setAttribute("viewBox", narrow.matches ? phone : full);

	fit();

	narrow.addEventListener("change", fit);
}

document.addEventListener("DOMContentLoaded", () => {

	const svg = document.getElementById("sea-map");

	if(svg) drawMap(svg);
});
