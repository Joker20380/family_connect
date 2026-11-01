"""Render validated symbolic infrastructure templates without executing them."""

import ipaddress
from pathlib import Path
import re

from .contracts import ROLES, exact, fail


def templates(role, network):
    if role not in ROLES:
        fail('template_role')
    exact(network, ('interface', 'uplink', 'subnet'))
    if any(not re.fullmatch(r'[a-zA-Z][a-zA-Z0-9_-]{0,14}', network[key]) for key in ('interface','uplink')):
        fail('template_interface')
    try:
        subnet = ipaddress.IPv4Network(network['subnet'],strict=True)
    except ValueError:
        fail('template_subnet')
    if not subnet.is_private or subnet.prefixlen<16 or network['interface']==network['uplink']:
        fail('template_network')
    root = Path(__file__).with_name('templates')
    service = (root/'family-connect-role.service.in').read_text().replace('@ROLE@',role)
    firewall = (root/'firewall.nft.in').read_text()
    for key in ('interface','uplink','subnet'):
        firewall = firewall.replace('@'+key.upper()+'@',network[key])
    return {'systemd/family-connect-'+role+'.service':service.encode(), 'firewall/instance.nft':firewall.encode(),
            'sysctl/forwarding.conf':(root/'forwarding.conf').read_bytes(),
            'schemas/configuration.json':(root/'configuration.schema.json').read_bytes()}
