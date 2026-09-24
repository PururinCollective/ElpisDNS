# Adding your resolver to ΕΛΠΙΣ DNS

Everything the website shows comes out of one file: [`dns.json`](dns.json).
No build step, no framework, no meeting. Copy a block, change the values,
open a pull request.

## 1. Copy a block

Open `dns.json`, find the `resolvers` array, and copy any entry. A minimal
one looks like this:

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
	"servers": [
		"dns.example.com"
	]
}
```

Your editor will autocomplete and validate as you type, because the file
points at [`dns.schema.json`](dns.schema.json). If something is red, read the
tooltip before you push.

## 2. Field reference

| Field | Required | What it is |
| --- | --- | --- |
| `id` | recommended | Unique slug, lower case with dashes. It becomes the share link, `https://elpis.violetnetworks.xyz/#your-id/DoH`. |
| `region` | yes | A `code` from the top level `regions` list. Adding a new country? Add it there first. |
| `provider` | yes | Who runs the box. Shown as a button, so keep it short. |
| `filter` | yes | A `code` from the top level `filters` list. `NSFW` = ads, trackers and malware only. `SFW` = the same plus adult content and safe search. |
| `network` | yes | `IPv4`, `IPv6` or `IPv4+IPv6`. Say what the resolver actually answers on. |
| `feature` | yes | What makes it different from its siblings: `CDN`, `International`, `DNS64/NAT64`. |
| `kind` | yes | Any of `DoH`, `DoT`, `DoQ`. List only what is really listening. |
| `servers` | yes | Hostnames, at least one. No scheme, no path, no port. The site picks one at random so the load stays spread out. |
| `dohPath` | no | Only if your DoH path is not `/dns-query`. |
| `dotPort` | no | Only if your DoT port is not `853`. |
| `maintainer` | no | Who to poke when it breaks. |
| `homepage` | no | Operator page, AS page or status page. |
| `notes` | no | One or two sentences, shown under the selection. |
| `stamp` | no | What the generated `sdns://` stamp claims: `{ "dnssec": true, "nolog": true, "nofilter": false }`. Defaults to DNSSEC on, no logs, filtering on. |

Entries that share a region, provider, filter, network and feature are the
same entry &mdash; add your hostname to its `servers` list instead of creating
a second block.

## 3. What we expect from a resolver

This is a public list. People will point their phones, routers and families
at whatever is on it, so the bar is not decorative.

- **Encrypted only.** DoH, DoT or DoQ, with a valid publicly trusted certificate. No plain port 53 entries.
- **A stable hostname.** Something you intend to keep. Removing an entry is easy, but every removal breaks somebody's router.
- **No answer tampering** beyond the filtering profile you declared. If you block ads, say `NSFW`. If you also block adult content, say `SFW`. If you block anything else, say so in `notes` &mdash; a surprise block list is exactly what this project exists to route around.
- **Don't sell the queries.** Do not log, profile, or hand query data to third parties. If you are legally required to keep something, put it in `notes` and be honest about it.
- **Keep it up.** Occasional maintenance is normal; a host that is dead for weeks gets removed.
- **Your stamp must be true.** The site generates an `sdns://` stamp for your entry, and clients act on the flags inside it. If you do not validate DNSSEC, or you keep query logs, set `"stamp": { "dnssec": false }` or `{ "nolog": false }` on your entry. Claiming a property you do not provide is worse than not being listed.

## 4. Test before you push

```bash
python -m http.server 8000
```

Open <http://localhost:8000>, then check:

- Your entry appears under the right Filter, Region, Provider, Network and Feature.
- Switching between DoH and DoT builds the endpoint you expected.
- The browser console is clean. A malformed entry is skipped with a warning there.
- Both themes look right &mdash; click the icon in the top bar to cycle system, light and dark.

Then test the resolver itself:

```bash
# DoH
curl -H 'accept: application/dns-json' 'https://dns.example.com/dns-query?name=example.com&type=A'

# DoT
kdig -d @dns.example.com +tls-ca +tls-host=dns.example.com example.com
```

If you do not have `kdig`, the [Setup page](setup.html) lists other ways to
check what is really answering.

## 5. Re-stamp the assets

If you touched any CSS, JS or JSON - `dns.json` counts - refresh the cache
busting hashes before you commit:

```bash
python tools/stamp-assets.py
```

Every local asset link is suffixed with the first eight hex characters of the
file's SHA-256, so a changed file lands on a URL no cache has seen before.
It rewrites nothing when nothing changed, and `--check` exits non-zero if a
stamp is stale, which makes it a one line CI guard.

## 6. Open the pull request

Say who you are, where the server sits, what it filters, and how long you
plan to run it. That is the whole ritual.

## Working on the website itself

| File | What it holds |
| --- | --- |
| `index.html` | The front page and the selector markup |
| `resolver.html` | ΕΛΠΙΣ Resolver: server table and upstream lists |
| `self-host.html` | Running your own ΕΛΠΙΣ Resolver |
| `ml-dsa-44.html` | Post-quantum DNSSEC and ML-DSA-44 |
| `setup.html` | The setup guide, linked from the top bar |
| `mission.html` | Why ΕΛΠΙΣ exists: promises, block lists, how a lookup travels |
| `resolvers.json` | Public ΕΛΠΙΣ Resolver addresses. Edit this, not the HTML |
| `style-main.css` | Every colour token, both themes, all components, the narrow layout |
| `js/app.js` | Selector engine, endpoint building, share links |
| `js/app-resolvers.js` | Resolver table and AdGuard Home / Pi-hole lists, from `resolvers.json` |
| `js/app-theme.js` | System, light and dark switching |
| `js/app-copy.js` | Clipboard, shared by every page |
| `js/app-stamp.js` | Builds the `sdns://` stamp for the selected endpoint |
| `js/app-quote.js` | Footer quotes |
| `js/app-mikrotik.js` | The `.rsc` generator |
| `js/app-setup.js` | Setup page helpers |
| `img/hero-map.svg` | The animated map. Generated, and not shown by the current design |
| `tools/make-hero-map.py` | Regenerates the map and its reduced-motion still |
| `tools/make-og-mldsa.py` | Redraws `img/og-ml-dsa-44.png`, the share card for the ML-DSA page |
| `tools/stamp-assets.py` | Re-stamps `?hash=` cache busters. Run after changing CSS, JS or JSON |

House style: tabs for indentation, blank line between logical steps, no
build tooling. Colours go in the token block at the top of `style-main.css`
&mdash; if you find yourself typing a hex code anywhere else, add a token instead,
or the dark theme will quietly break.
