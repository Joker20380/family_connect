#include <jni.h>
#include <stdint.h>
#include <stdlib.h>
static JavaVM *fcVm;
JNIEXPORT jint JNICALL JNI_OnLoad(JavaVM *vm,void *reserved){fcVm=vm;return JNI_VERSION_1_6;}
static JNIEnv *fcEnv(int *attached){JNIEnv *env=NULL;*attached=0;if((*fcVm)->GetEnv(fcVm,(void **)&env,JNI_VERSION_1_6)!=JNI_OK){if((*fcVm)->AttachCurrentThread(fcVm,&env,NULL)!=JNI_OK)return NULL;*attached=1;}return env;}
int fcProtect(uintptr_t owner,int fd){int attached;JNIEnv *env=fcEnv(&attached);if(!env)return 0;jobject obj=(jobject)owner;jclass cls=(*env)->GetObjectClass(env,obj);jmethodID method=(*env)->GetMethodID(env,cls,"protect","(I)Z");int ok=method&&(*env)->CallBooleanMethod(env,obj,method,fd);if((*env)->ExceptionCheck(env)){(*env)->ExceptionClear(env);ok=0;}(*env)->DeleteLocalRef(env,cls);if(attached)(*fcVm)->DetachCurrentThread(fcVm);return ok;}
void fcRelease(uintptr_t owner){int attached;JNIEnv *env=fcEnv(&attached);if(!env)return;(*env)->DeleteGlobalRef(env,(jobject)owner);if(attached)(*fcVm)->DetachCurrentThread(fcVm);}
struct fcString{const char *str;long n;};
extern int64_t fcTcpStart(int32_t fd,struct fcString config,uintptr_t owner);
extern int32_t fcTcpStop(int64_t handle);
extern int32_t fcTcpConnections(int64_t handle);
JNIEXPORT jlong JNICALL Java_com_familyconnect_app_NativeTcp_start(JNIEnv *env,jclass cls,jint fd,jstring profile,jobject service){
 if(!profile||!service)return 0;const char *p=(*env)->GetStringUTFChars(env,profile,NULL);if(!p)return 0;
 jobject owner=(*env)->NewGlobalRef(env,service);int64_t result=0;if(owner)result=fcTcpStart(fd,(struct fcString){p,(*env)->GetStringUTFLength(env,profile)},(uintptr_t)owner);
 (*env)->ReleaseStringUTFChars(env,profile,p);return result;
}
JNIEXPORT jboolean JNICALL Java_com_familyconnect_app_NativeTcp_stop(JNIEnv *env,jclass cls,jlong id){return fcTcpStop(id)!=0;}
JNIEXPORT jint JNICALL Java_com_familyconnect_app_NativeTcp_connections(JNIEnv *env,jclass cls,jlong id){return fcTcpConnections(id);}
extern char *fcTcpDns(int64_t handle,struct fcString query,int32_t millis);
extern char *fcAwgDns(int32_t handle,struct fcString source,struct fcString query,int32_t millis);
JNIEXPORT jstring JNICALL Java_com_familyconnect_app_NativeTcp_tcpDns(JNIEnv *env,jclass cls,jlong id,jstring query,jint millis){
 if(!query||(*env)->GetStringUTFLength(env,query)>1024)return NULL;
 const char *text=(*env)->GetStringUTFChars(env,query,NULL);if(!text)return NULL;
 char *answer=fcTcpDns(id,(struct fcString){text,(*env)->GetStringUTFLength(env,query)},millis);
 (*env)->ReleaseStringUTFChars(env,query,text);if(!answer)return NULL;
 jstring result=(*env)->NewStringUTF(env,answer);free(answer);return result;
}
JNIEXPORT jstring JNICALL Java_com_familyconnect_app_NativeTcp_awgDns(JNIEnv *env,jclass cls,jint id,jstring source,jstring query,jint millis){
 if(!source||!query||(*env)->GetStringUTFLength(env,source)>15||(*env)->GetStringUTFLength(env,query)>1024)return NULL;
 const char *address=(*env)->GetStringUTFChars(env,source,NULL);if(!address)return NULL;
 const char *text=(*env)->GetStringUTFChars(env,query,NULL);if(!text){(*env)->ReleaseStringUTFChars(env,source,address);return NULL;}
 char *answer=fcAwgDns(id,(struct fcString){address,(*env)->GetStringUTFLength(env,source)},(struct fcString){text,(*env)->GetStringUTFLength(env,query)},millis);
 (*env)->ReleaseStringUTFChars(env,source,address);(*env)->ReleaseStringUTFChars(env,query,text);if(!answer)return NULL;
 jstring result=(*env)->NewStringUTF(env,answer);free(answer);return result;
}
