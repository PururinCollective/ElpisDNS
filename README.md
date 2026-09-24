<p align="center">
	<img src="img/elpis-logo.svg" alt="ΕΛΠΙΣ DNS" width="620">
</p>

# ΕΛΠΙΣ DNS

**Resolve freely. Answer to no one.**

Every website you open begins with a question: *where is this?* Whoever answers
that question owns your internet &mdash; they can log it, sell it, or decide that
today, for reasons nobody wrote down, this particular door is closed.

ΕΛΠΙΣ DNS is a community-run set of encrypted resolvers so that question stays
between you and someone who does not want anything from it. DoH and DoT only,
regional routing, CDN acceleration, DNS64/NAT64, and no ledger of your curiosity.
Aligned with the vision of [EFF Internet Freedom and Privacy](https://www.eff.org/).

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
| `dns.schema.json` | Schema that validates the above in your editor |
| `resolvers.json` | Public ΕΛΠΙΣ Resolver addresses, the backup notice, and what each server runs |
| `index.html` | Front page and selector markup |
| `resolver.html` | ΕΛΠΙΣ Resolver: the server table and the AdGuard Home / Pi-hole upstream lists |
| `self-host.html` | Running your own resolver, from a home lab to ISP hardware |
| `ml-dsa-44.html` | Post-quantum DNSSEC: ML-DSA-44, and why we are second in the world to validate it |
| `setup.html` | Setup guide |
| `mission.html` | Why ΕΛΠΙΣ exists: promises, block lists, how a lookup travels |
| `style-main.css` | Colour tokens, light and dark themes, all components and the narrow layout |
| `js/app.js` | Selector engine, endpoint building, share links |
| `js/app-resolvers.js` | Builds the resolver table and upstream lists from `resolvers.json` |
| `js/app-theme.js` | System / light / dark switching |
| `js/app-copy.js` | Clipboard, shared by every page |
| `js/app-stamp.js` | `sdns://` DNS stamp generator |
| `js/app-quote.js` | Footer quotes |
| `js/app-mikrotik.js` | RouterOS `.rsc` generator |
| `js/app-setup.js` | Setup page helpers, and copy buttons on code blocks |
| `img/hero-map.svg` | Animated night map, generated. Not shown by the current design |
| `tools/make-hero-map.py` | Regenerates that map. Only needed if you change it |
| `img/og-*.png`, `img/icon-*.png`, `favicon.ico`, `img/apple-touch-icon.png` | Share cards for each page, the favicon and app icons, generated |
| `tools/make-brand-images.py` | Redraws them. Needs Pillow and Noto Sans |
| `tools/indexnow.py` | Tells Bing, Yandex and friends which pages changed. Run after a deploy |
| `site.webmanifest` | App name, colours and icons for browsers and search results |
| `404.html` | Page-not-found, served by the host for missing paths |
| `tools/stamp-assets.py` | Re-stamps `?hash=` cache busters after any asset change |

The colours are the ones the ΕΛΠΙΣ Resolver status page uses &mdash; steel grey
and one blue accent &mdash; so the site and the resolver read as one product.

The public resolver addresses live in `resolvers.json`. Add a server, change a
role between `active` and `backup`, or clear the `notice`, and the resolver
page, the setup page and every AdGuard Home and Pi-hole list follow.

The site follows your operating system's light or dark preference out of the box;
the icon in the top bar cycles system, light and dark, and the choice is remembered.

### Search engines and link previews

Every page carries the same set, so a link to any of them previews properly
and indexes cleanly:

- **Search:** title, description, canonical URL and robots rules. Structured
  data (Organization, WebSite, WebPage and breadcrumbs, plus the resolver's
  SoftwareApplication and the ML-DSA page's TechArticle and FAQ) is read by
  Google, Bing and Yandex alike.
- **Link previews:** Open Graph for Facebook, LinkedIn, Discord, Telegram,
  WhatsApp and iMessage; Twitter card tags for X; and `twitter:label` /
  `twitter:data` pairs, which Slack prints under the preview.
- **Share cards:** the front page uses the illustration, `img/og-image.jpg`.
  Every other page has its own 1200x630 card, drawn by
  `python tools/make-brand-images.py`, which also draws the manifest icons.
  Change a card's wording in `CARDS` at the top of that script.
- **`sitemap.xml`** lists every page with its card, and `robots.txt` points
  to it. Bump `<lastmod>` when a page changes.
- **IndexNow:** after a deploy, `python tools/indexnow.py` tells Bing (which
  Yahoo and DuckDuckGo draw on), Yandex, Naver, Seznam and Yep straight
  away. Google does not take part and reads the sitemap instead.
- **Ownership:** the head of `index.html` has a commented block for the
  Google, Bing, Yandex, Baidu and Naver verification codes. A DNS TXT record
  does the same job for the whole domain.
- **`404.html`** is served for missing paths and asks not to be indexed.

### Cache busting

Asset links carry a content hash rather than a hand-maintained version number:

```
python tools/stamp-assets.py
```

Every local `.css`, `.js`, `.json`, `.svg`, `.png` and `.ico` reference becomes
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

## Sponsor

Proudly Sponsored by [Perfect Network](https://perfect.my/) ([AS154516](https://bgp.tools/as/154516))

![PERFECT](img/perfect.png)

---

*~ Part of Pururin Collective Project ~*
