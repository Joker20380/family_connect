#include <jni.h>
#include <stdint.h>
#include <stdlib.h>

struct provision_text { const char *ptr; long len; };
extern int64_t fcProvisionBegin(struct provision_text,struct provision_text,struct provision_text,struct provision_text,int64_t,uintptr_t);
extern char *fcProvisionPost(int64_t,struct provision_text,struct provision_text,struct provision_text);
extern void fcProvisionClose(int64_t);

JNIEXPORT jlong JNICALL Java_com_familyconnect_app_NativeRestricted_provisionBegin(JNIEnv *env,jclass cls,jbyteArray locator,jbyteArray anchor,jstring gateway,jstring resolver,jlong budget,jobject protector){
 if(!locator||!anchor||!gateway||!resolver||!protector)return 0;
 jbyte *raw=(*env)->GetByteArrayElements(env,locator,NULL),*root=(*env)->GetByteArrayElements(env,anchor,NULL);
 const char *target=(*env)->GetStringUTFChars(env,gateway,NULL),*dns=(*env)->GetStringUTFChars(env,resolver,NULL);int64_t result=0;
 if(raw&&root&&target&&dns){jobject owner=(*env)->NewGlobalRef(env,protector);if(owner)result=fcProvisionBegin((struct provision_text){(char*)raw,(*env)->GetArrayLength(env,locator)},(struct provision_text){(char*)root,(*env)->GetArrayLength(env,anchor)},(struct provision_text){target,(*env)->GetStringUTFLength(env,gateway)},(struct provision_text){dns,(*env)->GetStringUTFLength(env,resolver)},budget,(uintptr_t)owner);}
 if(raw)(*env)->ReleaseByteArrayElements(env,locator,raw,JNI_ABORT);
 if(root)(*env)->ReleaseByteArrayElements(env,anchor,root,JNI_ABORT);
 if(target)(*env)->ReleaseStringUTFChars(env,gateway,target);
 if(dns)(*env)->ReleaseStringUTFChars(env,resolver,dns);
 return result;
}
JNIEXPORT jstring JNICALL Java_com_familyconnect_app_NativeRestricted_provisionPost(JNIEnv *env,jclass cls,jlong handle,jstring path,jstring body,jstring requestId){
 if(!path||!body||!requestId)return NULL;
 const char *route=(*env)->GetStringUTFChars(env,path,NULL),*payload=(*env)->GetStringUTFChars(env,body,NULL),*request=(*env)->GetStringUTFChars(env,requestId,NULL);
 char *raw=NULL;
 if(route&&payload&&request)raw=fcProvisionPost(handle,(struct provision_text){route,(*env)->GetStringUTFLength(env,path)},(struct provision_text){payload,(*env)->GetStringUTFLength(env,body)},(struct provision_text){request,(*env)->GetStringUTFLength(env,requestId)});
 if(route)(*env)->ReleaseStringUTFChars(env,path,route);
 if(payload)(*env)->ReleaseStringUTFChars(env,body,payload);
 if(request)(*env)->ReleaseStringUTFChars(env,requestId,request);
 if(!raw)return NULL;
 jstring result=(*env)->NewStringUTF(env,raw);free(raw);return result;
}
JNIEXPORT void JNICALL Java_com_familyconnect_app_NativeRestricted_provisionClose(JNIEnv *env,jclass cls,jlong handle){fcProvisionClose(handle);}
