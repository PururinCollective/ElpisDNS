<p align="center">
	<img src="img/elpis-logo.svg" alt="ΕΛΠΙΣ DNS" width="620">
</p>

# ΕΛΠΙΣ DNS

**Resolve freely. Answer to no one.** By the community, for the community.

Every website you open begins with a question: *where is this?* Whoever answers
that question owns your internet &mdash; they can log it, sell it, or decide that
today, for reasons nobody wrote down, this particular door is closed.

ΕΛΠΙΣ DNS is a community-run set of encrypted resolvers for South East Asia, so
that question stays between you and someone who does not want anything from it.
DoH and DoT only, four networks carrying it, ECS for the CDNs, DNS64/NAT64 for
IPv6-only hosts, and no ledger of your curiosity. Aligned with the vision of
[EFF Internet Freedom and Privacy](https://www.eff.org/).

- **[Pick an endpoint](https://elpis.violetnetworks.xyz/)** &mdash; filter, region, provider, transport
- **[Why ΕΛΠΙΣ](https://elpis.violetnetworks.xyz/mission.html)** &mdash; what we block, what we refuse to keep, and how to check it
- **[Setup guide](https://elpis.violetnetworks.xyz/setup.html)** &mdash; Android, Windows, iOS, Firefox, Chrome, MikroTik, OpenWrt, AdGuard Home
- **[Add your resolver](CONTRIBUTING.md)** &mdash; one JSON block, one pull request
- **[The resolver we wrote](https://github.com/PururinCollective/elpis-resolver)** &mdash; C99, SIMD, ML-DSA-44, one static binary

## What it is built on

- Privacy first: encrypted transport, no query logging, no profiling
- [ΕΛΠΙΣ Resolver](https://github.com/PururinCollective/elpis-resolver), our own recursive
  resolver &mdash; portable C99 with SIMD kernels, no dependencies, and the second resolver
  in the world to validate ML-DSA-44 post-quantum DNSSEC after Cloudflare
- Battle tested from 1.0.0 to 2.2.0 behind `a`, `b`, `c` and `gg.hitoha.moe`, about
  29 million queries a day between them, built in the open with community
  collaboration and Claude AI assistance
- EDNS Client Subnet on AS154516 only, so YouTube and the other CDNs answer for where
  you are; every other network sends no subnet at all
- An `sdns://` DNS stamp generated for every endpoint, for dnscrypt-proxy and friends
- Ads, trackers, malware and phishing filtered by default
- A Family profile with adult content blocked and safe search enforced
- CDN acceleration and regional routing optimisation
- DNS64/NAT64 for IPv6-only networks
- Internet freedom &mdash; a block list is somebody's opinion, and the network was designed to route around exactly that

## Adding your DoH/DoT resolver

Everything the website shows comes out of one file: [`dns.json`](dns.json).
Copy a block inside `resolvers`, change the values, open a pull request.

```json
{
	"id": "sg-yourname-intl",
	"region": "SG",
	"provider": "Your Name",
	"filter": "NSFW",
	"network": "IPv4+IPv6",
	"feature": "International",
	"kind": ["DoH", "DoT"],
	"maintainer": "Your Name",
	"homepage": "https://example.com",
	"notes": "One sentence the visitor sees when this entry is selected.",
	"servers": ["dns.example.com"]
}
```

Your editor validates as you type against [`dns.schema.json`](dns.schema.json).
Non-standard DoH path or DoT port? Add `dohPath` or `dotPort`. A new country?
Add it to the `regions` list at the top of the file and the button appears by
itself. The full field reference and the expectations we have of a listed
resolver are in **[CONTRIBUTING.md](CONTRIBUTING.md)**.

## Running it locally

No build step, no framework, no dependencies. Serve the folder:

```
python -m http.server 8000
```

Then open <http://localhost:8000>. `file://` will not work &mdash; `dns.json` is
fetched over HTTP.

| File | What it holds |
| --- | --- |
| `dns.json` | Every resolver, region and filtering profile |
| `network.json` | The networks on the map: ASNs, places, endpoints, queries a day |
| `dns.schema.json` | Schema that validates the above in your editor |
| `index.html` | Front page and selector markup |
| `setup.html` | Setup guide |
| `mission.html` | Why ΕΛΠΙΣ exists: block lists, recursion, the raw resolvers |
| `style-main.css` | Colour tokens, light and dark themes, all components |
| `style-mobile.css` | Narrow layout |
| `js/app.js` | Selector engine, endpoint building, share links |
| `js/app-theme.js` | System / light / dark switching |
| `js/app-copy.js` | Clipboard, shared by every page |
| `js/app-stamp.js` | `sdns://` DNS stamp generator |
| `js/app-quote.js` | Footer quotes |
| `js/app-mikrotik.js` | RouterOS `.rsc` generator |
| `js/app-setup.js` | Setup page helpers |
| `js/app-mesh.js` | The animated network behind the hero and the page heads |
| `js/app-map.js` | The South East Asia network map and the cards under it |
| `img/sea-map.json` | Land for the map, generated |
| `tools/make-sea-map.py` | Regenerates that land. Only needed if you change the region |
| `tools/stamp-assets.py` | Re-stamps `?hash=` cache busters after any asset change |

The look is Firefox's: ink purple, violet, and the yellow-to-violet sweep of
the fox, set in Mozilla Headline and Mozilla Text. The banner is a network
drawn by `js/app-mesh.js` &mdash; nodes, links and streaks of light running
across them &mdash; sized to whatever screen it lands on, paused when it scrolls
away, and left still for anyone who asks for reduced motion.

The network map reads `network.json` for the nodes and `img/sea-map.json`
for the land. The land is Natural Earth 1:50m clipped to the region, and only
needs rebuilding if the region changes:

```
python tools/make-sea-map.py
```

The site follows your operating system's light or dark preference out of the box;
the icon in the top bar cycles system, light and dark, and the choice is remembered.

### Cache busting

Asset links carry a content hash rather than a hand-maintained version number:

```
python tools/stamp-assets.py
```

Every local `.css`, `.js`, `.json` and `.svg` reference becomes
`style-main.css?hash=2338f332`, the first eight hex characters of the file's
SHA-256. Change a file and its URL changes with it, so Cloudflare has to
fetch the new copy; leave a file alone and the URL is stable, so nobody
re-downloads it. Run it after any asset change, or wire `--check` into CI to
be told when you forget. It follows references through files, so editing
`dns.json` re-stamps `js/app.js` and then the pages that load it.

## Usage

Quick way to use our DNS resolvers. The [setup page](https://elpis.violetnetworks.xyz/setup.html)
covers every platform in detail &mdash; here is the short version for routers.

### Android

Settings &rarr; Network &amp; internet &rarr; **Private DNS** &rarr; provider hostname:

```
b.hitoha.moe
```

### MikroTik

Basic DNS first:

```rsc
/ip dns
set servers=1.0.0.1,1.1.1.1 allow-remote-requests=yes
```

DoH forwarders:

```rsc
/ip dns forwarders
add doh-servers="https://b.hitoha.moe/dns-query,https://c.hitoha.moe/dns-query,https://gg.hitoha.moe/dns-query" name=AdGuard
```

Static entries so the router can find the resolver it is about to use:

```rsc
/ip dns static
add address=151.158.198.53 name=b.hitoha.moe type=A
add address=160.187.96.67 name=c.hitoha.moe type=A
add address=103.131.188.71 name=gg.hitoha.moe type=A
add name=* forward-to=AdGuard type=FWD
```

The front page will generate this file for whichever endpoint you pick &mdash;
press **.rsc**.

## The networks

By the community, for the community. ΕΛΠΙΣ is carried by four autonomous
systems, and no single one of them can switch it off:

| ASN | Network | Where |
| --- | --- | --- |
| [AS154516](https://bgp.tools/as/154516) | [Perfect Network](https://perfect.my/) | Semenyih, Malaysia &mdash; ECS on |
| [AS153334](https://bgp.tools/as/153334) | Origin TechLab | Kuala Lumpur, Malaysia |
| [AS135134](https://bgp.tools/as/135134) | Shana Network | Singapore |
| [AS204535](https://bgp.tools/as/204535) | [kevin.moe](https://kevin.moe/) | Malaysia |

---

*~ Part of Pururin Collective Project ~*
