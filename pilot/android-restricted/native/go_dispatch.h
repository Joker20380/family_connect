#ifndef FC_GO_DISPATCH_H
#define FC_GO_DISPATCH_H
#include <stdint.h>
struct text { const char *str; long size; };
struct provision_text { const char *ptr; long len; };
struct chat_text { const char *ptr; long len; };
int64_t fcProvisionBegin(struct provision_text locator, struct provision_text anchor, struct provision_text gateway, struct provision_text resolver, int64_t budget, uintptr_t owner, char ** report);
int64_t isolatedProvisionBegin(struct provision_text locator, struct provision_text anchor, struct provision_text gateway, struct provision_text resolver, int64_t budget, uintptr_t owner, char ** report);
#ifndef FC_GO_DISPATCH_IMPLEMENTATION
#define fcProvisionBegin isolatedProvisionBegin
#endif
char * fcProvisionPost(int64_t handle, struct provision_text path, struct provision_text body, struct provision_text request, char ** report);
char * isolatedProvisionPost(int64_t handle, struct provision_text path, struct provision_text body, struct provision_text request, char ** report);
#ifndef FC_GO_DISPATCH_IMPLEMENTATION
#define fcProvisionPost isolatedProvisionPost
#endif
char * fcProvisionClose(int64_t handle);
char * isolatedProvisionClose(int64_t handle);
#ifndef FC_GO_DISPATCH_IMPLEMENTATION
#define fcProvisionClose isolatedProvisionClose
#endif
#ifndef FC_PROVISION_ONLY
int64_t fcRestrictedBegin(struct text directory, struct text control, struct text resolver, int64_t budget, uintptr_t owner);
int64_t isolatedRestrictedBegin(struct text directory, struct text control, struct text resolver, int64_t budget, uintptr_t owner);
#ifndef FC_GO_DISPATCH_IMPLEMENTATION
#define fcRestrictedBegin isolatedRestrictedBegin
#endif
int64_t fcRestrictedBeginReady(struct text response, struct text identity, struct text anchor, struct text resolver, int64_t budget, uintptr_t owner, int32_t speed);
int64_t isolatedRestrictedBeginReady(struct text response, struct text identity, struct text anchor, struct text resolver, int64_t budget, uintptr_t owner, int32_t speed);
#ifndef FC_GO_DISPATCH_IMPLEMENTATION
#define fcRestrictedBeginReady isolatedRestrictedBeginReady
#endif
int32_t fcRestrictedTun(int64_t handle, int32_t fd);
int32_t isolatedRestrictedTun(int64_t handle, int32_t fd);
#ifndef FC_GO_DISPATCH_IMPLEMENTATION
#define fcRestrictedTun isolatedRestrictedTun
#endif
int32_t fcRestrictedState(int64_t handle);
int32_t isolatedRestrictedState(int64_t handle);
#ifndef FC_GO_DISPATCH_IMPLEMENTATION
#define fcRestrictedState isolatedRestrictedState
#endif
int32_t fcRestrictedStop(int64_t handle);
int32_t isolatedRestrictedStop(int64_t handle);
#ifndef FC_GO_DISPATCH_IMPLEMENTATION
#define fcRestrictedStop isolatedRestrictedStop
#endif
char * fcRestrictedStats(int64_t handle);
char * fcRestrictedDns(int64_t handle,struct text query,int32_t millis);
char * isolatedRestrictedDns(int64_t handle,struct text query,int32_t millis);
#ifndef FC_GO_DISPATCH_IMPLEMENTATION
#define fcRestrictedDns isolatedRestrictedDns
#endif
char * isolatedRestrictedStats(int64_t handle);
#ifndef FC_GO_DISPATCH_IMPLEMENTATION
#define fcRestrictedStats isolatedRestrictedStats
#endif
char * fcRestrictedReadiness(struct text directory);
char * isolatedRestrictedReadiness(struct text directory);
#ifndef FC_GO_DISPATCH_IMPLEMENTATION
#define fcRestrictedReadiness isolatedRestrictedReadiness
#endif
int32_t fcRestrictedValidateDelivery(struct text response, struct text identity, struct text anchor);
int32_t isolatedRestrictedValidateDelivery(struct text response, struct text identity, struct text anchor);
#ifndef FC_GO_DISPATCH_IMPLEMENTATION
#define fcRestrictedValidateDelivery isolatedRestrictedValidateDelivery
#endif
int32_t fcRestrictedValidationCode(struct text response, struct text identity, struct text anchor);
int32_t isolatedRestrictedValidationCode(struct text response, struct text identity, struct text anchor);
#ifndef FC_GO_DISPATCH_IMPLEMENTATION
#define fcRestrictedValidationCode isolatedRestrictedValidationCode
#endif
int32_t fcRestrictedRenew(int64_t handle, struct text response, struct text identity);
int32_t isolatedRestrictedRenew(int64_t handle, struct text response, struct text identity);
#ifndef FC_GO_DISPATCH_IMPLEMENTATION
#define fcRestrictedRenew isolatedRestrictedRenew
#endif
char * fcRestrictedFault(struct text command);
char * isolatedRestrictedFault(struct text command);
#ifndef FC_GO_DISPATCH_IMPLEMENTATION
#define fcRestrictedFault isolatedRestrictedFault
#endif
int64_t fcChatAcquire(struct chat_text response, struct chat_text identity, struct chat_text anchor, struct chat_text resolver, uintptr_t owner);
int64_t isolatedChatAcquire(struct chat_text response, struct chat_text identity, struct chat_text anchor, struct chat_text resolver, uintptr_t owner);
#ifndef FC_GO_DISPATCH_IMPLEMENTATION
#define fcChatAcquire isolatedChatAcquire
#endif
int32_t fcChatState(int64_t handle);
int32_t isolatedChatState(int64_t handle);
#ifndef FC_GO_DISPATCH_IMPLEMENTATION
#define fcChatState isolatedChatState
#endif
void fcChatRelease(int64_t handle);
void isolatedChatRelease(int64_t handle);
#ifndef FC_GO_DISPATCH_IMPLEMENTATION
#define fcChatRelease isolatedChatRelease
#endif
int32_t fcChatOpen(int64_t handle, int32_t timeout);
int32_t isolatedChatOpen(int64_t handle, int32_t timeout);
#ifndef FC_GO_DISPATCH_IMPLEMENTATION
#define fcChatOpen isolatedChatOpen
#endif
char * fcChatRequest(int64_t handle, struct chat_text path, struct chat_text body, int32_t timeout);
char * isolatedChatRequest(int64_t handle, struct chat_text path, struct chat_text body, int32_t timeout);
#ifndef FC_GO_DISPATCH_IMPLEMENTATION
#define fcChatRequest isolatedChatRequest
#endif
#endif
#endif
