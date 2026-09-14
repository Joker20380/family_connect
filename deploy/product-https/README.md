# Family Connect product HTTPS pilot

TLS front end for the existing `127.0.0.1:18082` API on the authorized original
gateway. TCP/443 remains assigned to the VPN TCP transport; this front end uses
TCP/8443. TCP/80 serves only ACME challenges, never the enrollment API.

Render `@IP@` as `185.251.89.19`. Use an isolated nginx container with host
networking, the rendered config directory read-only at `/etc/fc`, the private
certificate directory read-only at `/etc/letsencrypt`, and the ACME webroot
read-only at `/var/www/acme`. Start nginx with `-c /etc/fc/nginx.conf`; mounting
the directory permits atomic config replacement before reload. Pin downloaded
container image digests in the deployment receipt.

The proxy accepts only the four existing public POST routes. It bounds request
size, header/body/upstream timeouts, per-IP/global request and connection counts.
Query strings are refused; access/body logging is disabled. It exposes no admin
routes, health/debug endpoints, redirects or CORS policy. Invitation tokens stay
in POST bodies. Existing API authentication, binding and single-use checks remain
mandatory behind the proxy.

IP certificates require Certbot >=5.4 for webroot and the `shortlived` ACME
profile. Validate with a staging certificate first, then request the production
certificate. Keep certificate/account keys, renewal config and logs under the
private ignored server state, outside Git/CI. Run automatic renewal at least
twice daily; validate nginx and reload only after successful renewal. Record
renewal dry-run and certificate expiry before calling this a deployed endpoint.

[Official Certbot IP certificate instructions](https://letsencrypt.org/2026/03/11/shorter-certs-certbot).

Rollback: stop only the new Family Connect HTTPS container and renewal timer.
Retain certificate state for reactivation; leave the localhost API, DB, peers,
TCP/443 transport, Amsterdam relay and existing gateway services intact.

This template is preparation, not evidence of deployment or Android HTTPS
registration. Use the dated release report for actual rollout and tests.
