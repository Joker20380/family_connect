#include <jni.h>
#include <stdint.h>
#include <stdlib.h>

struct chat_text { const char *ptr; long len; };
extern int64_t fcChatAcquire(struct chat_text,struct chat_text,struct chat_text,struct chat_text,uintptr_t);
extern int32_t fcChatState(int64_t);
extern void fcChatRelease(int64_t);
extern int32_t fcChatOpen(int64_t,int32_t);
extern char *fcChatRequest(int64_t,struct chat_text,struct chat_text,int32_t);

JNIEXPORT jlong JNICALL Java_com_familyconnect_app_NativeRestricted_chatAcquire(JNIEnv *env,jclass cls,jbyteArray response,jbyteArray identity,jbyteArray anchor,jstring resolver,jobject protector){
 if(!response||!identity||!anchor||!resolver||!protector)return 0;
 jbyte *raw=(*env)->GetByteArrayElements(env,response,NULL),*secret=(*env)->GetByteArrayElements(env,identity,NULL),*root=(*env)->GetByteArrayElements(env,anchor,NULL);
 const char *dns=(*env)->GetStringUTFChars(env,resolver,NULL);int64_t result=0;
 if(raw&&secret&&root&&dns){jobject owner=(*env)->NewGlobalRef(env,protector);if(owner)result=fcChatAcquire((struct chat_text){(char*)raw,(*env)->GetArrayLength(env,response)},(struct chat_text){(char*)secret,(*env)->GetArrayLength(env,identity)},(struct chat_text){(char*)root,(*env)->GetArrayLength(env,anchor)},(struct chat_text){dns,(*env)->GetStringUTFLength(env,resolver)},(uintptr_t)owner);}
 if(secret){volatile jbyte *wipe=secret;for(jsize index=0;index<(*env)->GetArrayLength(env,identity);index++)wipe[index]=0;}
 if(raw)(*env)->ReleaseByteArrayElements(env,response,raw,JNI_ABORT);
 if(secret)(*env)->ReleaseByteArrayElements(env,identity,secret,JNI_ABORT);
 if(root)(*env)->ReleaseByteArrayElements(env,anchor,root,JNI_ABORT);
 if(dns)(*env)->ReleaseStringUTFChars(env,resolver,dns);
 return result;
}
JNIEXPORT jint JNICALL Java_com_familyconnect_app_NativeRestricted_chatState(JNIEnv *env,jclass cls,jlong handle){return fcChatState(handle);}
JNIEXPORT void JNICALL Java_com_familyconnect_app_NativeRestricted_chatRelease(JNIEnv *env,jclass cls,jlong handle){fcChatRelease(handle);}
JNIEXPORT jint JNICALL Java_com_familyconnect_app_NativeRestricted_chatOpen(JNIEnv *env,jclass cls,jlong handle,jint timeout){return fcChatOpen(handle,timeout);}
JNIEXPORT jstring JNICALL Java_com_familyconnect_app_NativeRestricted_chatRequest(JNIEnv *env,jclass cls,jlong handle,jstring path,jstring body,jint timeout){
 if(!path||!body)return NULL;
 const char *route=(*env)->GetStringUTFChars(env,path,NULL),*payload=(*env)->GetStringUTFChars(env,body,NULL);
 char *raw=NULL;
 if(route&&payload)raw=fcChatRequest(handle,(struct chat_text){route,(*env)->GetStringUTFLength(env,path)},(struct chat_text){payload,(*env)->GetStringUTFLength(env,body)},timeout);
 if(route)(*env)->ReleaseStringUTFChars(env,path,route);
 if(payload)(*env)->ReleaseStringUTFChars(env,body,payload);
 if(!raw)return NULL;
 jstring result=(*env)->NewStringUTF(env,raw);free(raw);return result;
}
