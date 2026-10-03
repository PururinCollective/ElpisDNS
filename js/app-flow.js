/*
	ΕΛΠΙΣ DNS - the banner animation

	Plays one DNS lookup from start to finish: your device asks ΕΛΠΙΣ DNS,
	ΕΛΠΙΣ DNS asks ΕΛΠΙΣ Resolver, the resolver walks root, TLD and name
	server, and the answer travels all the way back.

	The boxes are plain HTML laid out by the CSS grid, so they reflow on a
	phone like anything else. This file measures where they landed, draws
	the wires between them in the SVG behind, and runs light along one
	wire at a time, the way the mesh on openpon.org does.

	One clock drives everything and it only moves while the banner is on
	screen, so a background tab costs nothing. Visitors who ask for reduced
	motion get the wires and the full list of steps, standing still.
*/

const FLOW_LINKS = [
	["you", "dns"],
	["dns", "resolver"],
	["resolver", "root"],
	["resolver", "tld"],
	["resolver", "ns"]
];

const FLOW_HOP = 1050;
const FLOW_NOTE = 1100;

/*
	The script. "from/to" is a hop along a wire, "note" pops a label over a
	box. "step" is the line of the caption list that is lit meanwhile.
*/
const FLOW_SCRIPT = [
	{ step: 0, wait: 700 },
	{ step: 0, from: "you", to: "dns", say: "🔒 example.com?" },
	{ step: 1, note: "dns", say: "Not an ad ✓" },
	{ step: 1, from: "dns", to: "resolver", say: "example.com?" },
	{ step: 2, from: "resolver", to: "root", say: "example.com?" },
	{ step: 2, from: "root", to: "resolver", say: "ask .com", answer: true },
	{ step: 3, from: "resolver", to: "tld", say: "example.com?" },
	{ step: 3, from: "tld", to: "resolver", say: "ask ns.example.com", answer: true },
	{ step: 4, from: "resolver", to: "ns", say: "example.com?" },
	{ step: 4, from: "ns", to: "resolver", say: "203.0.113.10", answer: true },
	{ step: 4, note: "resolver", say: "DNSSEC ✓" },
	{ step: 5, from: "resolver", to: "dns", say: "203.0.113.10", answer: true },
	{ step: 5, from: "dns", to: "you", say: "🔒 203.0.113.10", answer: true },
	{ step: 5, note: "you", say: "Cached ✓", wait: 2400 }
];

const SVG_NS = "http://www.w3.org/2000/svg";

function svgEl(name, attrs){

	const node = document.createElementNS(SVG_NS, name);

	Object.entries(attrs || {}).forEach(([key, value]) => {
		node.setAttribute(key, value);
	});

	return node;
}

function ease(t){

	return t < .5
		? 4 * t * t * t
		: 1 - Math.pow(-2 * t + 2, 3) / 2;
}

function startFlow(root){

	const svg = root.querySelector(".flow-wires");
	const steps = [...document.querySelectorAll("#flow-steps li")];

	const nodes = {};

	root.querySelectorAll("[data-node]").forEach(node => {
		nodes[node.dataset.node] = node;
	});

	// Two wires per link, one each way, so a reply can run backwards
	// without reversing a path by hand.
	const wires = {};

	const tail = svgEl("path", { class: "streak-tail", pathLength: 1000 });
	const core = svgEl("path", { class: "streak-core", pathLength: 1000 });
	const head = svgEl("circle", { class: "streak-head", r: 3.5 });
	const streak = svgEl("g", { opacity: 0 });

	streak.append(tail, core, head);

	const chip = document.createElement("span");
	chip.className = "flow-chip";
	chip.setAttribute("aria-hidden", "true");

	const note = document.createElement("span");
	note.className = "flow-note";
	note.setAttribute("aria-hidden", "true");

	root.append(chip, note);

	function box(node){

		const outer = root.getBoundingClientRect();
		const r = node.getBoundingClientRect();

		return {
			left: r.left - outer.left,
			right: r.right - outer.left,
			top: r.top - outer.top,
			bottom: r.bottom - outer.top,
			cx: r.left - outer.left + r.width / 2,
			cy: r.top - outer.top + r.height / 2
		};
	}

	// A cubic from the facing edge of one box to the facing edge of the
	// other, leaving and arriving level, like a cable.
	function curve(a, b){

		const A = box(nodes[a]);
		const B = box(nodes[b]);

		const forward = B.cx >= A.cx;

		const x1 = forward ? A.right : A.left;
		const x2 = forward ? B.left : B.right;

		const pull = (x2 - x1) * .5;

		return `M${x1} ${A.cy} C${x1 + pull} ${A.cy} ${x2 - pull} ${B.cy} ${x2} ${B.cy}`;
	}

	function layout(){

		const outer = root.getBoundingClientRect();

		svg.setAttribute("viewBox", `0 0 ${outer.width} ${outer.height}`);
		svg.textContent = "";

		// Measured but never drawn. Firefox will not measure a path that
		// is not in the document, so they live in a hidden group.
		const paths = svgEl("g", { visibility: "hidden" });

		FLOW_LINKS.forEach(([a, b]) => {

			const there = curve(a, b);

			svg.append(svgEl("path", { class: "wire", d: there }));

			wires[`${a}>${b}`] = svgEl("path", { d: there });
			wires[`${b}>${a}`] = svgEl("path", { d: curve(b, a) });

			paths.append(wires[`${a}>${b}`], wires[`${b}>${a}`]);
		});

		svg.append(paths, streak);
	}

	/* ---------- painting one moment ---------- */

	let lit = -1;

	function light(step){

		if(step === lit) return;

		lit = step;

		steps.forEach((li, i) => {
			li.classList.toggle("is-on", i === step);
			li.classList.toggle("is-done", i < step);
		});
	}

	function activate(...names){

		Object.entries(nodes).forEach(([name, node]) => {
			node.classList.toggle("is-active", names.includes(name));
		});
	}

	function place(label, x, y){

		// Kept inside the window, or a long label hangs off a phone screen.
		const width = label.offsetWidth;
		const room = root.clientWidth;

		const left = Math.max(4, Math.min(room - width - 4, x - width / 2));

		label.style.transform = `translate(${left}px, ${y}px)`;
	}

	function paintHop(action, t){

		const wire = wires[`${action.from}>${action.to}`];

		if(!wire) return;

		const e = ease(t);

		// Head runs the whole wire; the tail trails behind it and is
		// pulled in after it as it arrives.
		const span = 160;
		const reach = e * (1000 + span);

		tail.setAttribute("d", wire.getAttribute("d"));
		core.setAttribute("d", wire.getAttribute("d"));

		tail.setAttribute("stroke-dasharray", `${span} 3000`);
		tail.setAttribute("stroke-dashoffset", span - reach);

		core.setAttribute("stroke-dasharray", `40 3000`);
		core.setAttribute("stroke-dashoffset", 40 - Math.min(reach, 1040));

		const length = wire.getTotalLength();
		const point = wire.getPointAtLength(Math.min(e, 1) * length);

		head.setAttribute("cx", point.x);
		head.setAttribute("cy", point.y);

		streak.setAttribute("opacity", t >= 1 ? 0 : 1);
		streak.classList.toggle("is-answer", !!action.answer);

		chip.textContent = action.say;
		chip.classList.toggle("is-answer", !!action.answer);
		chip.classList.toggle("is-on", t > .04 && t < .96);

		place(chip, point.x, point.y - 34);
	}

	function paintNote(action, t){

		const b = box(nodes[action.note]);

		note.textContent = action.say;
		note.classList.toggle("is-on", t < .92);

		place(note, b.cx, b.top - 32);
	}

	function paint(action, t){

		light(action.step);

		if(action.from){

			note.classList.remove("is-on");
			activate(action.from, action.to);
			paintHop(action, t);
		}
		else if(action.note){

			chip.classList.remove("is-on");
			streak.setAttribute("opacity", 0);
			activate(action.note);
			paintNote(action, t);
		}
		else{

			chip.classList.remove("is-on");
			note.classList.remove("is-on");
			streak.setAttribute("opacity", 0);
			activate();
		}
	}

	function length(action){

		if(action.from) return FLOW_HOP;
		if(action.note) return action.wait || FLOW_NOTE;

		return action.wait || 600;
	}

	/* ---------- the clock ---------- */

	let index = 0;
	let started = 0;
	let clock = 0;
	let last = null;
	let visible = false;
	let frame = 0;

	function tick(now){

		frame = 0;

		if(last !== null){
			clock += Math.min(now - last, 64);
		}

		last = now;

		let action = FLOW_SCRIPT[index];
		let t = (clock - started) / length(action);

		while(t >= 1){

			paint(action, 1);

			index = (index + 1) % FLOW_SCRIPT.length;
			started += length(action);

			action = FLOW_SCRIPT[index];
			t = (clock - started) / length(action);
		}

		paint(action, Math.max(0, t));

		run();
	}

	function run(){

		if(visible && !document.hidden && !frame){
			frame = requestAnimationFrame(tick);
		}
	}

	function halt(){

		if(frame){
			cancelAnimationFrame(frame);
			frame = 0;
		}

		last = null;
	}

	layout();

	if(window.ResizeObserver){
		new ResizeObserver(() => layout()).observe(root);
	}
	else{
		window.addEventListener("resize", layout);
	}

	const still = window.matchMedia("(prefers-reduced-motion: reduce)");

	if(still.matches) return;

	document.querySelector(".flow-window")?.classList.add("flow-live");

	new IntersectionObserver(entries => {

		visible = entries[0].isIntersecting;

		visible ? run() : halt();

	}).observe(root);

	document.addEventListener("visibilitychange", () => {
		document.hidden ? halt() : run();
	});
}

document.addEventListener("DOMContentLoaded", () => {

	const root = document.getElementById("flow");

	if(root) startFlow(root);
});
