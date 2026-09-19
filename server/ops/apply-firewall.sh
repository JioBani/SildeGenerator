#!/bin/sh
# Run manually on mini as root after reviewing. Only SlideGenerator bridges are affected.
set -eu
[ "$(id -u)" = 0 ] || { echo 'Run with sudo'; exit 1; }
iptables -w -nL DOCKER-USER >/dev/null 2>&1 || { echo 'Docker iptables backend required; do not apply to nftables backend.'; exit 1; }
for chain in SG-FORWARD SG-HOST; do iptables -w -N "$chain" 2>/dev/null || true; iptables -w -F "$chain"; done
# Allow replies to connections initiated by the host; forbid containers initiating host access.
iptables -w -A SG-HOST -m conntrack --ctstate ESTABLISHED,RELATED -j RETURN
iptables -w -A SG-HOST -i sg-ingress -j DROP
iptables -w -A SG-HOST -i sg-backend -j DROP
iptables -w -A SG-HOST -i sg-egress -j DROP
iptables -w -A SG-HOST -j RETURN
iptables -w -C INPUT -j SG-HOST 2>/dev/null || iptables -w -I INPUT 1 -j SG-HOST
# Queue traffic only on the internal bridge; established replies stay permitted.
iptables -w -A SG-FORWARD -i sg-backend -o sg-backend -p tcp --dport 6379 -j RETURN
iptables -w -A SG-FORWARD -i sg-backend -m conntrack --ctstate ESTABLISHED,RELATED -j RETURN
iptables -w -A SG-FORWARD -i sg-backend -j DROP
iptables -w -A SG-FORWARD -i sg-ingress -m conntrack --ctstate ESTABLISHED,RELATED -j RETURN
iptables -w -A SG-FORWARD -i sg-ingress -j DROP
for cidr in 0.0.0.0/8 10.0.0.0/8 100.64.0.0/10 127.0.0.0/8 169.254.0.0/16 172.16.0.0/12 192.0.0.0/24 192.168.0.0/16 198.18.0.0/15 224.0.0.0/4 240.0.0.0/4; do
  iptables -w -A SG-FORWARD -i sg-egress -d "$cidr" -j DROP
done
iptables -w -A SG-FORWARD -i sg-egress -p tcp --dport 443 -j RETURN
iptables -w -A SG-FORWARD -i sg-egress -p udp --dport 53 -j RETURN
iptables -w -A SG-FORWARD -i sg-egress -p tcp --dport 53 -j RETURN
iptables -w -A SG-FORWARD -i sg-egress -j DROP
iptables -w -A SG-FORWARD -j RETURN
iptables -w -C DOCKER-USER -j SG-FORWARD 2>/dev/null || iptables -w -I DOCKER-USER 1 -j SG-FORWARD
# No IPv6 egress is part of this deployment. Prevent accidental future enablement bypassing IPv4 rules.
for chain in SG6-FORWARD SG6-HOST; do ip6tables -w -N "$chain" 2>/dev/null || true; ip6tables -w -F "$chain"; done
ip6tables -w -A SG6-HOST -m conntrack --ctstate ESTABLISHED,RELATED -j RETURN
for bridge in sg-backend sg-egress sg-ingress; do
  ip6tables -w -A SG6-HOST -i "$bridge" -j DROP
  ip6tables -w -A SG6-FORWARD -i "$bridge" -j DROP
done
ip6tables -w -A SG6-HOST -j RETURN
ip6tables -w -A SG6-FORWARD -j RETURN
ip6tables -w -C INPUT -j SG6-HOST 2>/dev/null || ip6tables -w -I INPUT 1 -j SG6-HOST
ip6tables -w -C FORWARD -j SG6-FORWARD 2>/dev/null || ip6tables -w -I FORWARD 1 -j SG6-FORWARD
printf 'SlideGenerator rules installed. Run ops/verify-security.py and persist rules with the supplied systemd unit.\n'
