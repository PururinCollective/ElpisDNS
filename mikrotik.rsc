/ip dns forwarders
add doh-servers="https://b.hitoha.moe/dns-query,https://gg.hitoha.moe/dns-query" name=AdGuard

/ip dns static
add address=151.158.198.53 name=b.hitoha.moe type=A
add address=103.131.188.71 name=gg.hitoha.moe type=A
add name=* forward-to=AdGuard type=FWD

/ip dns
set servers=1.0.0.1,1.1.1.1 allow-remote-requests=yes cache-size=65536KiB doh-max-concurrent-queries=2000 doh-max-server-connections=100 max-concurrent-queries=500 max-concurrent-tcp-sessions=100
