//go:build android && fc_messenger_lab

#include <jni.h>
#include <stdint.h>
#include <stdlib.h>
struct lab_text {const char *ptr;long len;};
extern char *fcMessengerSharing(int64_t,struct lab_text,struct lab_text,struct lab_text,struct lab_text);
JNIEXPORT jstring JNICALL Java_com_familyconnect_app_MessengerLabActivity_sharing(JNIEnv *env,jclass cls,jlong handle,jbyteArray response,jbyteArray identity,jbyteArray anchor,jstring body){
 if(!response||!identity||!anchor||!body)return NULL;
 jbyte *raw=(*env)->GetByteArrayElements(env,response,NULL),*secret=(*env)->GetByteArrayElements(env,identity,NULL),*root=(*env)->GetByteArrayElements(env,anchor,NULL);
 const char *request=(*env)->GetStringUTFChars(env,body,NULL);char *result=NULL;
 if(raw&&secret&&root&&request)result=fcMessengerSharing(handle,(struct lab_text){(char*)raw,(*env)->GetArrayLength(env,response)},(struct lab_text){(char*)secret,(*env)->GetArrayLength(env,identity)},(struct lab_text){(char*)root,(*env)->GetArrayLength(env,anchor)},(struct lab_text){request,(*env)->GetStringUTFLength(env,body)});
 if(secret){volatile jbyte *wipe=secret;for(jsize index=0;index<(*env)->GetArrayLength(env,identity);index++)wipe[index]=0;}
 if(raw)(*env)->ReleaseByteArrayElements(env,response,raw,JNI_ABORT);
 if(secret)(*env)->ReleaseByteArrayElements(env,identity,secret,JNI_ABORT);
 if(root)(*env)->ReleaseByteArrayElements(env,anchor,root,JNI_ABORT);
 if(request)(*env)->ReleaseStringUTFChars(env,body,request);
 if(!result)return NULL;
 jstring value=(*env)->NewStringUTF(env,result);free(result);return value;
}
