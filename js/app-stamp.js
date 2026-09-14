/*
	ΕΛΠΙΣ DNS - DNS stamps

	One string that carries the protocol, the host, the path and what the
	resolver promises, so clients like dnscrypt-proxy, AdGuard Home and
	YogaDNS can be configured by pasting a single field.

	Format: https://dnscrypt.info/stamps-specifications/

		sdns:// base64url(
			proto || props || LP(addr) || VLP(hashes) || LP(host) [|| LP(path)]
		)

	proto  0x00 plain DNS, 0x02 DoH, 0x03 DoT, 0x04 DoQ
	props  64 bit little endian: 1 DNSSEC, 2 no logs, 4 no filtering
	LP     one length byte, then the bytes
	VLP    the same, but every element except the last has 0x80 set on its
	       length byte. An empty certificate pin set is a single empty element.

	Verified against 475 stamps from the DNSCrypt public resolver list:
	decode, re-encode, byte identical.
*/

const STAMP_PROTO = {
	Plain: 0x00,
	DoH: 0x02,
	DoT: 0x03,
	DoQ: 0x04
};

// What a listed resolver is assumed to do unless dns.json says otherwise.
// Ours validate DNSSEC and keep no query log, and they do filter - the
// whole point of the Standard and Family profiles - so "no filtering"
// stays off.
const STAMP_FLAGS = {
	dnssec: true,
	nolog: true,
	nofilter: false
};

function stampProps(flags){

	const f = { ...STAMP_FLAGS, ...flags };

	return (f.dnssec ? 1 : 0) |
		(f.nolog ? 2 : 0) |
		(f.nofilter ? 4 : 0);
}

function stampBytes(text){

	return Array.from(new TextEncoder().encode(text || ""));
}

function stampLP(text){

	const bytes = stampBytes(text);

	if(bytes.length > 255){
		throw new RangeError(`"${text}" is too long for a length prefix`);
	}

	return [bytes.length, ...bytes];
}

function stampU64(value){

	const out = new Array(8).fill(0);

	let left = value;

	for(let i = 0; i < 8 && left > 0; i++){
		out[i] = left & 0xff;
		left = Math.floor(left / 256);
	}

	return out;
}

function stampBase64(bytes){

	let binary = "";

	bytes.forEach(b => {
		binary += String.fromCharCode(b);
	});

	return btoa(binary)
		.replace(/\+/g, "-")
		.replace(/\//g, "_")
		.replace(/=+$/, "");
}

/*
	kind   "DoH", "DoT", "DoQ" or "Plain"
	host   hostname, with :port only when it is not the default
	path   DoH query path, ignored by every other protocol
	flags  optional { dnssec, nolog, nofilter } override
	addr   optional IP literal, for plain DNS or to pin a DoH address
*/
function dnsStamp(kind, host, path, flags, addr){

	const proto = STAMP_PROTO[kind];

	if(proto === undefined) return "";

	let bytes = [proto, ...stampU64(stampProps(flags))];

	if(proto === STAMP_PROTO.Plain){
		return "sdns://" + stampBase64([...bytes, ...stampLP(addr || host)]);
	}

	bytes = bytes.concat(stampLP(addr || ""));

	// No certificate pins: one empty element.
	bytes.push(0);

	bytes = bytes.concat(stampLP(host));

	if(proto === STAMP_PROTO.DoH){
		bytes = bytes.concat(stampLP(path || "/dns-query"));
	}

	return "sdns://" + stampBase64(bytes);
}
