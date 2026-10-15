//go:build (linux || android) && cgo

#include <netdb.h>
#include <stdatomic.h>

static atomic_int fc_dns_denied = 0;
static atomic_ulong fc_dns_calls = 0;

int __real_getaddrinfo(const char *, const char *, const struct addrinfo *, struct addrinfo **);

int __wrap_getaddrinfo(const char *node, const char *service, const struct addrinfo *hints, struct addrinfo **result) {
    if (atomic_load(&fc_dns_denied)) {
        atomic_fetch_add(&fc_dns_calls, 1);
        *result = 0;
        return EAI_AGAIN;
    }
    return __real_getaddrinfo(node, service, hints, result);
}

void fc_deny_dns(void) { atomic_store(&fc_dns_denied, 1); }
void fc_reset_dns_count(void) { atomic_store(&fc_dns_calls, 0); }
unsigned long fc_dns_count(void) { return atomic_load(&fc_dns_calls); }
