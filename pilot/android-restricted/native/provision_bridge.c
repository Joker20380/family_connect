#include <jni.h>
#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include <time.h>

#include "go_dispatch.h"

static void diagnostic(JNIEnv *env,jobjectArray output,const char *raw){
 if(!output||(*env)->ExceptionCheck(env)||(*env)->GetArrayLength(env,output)!=1)return;
 jstring value=(*env)->NewStringUTF(env,raw);
 if(value){(*env)->SetObjectArrayElement(env,output,0,value);(*env)->DeleteLocalRef(env,value);}
}
static int64_t monotonicMillis(void){struct timespec now;clock_gettime(CLOCK_MONOTONIC,&now);return (int64_t)now.tv_sec*1000+now.tv_nsec/1000000;}
static void jniFailure(JNIEnv *env,jobjectArray output,const char *stage,const char *reason,int64_t started,int64_t budget){
 char raw[384];int64_t elapsed=monotonicMillis()-started,remaining=budget>elapsed?budget-elapsed:0;
 snprintf(raw,sizeof(raw),"{\"go_entered\":false,\"first_failure\":\"%s\",\"reason\":\"%s\",\"elapsed_ms\":%lld,\"remaining_ms\":%lld,\"budget_known\":%s}",stage,reason,(long long)elapsed,(long long)remaining,budget>=0?"true":"false");
 diagnostic(env,output,raw);
}

JNIEXPORT jlong JNICALL Java_com_familyconnect_app_NativeRestricted_provisionBegin(JNIEnv *env,jclass cls,jbyteArray locator,jbyteArray anchor,jstring gateway,jstring resolver,jlong budget,jobject protector,jobjectArray output){
 int64_t started=monotonicMillis();
 jniFailure(env,output,"JNI_ARGUMENTS","REJECTED",started,budget);
 if(!locator||!anchor||!gateway||!resolver||!protector||!output||(*env)->GetArrayLength(env,output)!=1)return 0;
 jniFailure(env,output,"JNI_MARSHAL","JNI_RESOURCE",started,budget);
 jbyte *raw=NULL,*root=NULL;const char *target=NULL,*dns=NULL;int64_t result=0;char *report=NULL;
 raw=(*env)->GetByteArrayElements(env,locator,NULL);if(!raw)goto cleanup_begin;
 root=(*env)->GetByteArrayElements(env,anchor,NULL);if(!root)goto cleanup_begin;
 target=(*env)->GetStringUTFChars(env,gateway,NULL);if(!target)goto cleanup_begin;
 dns=(*env)->GetStringUTFChars(env,resolver,NULL);if(!dns)goto cleanup_begin;
 if(raw&&root&&target&&dns&&!(*env)->ExceptionCheck(env)){jobject owner=(*env)->NewGlobalRef(env,protector);if(owner)result=fcProvisionBegin((struct provision_text){(char*)raw,(*env)->GetArrayLength(env,locator)},(struct provision_text){(char*)root,(*env)->GetArrayLength(env,anchor)},(struct provision_text){target,(*env)->GetStringUTFLength(env,gateway)},(struct provision_text){dns,(*env)->GetStringUTFLength(env,resolver)},budget,(uintptr_t)owner,&report);}
 cleanup_begin:
 if(raw)(*env)->ReleaseByteArrayElements(env,locator,raw,JNI_ABORT);
 if(root)(*env)->ReleaseByteArrayElements(env,anchor,root,JNI_ABORT);
 if(target)(*env)->ReleaseStringUTFChars(env,gateway,target);
 if(dns)(*env)->ReleaseStringUTFChars(env,resolver,dns);
 if(report){diagnostic(env,output,report);free(report);}
 return result;
}
JNIEXPORT jstring JNICALL Java_com_familyconnect_app_NativeRestricted_provisionPost(JNIEnv *env,jclass cls,jlong handle,jstring path,jstring body,jstring requestId,jobjectArray output){
 int64_t started=monotonicMillis();
 jniFailure(env,output,"JNI_ARGUMENTS","REJECTED",started,-1);
 if(!path||!body||!requestId||!output||(*env)->GetArrayLength(env,output)!=1)return NULL;
 jniFailure(env,output,"JNI_MARSHAL","JNI_RESOURCE",started,-1);
 const char *route=NULL,*payload=NULL,*request=NULL;
 char *raw=NULL,*report=NULL;
 route=(*env)->GetStringUTFChars(env,path,NULL);if(!route)goto cleanup_post;
 payload=(*env)->GetStringUTFChars(env,body,NULL);if(!payload)goto cleanup_post;
 request=(*env)->GetStringUTFChars(env,requestId,NULL);if(!request)goto cleanup_post;
 if(route&&payload&&request&&!(*env)->ExceptionCheck(env))raw=fcProvisionPost(handle,(struct provision_text){route,(*env)->GetStringUTFLength(env,path)},(struct provision_text){payload,(*env)->GetStringUTFLength(env,body)},(struct provision_text){request,(*env)->GetStringUTFLength(env,requestId)},&report);
 cleanup_post:
 if(route)(*env)->ReleaseStringUTFChars(env,path,route);
 if(payload)(*env)->ReleaseStringUTFChars(env,body,payload);
 if(request)(*env)->ReleaseStringUTFChars(env,requestId,request);
 if(report){diagnostic(env,output,report);free(report);}
 if(!raw)return NULL;
 jstring result=(*env)->NewStringUTF(env,raw);free(raw);return result;
}
JNIEXPORT jstring JNICALL Java_com_familyconnect_app_NativeRestricted_provisionClose(JNIEnv *env,jclass cls,jlong handle){char *raw=fcProvisionClose(handle);if(!raw)return NULL;jstring result=(*env)->NewStringUTF(env,raw);free(raw);return result;}
