#define FC_GO_DISPATCH_IMPLEMENTATION
#include "go_dispatch.h"
#include <assert.h>
#include <errno.h>
#include <pthread.h>
#include <stdatomic.h>
#include <stdlib.h>
#include <string.h>

static _Thread_local int runtime_slot;
static atomic_int entered, closed, fail_create, released;
static void entered_go(void) { assert(runtime_slot == 0); runtime_slot = 2; atomic_fetch_add(&entered, 1); }
int __real_pthread_create(pthread_t *, const pthread_attr_t *, void *(*)(void *), void *);
int __wrap_pthread_create(pthread_t *thread, const pthread_attr_t *attr, void *(*invoke)(void *), void *argument) {
    if (atomic_load(&fail_create)) return EAGAIN;
    return __real_pthread_create(thread, attr, invoke, argument);
}
void fcRestrictedRelease(uintptr_t owner) { assert(owner == 99); atomic_fetch_add(&released, 1); }
int64_t fcProvisionBegin(struct provision_text locator, struct provision_text anchor, struct provision_text gateway, struct provision_text resolver, int64_t budget, uintptr_t owner, char **report) {
    entered_go();
    assert(locator.len == 3 && memcmp(locator.ptr, "abc", 3) == 0);
    assert(anchor.len == 4 && gateway.len == 5 && resolver.len == 6 && budget == 3000 && owner == 99);
    *report = "LOCATOR";
    return 71;
}
char *fcProvisionPost(int64_t handle, struct provision_text path, struct provision_text body, struct provision_text request, char **report) {
    entered_go(); assert(handle == 71 && path.len == 1 && body.len == 2 && request.len == 3);
    while (!atomic_load(&closed)) {}
    *report = "CANCELLED";
    return NULL;
}
char *fcProvisionClose(int64_t handle) { entered_go(); assert(handle == 71); atomic_store(&closed, 1); return "CLOSED"; }
#define NUMERIC_STUB(name, parameters, check) int32_t name parameters { entered_go(); assert(check); return -1; }
#define TEXT_STUB(name, parameters, check) char *name parameters { entered_go(); assert(check); return NULL; }
int64_t fcRestrictedBegin(struct text directory, struct text control, struct text resolver, int64_t budget, uintptr_t owner) { entered_go(); assert(directory.size == 0 && control.size == 0 && resolver.size == 0 && budget == 3000 && owner == 99); return 0; }
int64_t fcRestrictedBeginReady(struct text response, struct text identity, struct text anchor, struct text resolver, int64_t budget, uintptr_t owner, int32_t speed) { entered_go(); assert(response.size == 0 && identity.size == 0 && anchor.size == 0 && resolver.size == 0 && budget == 3000 && owner == 99 && speed == 0); return 0; }
NUMERIC_STUB(fcRestrictedTun, (int64_t handle, int32_t fd), handle == -1 && fd == -1)
NUMERIC_STUB(fcRestrictedState, (int64_t handle), handle == -1)
NUMERIC_STUB(fcRestrictedStop, (int64_t handle), handle == -1)
TEXT_STUB(fcRestrictedStats, (int64_t handle), handle == -1)
TEXT_STUB(fcRestrictedReadiness, (struct text directory), directory.size == 0)
NUMERIC_STUB(fcRestrictedValidateDelivery, (struct text response, struct text identity, struct text anchor), response.size == 0 && identity.size == 0 && anchor.size == 0)
NUMERIC_STUB(fcRestrictedValidationCode, (struct text response, struct text identity, struct text anchor), response.size == 0 && identity.size == 0 && anchor.size == 0)
NUMERIC_STUB(fcRestrictedRenew, (int64_t handle, struct text response, struct text identity), handle == -1 && response.size == 0 && identity.size == 0)
TEXT_STUB(fcRestrictedFault, (struct text command), command.size == 0)
int64_t fcChatAcquire(struct chat_text response, struct chat_text identity, struct chat_text anchor, struct chat_text resolver, uintptr_t owner) { entered_go(); assert(response.len == 0 && identity.len == 0 && anchor.len == 0 && resolver.len == 0 && owner == 99); return 0; }
NUMERIC_STUB(fcChatState, (int64_t handle), handle == -1)
void fcChatRelease(int64_t handle) { entered_go(); assert(handle == -1); }
NUMERIC_STUB(fcChatOpen, (int64_t handle, int32_t timeout), handle == -1 && timeout == 1000)
TEXT_STUB(fcChatRequest, (int64_t handle, struct chat_text path, struct chat_text body, int32_t timeout), handle == -1 && path.len == 0 && body.len == 0 && timeout == 1000)

static void *post(void *unused) {
    assert(unused == NULL);
    char *report = NULL;
    runtime_slot = 1;
    assert(isolatedProvisionPost(71, (struct provision_text){"a",1}, (struct provision_text){"ab",2}, (struct provision_text){"abc",3}, &report) == NULL);
    assert(strcmp(report, "CANCELLED") == 0 && runtime_slot == 1);
    return NULL;
}
int main(void) {
    runtime_slot = 1;
    struct provision_text locator = {"abc",3}, anchor = {"root",4}, gateway = {"node1",5}, resolver = {"dns:53",6};
    struct text empty = {NULL,0};
    struct chat_text chat = {NULL,0};
    char *report = NULL;
    assert(isolatedProvisionBegin(locator,anchor,gateway,resolver,3000,99,&report) == 71);
    assert(strcmp(report,"LOCATOR") == 0 && runtime_slot == 1);
    pthread_t posting;
    assert(pthread_create(&posting, NULL, post, NULL) == 0);
    while (atomic_load(&entered) < 2) {}
    assert(strcmp(isolatedProvisionClose(71), "CLOSED") == 0);
    assert(pthread_join(posting, NULL) == 0);
    isolatedRestrictedBegin(empty,empty,empty,3000,99);
    isolatedRestrictedBeginReady(empty,empty,empty,empty,3000,99,0);
    isolatedRestrictedTun(-1,-1); isolatedRestrictedState(-1); isolatedRestrictedStop(-1);
    isolatedRestrictedStats(-1); isolatedRestrictedReadiness(empty);
    isolatedRestrictedValidateDelivery(empty,empty,empty); isolatedRestrictedValidationCode(empty,empty,empty);
    isolatedRestrictedRenew(-1,empty,empty); isolatedRestrictedFault(empty);
    isolatedChatAcquire(chat,chat,chat,chat,99); isolatedChatState(-1); isolatedChatRelease(-1);
    isolatedChatOpen(-1,1000); isolatedChatRequest(-1,chat,chat,1000);
    assert(atomic_load(&entered) == 19 && runtime_slot == 1);
    atomic_store(&fail_create,1);
    report = NULL;
    assert(isolatedProvisionBegin(locator,anchor,gateway,resolver,3000,99,&report) == 0);
    assert(report == NULL && atomic_load(&released) == 1);
    assert(isolatedRestrictedBegin(empty,empty,empty,3000,99) == 0);
    assert(isolatedRestrictedBeginReady(empty,empty,empty,empty,3000,99,0) == 0);
    assert(isolatedChatAcquire(chat,chat,chat,chat,99) == 0);
    assert(atomic_load(&released) == 4 && atomic_load(&entered) == 19);
    assert(isolatedRestrictedValidationCode(empty,empty,empty) == 1);
    assert(isolatedRestrictedValidateDelivery(empty,empty,empty) == 0);
    assert(isolatedRestrictedState(-1) == -1 && isolatedChatState(-1) == -1);
    assert(isolatedChatOpen(-1,1000) == -1 && runtime_slot == 1);
    return 0;
}
