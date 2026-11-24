#define FC_GO_DISPATCH_IMPLEMENTATION
#include "go_dispatch.h"
#include <pthread.h>
#include <stdlib.h>
extern void fcRestrictedRelease(uintptr_t owner);

static int dispatch(void *(*invoke)(void *), void *arguments) {
    pthread_t thread;
    if (pthread_create(&thread, NULL, invoke, arguments) != 0) return 0;
    if (pthread_join(thread, NULL) != 0) abort();
    return 1;
}

struct isolatedProvisionBeginArgs { struct provision_text locator; struct provision_text anchor; struct provision_text gateway; struct provision_text resolver; int64_t budget; uintptr_t owner; char ** report; int64_t result; };
static void *isolatedProvisionBeginInvoke(void *opaque) {
    struct isolatedProvisionBeginArgs *arguments = opaque;
    arguments->result = fcProvisionBegin(arguments->locator, arguments->anchor, arguments->gateway, arguments->resolver, arguments->budget, arguments->owner, arguments->report);
    return NULL;
}
int64_t isolatedProvisionBegin(struct provision_text locator, struct provision_text anchor, struct provision_text gateway, struct provision_text resolver, int64_t budget, uintptr_t owner, char ** report) {
    struct isolatedProvisionBeginArgs arguments = { .locator = locator, .anchor = anchor, .gateway = gateway, .resolver = resolver, .budget = budget, .owner = owner, .report = report };
    if (!dispatch(isolatedProvisionBeginInvoke, &arguments)) {
        fcRestrictedRelease(owner);
        return 0;
    }
    return arguments.result;
}

struct isolatedProvisionPostArgs { int64_t handle; struct provision_text path; struct provision_text body; struct provision_text request; char ** report; char * result; };
static void *isolatedProvisionPostInvoke(void *opaque) {
    struct isolatedProvisionPostArgs *arguments = opaque;
    arguments->result = fcProvisionPost(arguments->handle, arguments->path, arguments->body, arguments->request, arguments->report);
    return NULL;
}
char * isolatedProvisionPost(int64_t handle, struct provision_text path, struct provision_text body, struct provision_text request, char ** report) {
    struct isolatedProvisionPostArgs arguments = { .handle = handle, .path = path, .body = body, .request = request, .report = report };
    if (!dispatch(isolatedProvisionPostInvoke, &arguments)) {
        return NULL;
    }
    return arguments.result;
}

struct isolatedProvisionCloseArgs { int64_t handle; char * result; };
static void *isolatedProvisionCloseInvoke(void *opaque) {
    struct isolatedProvisionCloseArgs *arguments = opaque;
    arguments->result = fcProvisionClose(arguments->handle);
    return NULL;
}
char * isolatedProvisionClose(int64_t handle) {
    struct isolatedProvisionCloseArgs arguments = { .handle = handle };
    if (!dispatch(isolatedProvisionCloseInvoke, &arguments)) {
        return NULL;
    }
    return arguments.result;
}
#ifndef FC_PROVISION_ONLY

struct isolatedRestrictedBeginArgs { struct text directory; struct text control; struct text resolver; int64_t budget; uintptr_t owner; int64_t result; };
static void *isolatedRestrictedBeginInvoke(void *opaque) {
    struct isolatedRestrictedBeginArgs *arguments = opaque;
    arguments->result = fcRestrictedBegin(arguments->directory, arguments->control, arguments->resolver, arguments->budget, arguments->owner);
    return NULL;
}
int64_t isolatedRestrictedBegin(struct text directory, struct text control, struct text resolver, int64_t budget, uintptr_t owner) {
    struct isolatedRestrictedBeginArgs arguments = { .directory = directory, .control = control, .resolver = resolver, .budget = budget, .owner = owner };
    if (!dispatch(isolatedRestrictedBeginInvoke, &arguments)) {
        fcRestrictedRelease(owner);
        return 0;
    }
    return arguments.result;
}

struct isolatedRestrictedBeginReadyArgs { struct text response; struct text identity; struct text anchor; struct text resolver; int64_t budget; uintptr_t owner; int32_t speed; int64_t result; };
static void *isolatedRestrictedBeginReadyInvoke(void *opaque) {
    struct isolatedRestrictedBeginReadyArgs *arguments = opaque;
    arguments->result = fcRestrictedBeginReady(arguments->response, arguments->identity, arguments->anchor, arguments->resolver, arguments->budget, arguments->owner, arguments->speed);
    return NULL;
}
int64_t isolatedRestrictedBeginReady(struct text response, struct text identity, struct text anchor, struct text resolver, int64_t budget, uintptr_t owner, int32_t speed) {
    struct isolatedRestrictedBeginReadyArgs arguments = { .response = response, .identity = identity, .anchor = anchor, .resolver = resolver, .budget = budget, .owner = owner, .speed = speed };
    if (!dispatch(isolatedRestrictedBeginReadyInvoke, &arguments)) {
        fcRestrictedRelease(owner);
        return 0;
    }
    return arguments.result;
}

struct isolatedRestrictedTunArgs { int64_t handle; int32_t fd; int32_t result; };
static void *isolatedRestrictedTunInvoke(void *opaque) {
    struct isolatedRestrictedTunArgs *arguments = opaque;
    arguments->result = fcRestrictedTun(arguments->handle, arguments->fd);
    return NULL;
}
int32_t isolatedRestrictedTun(int64_t handle, int32_t fd) {
    struct isolatedRestrictedTunArgs arguments = { .handle = handle, .fd = fd };
    if (!dispatch(isolatedRestrictedTunInvoke, &arguments)) {
        return 0;
    }
    return arguments.result;
}

struct isolatedRestrictedStateArgs { int64_t handle; int32_t result; };
static void *isolatedRestrictedStateInvoke(void *opaque) {
    struct isolatedRestrictedStateArgs *arguments = opaque;
    arguments->result = fcRestrictedState(arguments->handle);
    return NULL;
}
int32_t isolatedRestrictedState(int64_t handle) {
    struct isolatedRestrictedStateArgs arguments = { .handle = handle };
    if (!dispatch(isolatedRestrictedStateInvoke, &arguments)) {
        return -1;
    }
    return arguments.result;
}

struct isolatedRestrictedStopArgs { int64_t handle; int32_t result; };
static void *isolatedRestrictedStopInvoke(void *opaque) {
    struct isolatedRestrictedStopArgs *arguments = opaque;
    arguments->result = fcRestrictedStop(arguments->handle);
    return NULL;
}
int32_t isolatedRestrictedStop(int64_t handle) {
    struct isolatedRestrictedStopArgs arguments = { .handle = handle };
    if (!dispatch(isolatedRestrictedStopInvoke, &arguments)) {
        return 0;
    }
    return arguments.result;
}

struct isolatedRestrictedStatsArgs { int64_t handle; char * result; };
struct isolatedRestrictedDnsArgs { int64_t handle; struct text query; int32_t millis; char *result; };
static void *isolatedRestrictedDnsInvoke(void *opaque) {
    struct isolatedRestrictedDnsArgs *arguments=opaque;
    arguments->result=fcRestrictedDns(arguments->handle,arguments->query,arguments->millis);
    return NULL;
}
char * isolatedRestrictedDns(int64_t handle,struct text query,int32_t millis) {
    struct isolatedRestrictedDnsArgs arguments={.handle=handle,.query=query,.millis=millis};
    if(!dispatch(isolatedRestrictedDnsInvoke,&arguments))return NULL;
    return arguments.result;
}
static void *isolatedRestrictedStatsInvoke(void *opaque) {
    struct isolatedRestrictedStatsArgs *arguments = opaque;
    arguments->result = fcRestrictedStats(arguments->handle);
    return NULL;
}
char * isolatedRestrictedStats(int64_t handle) {
    struct isolatedRestrictedStatsArgs arguments = { .handle = handle };
    if (!dispatch(isolatedRestrictedStatsInvoke, &arguments)) {
        return NULL;
    }
    return arguments.result;
}

struct isolatedRestrictedReadinessArgs { struct text directory; char * result; };
static void *isolatedRestrictedReadinessInvoke(void *opaque) {
    struct isolatedRestrictedReadinessArgs *arguments = opaque;
    arguments->result = fcRestrictedReadiness(arguments->directory);
    return NULL;
}
char * isolatedRestrictedReadiness(struct text directory) {
    struct isolatedRestrictedReadinessArgs arguments = { .directory = directory };
    if (!dispatch(isolatedRestrictedReadinessInvoke, &arguments)) {
        return NULL;
    }
    return arguments.result;
}

struct isolatedRestrictedValidateDeliveryArgs { struct text response; struct text identity; struct text anchor; int32_t result; };
static void *isolatedRestrictedValidateDeliveryInvoke(void *opaque) {
    struct isolatedRestrictedValidateDeliveryArgs *arguments = opaque;
    arguments->result = fcRestrictedValidateDelivery(arguments->response, arguments->identity, arguments->anchor);
    return NULL;
}
int32_t isolatedRestrictedValidateDelivery(struct text response, struct text identity, struct text anchor) {
    struct isolatedRestrictedValidateDeliveryArgs arguments = { .response = response, .identity = identity, .anchor = anchor };
    if (!dispatch(isolatedRestrictedValidateDeliveryInvoke, &arguments)) {
        return 0;
    }
    return arguments.result;
}

struct isolatedRestrictedValidationCodeArgs { struct text response; struct text identity; struct text anchor; int32_t result; };
static void *isolatedRestrictedValidationCodeInvoke(void *opaque) {
    struct isolatedRestrictedValidationCodeArgs *arguments = opaque;
    arguments->result = fcRestrictedValidationCode(arguments->response, arguments->identity, arguments->anchor);
    return NULL;
}
int32_t isolatedRestrictedValidationCode(struct text response, struct text identity, struct text anchor) {
    struct isolatedRestrictedValidationCodeArgs arguments = { .response = response, .identity = identity, .anchor = anchor };
    if (!dispatch(isolatedRestrictedValidationCodeInvoke, &arguments)) {
        return 1;
    }
    return arguments.result;
}

struct isolatedRestrictedRenewArgs { int64_t handle; struct text response; struct text identity; int32_t result; };
static void *isolatedRestrictedRenewInvoke(void *opaque) {
    struct isolatedRestrictedRenewArgs *arguments = opaque;
    arguments->result = fcRestrictedRenew(arguments->handle, arguments->response, arguments->identity);
    return NULL;
}
int32_t isolatedRestrictedRenew(int64_t handle, struct text response, struct text identity) {
    struct isolatedRestrictedRenewArgs arguments = { .handle = handle, .response = response, .identity = identity };
    if (!dispatch(isolatedRestrictedRenewInvoke, &arguments)) {
        return 0;
    }
    return arguments.result;
}

struct isolatedRestrictedFaultArgs { struct text command; char * result; };
static void *isolatedRestrictedFaultInvoke(void *opaque) {
    struct isolatedRestrictedFaultArgs *arguments = opaque;
    arguments->result = fcRestrictedFault(arguments->command);
    return NULL;
}
char * isolatedRestrictedFault(struct text command) {
    struct isolatedRestrictedFaultArgs arguments = { .command = command };
    if (!dispatch(isolatedRestrictedFaultInvoke, &arguments)) {
        return NULL;
    }
    return arguments.result;
}

struct isolatedChatAcquireArgs { struct chat_text response; struct chat_text identity; struct chat_text anchor; struct chat_text resolver; uintptr_t owner; int64_t result; };
static void *isolatedChatAcquireInvoke(void *opaque) {
    struct isolatedChatAcquireArgs *arguments = opaque;
    arguments->result = fcChatAcquire(arguments->response, arguments->identity, arguments->anchor, arguments->resolver, arguments->owner);
    return NULL;
}
int64_t isolatedChatAcquire(struct chat_text response, struct chat_text identity, struct chat_text anchor, struct chat_text resolver, uintptr_t owner) {
    struct isolatedChatAcquireArgs arguments = { .response = response, .identity = identity, .anchor = anchor, .resolver = resolver, .owner = owner };
    if (!dispatch(isolatedChatAcquireInvoke, &arguments)) {
        fcRestrictedRelease(owner);
        return 0;
    }
    return arguments.result;
}

struct isolatedChatStateArgs { int64_t handle; int32_t result; };
static void *isolatedChatStateInvoke(void *opaque) {
    struct isolatedChatStateArgs *arguments = opaque;
    arguments->result = fcChatState(arguments->handle);
    return NULL;
}
int32_t isolatedChatState(int64_t handle) {
    struct isolatedChatStateArgs arguments = { .handle = handle };
    if (!dispatch(isolatedChatStateInvoke, &arguments)) {
        return -1;
    }
    return arguments.result;
}

struct isolatedChatReleaseArgs { int64_t handle; };
static void *isolatedChatReleaseInvoke(void *opaque) {
    struct isolatedChatReleaseArgs *arguments = opaque;
    fcChatRelease(arguments->handle);
    return NULL;
}
void isolatedChatRelease(int64_t handle) {
    struct isolatedChatReleaseArgs arguments = { .handle = handle };
    dispatch(isolatedChatReleaseInvoke, &arguments);
}

struct isolatedChatOpenArgs { int64_t handle; int32_t timeout; int32_t result; };
static void *isolatedChatOpenInvoke(void *opaque) {
    struct isolatedChatOpenArgs *arguments = opaque;
    arguments->result = fcChatOpen(arguments->handle, arguments->timeout);
    return NULL;
}
int32_t isolatedChatOpen(int64_t handle, int32_t timeout) {
    struct isolatedChatOpenArgs arguments = { .handle = handle, .timeout = timeout };
    if (!dispatch(isolatedChatOpenInvoke, &arguments)) {
        return -1;
    }
    return arguments.result;
}

struct isolatedChatRequestArgs { int64_t handle; struct chat_text path; struct chat_text body; int32_t timeout; char * result; };
static void *isolatedChatRequestInvoke(void *opaque) {
    struct isolatedChatRequestArgs *arguments = opaque;
    arguments->result = fcChatRequest(arguments->handle, arguments->path, arguments->body, arguments->timeout);
    return NULL;
}
char * isolatedChatRequest(int64_t handle, struct chat_text path, struct chat_text body, int32_t timeout) {
    struct isolatedChatRequestArgs arguments = { .handle = handle, .path = path, .body = body, .timeout = timeout };
    if (!dispatch(isolatedChatRequestInvoke, &arguments)) {
        return NULL;
    }
    return arguments.result;
}
#endif
