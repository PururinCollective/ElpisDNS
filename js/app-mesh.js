/*
	ΕΛΠΙΣ DNS - hero mesh

	The network drawn behind the hero and the page heads: nodes on a
	jittered grid, each tied to its nearest neighbours, and streaks of
	light running multi-hop routes across it in the colours of the fox.

	Built here rather than shipped as an SVG file so it can match the
	shape of whatever it sits in - a phone hero is tall and narrow, a
	desktop one is wide - without cropping or stretching. The seed is
	fixed, so the same screen always gets the same mesh.

	Any element with data-mesh gets one. data-mesh="page" is the shorter,
	quieter variant for the mission and setup heads.

	Motion: streaks pause when the mesh scrolls out of view, and are not
	drawn at all for visitors who ask for reduced motion.
*/

(function(){

	const NS = "http://www.w3.org/2000/svg";

	// Roughly one node per CELL x CELL pixels.
	const CELL = 118;

	const STREAK_COLOURS = [
		"#ffbd4f",
		"#ff7139",
		"#ff4aa2",
		"#c9a8ff",
		"#ff9640",
		"#b48cff"
	];

	const PRESETS = {
		hero: { seed: 20260930, streaks: 11, nearShare: .38 },
		page: { seed: 154516, streaks: 6, nearShare: .3 }
	};

	const reducedMotion =
		window.matchMedia("(prefers-reduced-motion: reduce)");

	/* ---------- randomness that repeats ---------- */

	function mulberry32(seed){

		return function(){

			seed = seed + 0x6D2B79F5 | 0;

			let t = Math.imul(seed ^ seed >>> 15, 1 | seed);

			t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;

			return ((t ^ t >>> 14) >>> 0) / 4294967296;
		};
	}

	/* ---------- geometry ---------- */

	function placeNodes(width, height, preset, rand){

		// The grid runs a little past every edge, so links leave the frame
		// instead of stopping politely at it.
		const pad = CELL * .6;
		const cols = Math.max(4, Math.round((width + pad * 2) / CELL));
		const rows = Math.max(3, Math.round((height + pad * 2) / CELL));
		const cw = (width + pad * 2) / cols;
		const ch = (height + pad * 2) / rows;

		const nodes = [];

		for(let r = 0; r < rows; r++){

			for(let c = 0; c < cols; c++){

				if(rand() < .14) continue;

				const near = rand() < preset.nearShare;

				nodes.push({
					x: (c + .5 + (rand() - .5) * .85) * cw - pad,
					y: (r + .5 + (rand() - .5) * .85) * ch - pad,
					near,
					r: near ? 3.2 + rand() * 1.4 : 2 + rand() * 1,
					warm: rand() < .1,
					pulse: rand() < .14,
					links: []
				});
			}
		}

		return { nodes, reach: Math.hypot(cw, ch) * 1.25 };
	}

	function linkNodes(nodes, reach){

		const edges = [];
		const seen = new Set();

		nodes.forEach((node, i) => {

			const nearest = nodes
				.map((other, j) => ({ j, d: Math.hypot(other.x - node.x, other.y - node.y) }))
				.filter(o => o.j !== i && o.d < reach)
				.sort((a, b) => a.d - b.d)
				.slice(0, 3);

			nearest.forEach(({ j }) => {

				const key = i < j ? `${i}-${j}` : `${j}-${i}`;

				if(seen.has(key)) return;

				seen.add(key);

				edges.push([i, j]);

				node.links.push(j);
				nodes[j].links.push(i);
			});
		});

		return edges;
	}

	// A walk that keeps roughly to one heading, so a streak crosses the
	// frame like traffic rather than circling one node.
	function route(nodes, rand){

		let at = Math.floor(rand() * nodes.length);
		let heading = rand() * Math.PI * 2;

		const path = [at];
		const hops = 6 + Math.floor(rand() * 5);

		for(let step = 0; step < hops; step++){

			const here = nodes[at];

			const next = here.links
				.filter(j => !path.includes(j))
				.map(j => {

					const angle = Math.atan2(nodes[j].y - here.y, nodes[j].x - here.x);

					return { j, score: Math.cos(angle - heading) + rand() * .6 };
				})
				.sort((a, b) => b.score - a.score)[0];

			if(!next) break;

			const target = nodes[next.j];

			heading = Math.atan2(target.y - here.y, target.x - here.x);

			at = next.j;

			path.push(at);
		}

		return path.length > 3 ? path : null;
	}

	/* ---------- drawing ---------- */

	function round(value){
		return Math.round(value * 10) / 10;
	}

	function build(host){

		const preset = PRESETS[host.dataset.mesh] || PRESETS.hero;

		const width = Math.max(320, host.clientWidth);
		const height = Math.max(240, host.clientHeight);

		const rand = mulberry32(preset.seed);

		const { nodes, reach } = placeNodes(width, height, preset, rand);

		const edges = linkNodes(nodes, reach);

		const layer = near => {

			const lines = edges
				.filter(([a, b]) => (nodes[a].near && nodes[b].near) === near)
				.map(([a, b]) =>
					`<line class="mesh-edge" x1="${round(nodes[a].x)}" y1="${round(nodes[a].y)}" x2="${round(nodes[b].x)}" y2="${round(nodes[b].y)}"/>`
				)
				.join("");

			const dots = nodes
				.filter(node => node.near === near)
				.map(node => {

					const style = node.pulse
						? ` style="--dur:${(3 + rand() * 3).toFixed(1)}s;--delay:-${(rand() * 5).toFixed(1)}s"`
						: "";

					const classes = ["mesh-node", node.warm && "warm", node.pulse && "pulse"]
						.filter(Boolean)
						.join(" ");

					return `<g class="${classes}"${style}>` +
						`<circle class="mesh-halo" cx="${round(node.x)}" cy="${round(node.y)}" r="${round(node.r * 3)}"/>` +
						`<circle class="mesh-core" cx="${round(node.x)}" cy="${round(node.y)}" r="${round(node.r)}"/>` +
						`</g>`;
				})
				.join("");

			return `<g class="${near ? "mesh-near" : "mesh-far"}">${lines}${dots}</g>`;
		};

		let streaks = "";

		for(let i = 0, made = 0; i < preset.streaks * 4 && made < preset.streaks; i++){

			const path = route(nodes, rand);

			if(!path) continue;

			const d = "M" + path
				.map(j => `${round(nodes[j].x)} ${round(nodes[j].y)}`)
				.join(" L");

			const colour = STREAK_COLOURS[made % STREAK_COLOURS.length];

			// Negative delays start every streak somewhere along its run,
			// so the first frame is already busy.
			const dur = (3 + rand() * 3.2).toFixed(1);
			const delay = (rand() * 5).toFixed(1);

			const style = `stroke:${colour};--dur:${dur}s;--delay:-${delay}s`;

			streaks +=
				`<path class="mesh-streak tail" pathLength="1000" d="${d}" style="${style}"/>` +
				`<path class="mesh-streak core" pathLength="1000" d="${d}" style="${style}"/>`;

			made++;
		}

		host.innerHTML =
			`<svg xmlns="${NS}" viewBox="0 0 ${width} ${height}" preserveAspectRatio="none" focusable="false">` +
			layer(false) +
			layer(true) +
			(reducedMotion.matches ? "" : `<g class="mesh-streaks">${streaks}</g>`) +
			`</svg>`;

		host.dataset.builtWidth = width;
	}

	/* ---------- lifecycle ---------- */

	function watch(host){

		build(host);

		// Rebuild only when the width really changes; mobile browsers
		// resize the viewport every time the address bar slides away.
		if("ResizeObserver" in window){

			let timer;

			new ResizeObserver(() => {

				clearTimeout(timer);

				timer = setTimeout(() => {

					if(Math.abs(host.clientWidth - Number(host.dataset.builtWidth)) > 40){
						build(host);
					}
				}, 180);

			}).observe(host);
		}

		if("IntersectionObserver" in window){

			new IntersectionObserver(entries => {

				entries.forEach(entry =>
					host.classList.toggle("is-paused", !entry.isIntersecting)
				);

			}).observe(host);
		}
	}

	function start(){
		document.querySelectorAll("[data-mesh]").forEach(watch);
	}

	reducedMotion.addEventListener("change", start);

	if(document.readyState === "loading"){
		document.addEventListener("DOMContentLoaded", start);
	}
	else{
		start();
	}

})();
