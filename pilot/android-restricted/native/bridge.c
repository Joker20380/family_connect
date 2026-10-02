#include <jni.h>
#include <stdint.h>
#include <stdlib.h>
static JavaVM *vm;
JNIEXPORT jint JNICALL JNI_OnLoad(JavaVM *value,void *reserved){vm=value;return JNI_VERSION_1_6;}
static JNIEnv *environment(int *attached){JNIEnv *env=NULL;*attached=0;if((*vm)->GetEnv(vm,(void **)&env,JNI_VERSION_1_6)!=JNI_OK){if((*vm)->AttachCurrentThread(vm,&env,NULL)!=JNI_OK)return NULL;*attached=1;}return env;}
int fcRestrictedProtect(uintptr_t owner,int fd){int attached;JNIEnv *env=environment(&attached);if(!env)return 0;jobject service=(jobject)owner;jclass cls=(*env)->GetObjectClass(env,service);jmethodID method=(*env)->GetMethodID(env,cls,"protect","(I)Z");int ok=method&&(*env)->CallBooleanMethod(env,service,method,fd);if((*env)->ExceptionCheck(env)){(*env)->ExceptionClear(env);ok=0;}(*env)->DeleteLocalRef(env,cls);if(attached)(*vm)->DetachCurrentThread(vm);return ok;}
void fcRestrictedRelease(uintptr_t owner){int attached;JNIEnv *env=environment(&attached);if(!env)return;(*env)->DeleteGlobalRef(env,(jobject)owner);if(attached)(*vm)->DetachCurrentThread(vm);}
struct text{const char *str;long size;};
extern int64_t fcRestrictedBegin(struct text,struct text,struct text,uintptr_t);
extern int32_t fcRestrictedTun(int64_t,int32_t);
extern int32_t fcRestrictedState(int64_t);
extern int32_t fcRestrictedStop(int64_t);
extern char *fcRestrictedStats(int64_t);
extern char *fcRestrictedReadiness(struct text);
extern int32_t fcRestrictedValidateDelivery(struct text,struct text,struct text);
extern int32_t fcRestrictedValidationCode(struct text,struct text,struct text);
JNIEXPORT jint JNICALL Java_com_familyconnect_app_NativeRestricted_validationCode(JNIEnv *env,jclass cls,jbyteArray response,jbyteArray identity,jbyteArray anchor){
 if(!response||!identity||!anchor)return 1;
 jbyte *raw=(*env)->GetByteArrayElements(env,response,NULL),*public=(*env)->GetByteArrayElements(env,identity,NULL),*root=(*env)->GetByteArrayElements(env,anchor,NULL);
 int32_t result=1;
 if(raw&&public&&root)result=fcRestrictedValidationCode((struct text){(char*)raw,(*env)->GetArrayLength(env,response)},(struct text){(char*)public,(*env)->GetArrayLength(env,identity)},(struct text){(char*)root,(*env)->GetArrayLength(env,anchor)});
 if(raw)(*env)->ReleaseByteArrayElements(env,response,raw,JNI_ABORT);if(public)(*env)->ReleaseByteArrayElements(env,identity,public,JNI_ABORT);if(root)(*env)->ReleaseByteArrayElements(env,anchor,root,JNI_ABORT);return result;
}
extern int64_t fcRestrictedBeginReady(struct text,struct text,struct text,struct text,uintptr_t);
JNIEXPORT jboolean JNICALL Java_com_familyconnect_app_NativeRestricted_validateDelivery(JNIEnv *env,jclass cls,jbyteArray response,jbyteArray identity,jbyteArray anchor){
 if(!response||!identity||!anchor)return 0;
 jbyte *raw=(*env)->GetByteArrayElements(env,response,NULL),*public=(*env)->GetByteArrayElements(env,identity,NULL),*root=(*env)->GetByteArrayElements(env,anchor,NULL);
 int32_t result=0;
 if(raw&&public&&root)result=fcRestrictedValidateDelivery((struct text){(char*)raw,(*env)->GetArrayLength(env,response)},(struct text){(char*)public,(*env)->GetArrayLength(env,identity)},(struct text){(char*)root,(*env)->GetArrayLength(env,anchor)});
 if(raw)(*env)->ReleaseByteArrayElements(env,response,raw,JNI_ABORT);if(public)(*env)->ReleaseByteArrayElements(env,identity,public,JNI_ABORT);if(root)(*env)->ReleaseByteArrayElements(env,anchor,root,JNI_ABORT);return result!=0;
}
JNIEXPORT jlong JNICALL Java_com_familyconnect_app_NativeRestricted_beginReady(JNIEnv *env,jclass cls,jbyteArray response,jbyteArray identity,jbyteArray anchor,jstring resolver,jobject service){
 if(!response||!identity||!anchor||!resolver||!service)return 0;
 jbyte *raw=(*env)->GetByteArrayElements(env,response,NULL),*secret=(*env)->GetByteArrayElements(env,identity,NULL),*root=(*env)->GetByteArrayElements(env,anchor,NULL);
 const char *dns=(*env)->GetStringUTFChars(env,resolver,NULL);int64_t result=0;
 if(raw&&secret&&root&&dns){jobject owner=(*env)->NewGlobalRef(env,service);if(owner)result=fcRestrictedBeginReady((struct text){(char*)raw,(*env)->GetArrayLength(env,response)},(struct text){(char*)secret,(*env)->GetArrayLength(env,identity)},(struct text){(char*)root,(*env)->GetArrayLength(env,anchor)},(struct text){dns,(*env)->GetStringUTFLength(env,resolver)},(uintptr_t)owner);}
 if(secret){volatile jbyte *wipe=secret;jsize length=(*env)->GetArrayLength(env,identity);for(jsize index=0;index<length;index++)wipe[index]=0;}
 if(raw)(*env)->ReleaseByteArrayElements(env,response,raw,JNI_ABORT);if(secret)(*env)->ReleaseByteArrayElements(env,identity,secret,JNI_ABORT);if(root)(*env)->ReleaseByteArrayElements(env,anchor,root,JNI_ABORT);if(dns)(*env)->ReleaseStringUTFChars(env,resolver,dns);return result;
}
JNIEXPORT jstring JNICALL Java_com_familyconnect_app_NativeRestricted_readiness(JNIEnv *env,jclass cls,jstring directory){if(!directory)return NULL;const char *path=(*env)->GetStringUTFChars(env,directory,0);if(!path)return NULL;char *raw=fcRestrictedReadiness((struct text){path,(*env)->GetStringUTFLength(env,directory)});(*env)->ReleaseStringUTFChars(env,directory,path);if(!raw)return NULL;jstring result=(*env)->NewStringUTF(env,raw);free(raw);return result;}
JNIEXPORT jlong JNICALL Java_com_familyconnect_app_NativeRestricted_begin(JNIEnv *env,jclass cls,jstring directory,jstring control,jstring resolver,jobject service){
 if(!directory||!control||!resolver||!service)return 0;
 const char *dir=(*env)->GetStringUTFChars(env,directory,NULL),*url=(*env)->GetStringUTFChars(env,control,NULL),*dns=(*env)->GetStringUTFChars(env,resolver,NULL);
 if(!dir||!url||!dns){if(dir)(*env)->ReleaseStringUTFChars(env,directory,dir);if(url)(*env)->ReleaseStringUTFChars(env,control,url);if(dns)(*env)->ReleaseStringUTFChars(env,resolver,dns);return 0;}
 jobject owner=(*env)->NewGlobalRef(env,service);int64_t result=0;
 if(owner)result=fcRestrictedBegin((struct text){dir,(*env)->GetStringUTFLength(env,directory)},(struct text){url,(*env)->GetStringUTFLength(env,control)},(struct text){dns,(*env)->GetStringUTFLength(env,resolver)},(uintptr_t)owner);
 (*env)->ReleaseStringUTFChars(env,directory,dir);(*env)->ReleaseStringUTFChars(env,control,url);(*env)->ReleaseStringUTFChars(env,resolver,dns);return result;
}
JNIEXPORT jint JNICALL Java_com_familyconnect_app_NativeRestricted_state(JNIEnv *env,jclass cls,jlong id){return fcRestrictedState(id);}
JNIEXPORT jboolean JNICALL Java_com_familyconnect_app_NativeRestricted_attach(JNIEnv *env,jclass cls,jlong id,jint fd){return fcRestrictedTun(id,fd)!=0;}
JNIEXPORT jboolean JNICALL Java_com_familyconnect_app_NativeRestricted_stop(JNIEnv *env,jclass cls,jlong id){return fcRestrictedStop(id)!=0;}
JNIEXPORT jstring JNICALL Java_com_familyconnect_app_NativeRestricted_stats(JNIEnv *env,jclass cls,jlong id){char *raw=fcRestrictedStats(id);if(!raw)return NULL;jstring result=(*env)->NewStringUTF(env,raw);free(raw);return result;}
