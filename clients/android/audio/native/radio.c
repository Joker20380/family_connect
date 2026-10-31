#include <jni.h>
#include <stdlib.h>
#include <string.h>
#include "codec2.h"

static struct CODEC2 *create(JNIEnv *env, jint mode) {
    int selected = mode == 7 ? CODEC2_MODE_1600 : mode == 8 ? CODEC2_MODE_2400 : mode == 9 ? CODEC2_MODE_3200 : -1;
    struct CODEC2 *codec = selected < 0 ? NULL : codec2_create(selected);
    if (!codec) (*env)->ThrowNew(env, (*env)->FindClass(env, "java/lang/IllegalArgumentException"), "unsupported_codec");
    return codec;
}

JNIEXPORT jbyteArray JNICALL Java_com_familyconnect_app_RadioCodec_encode(JNIEnv *env, jclass type, jshortArray pcm, jint mode) {
    (void)type;
    if (!pcm) return NULL;
    jsize length = (*env)->GetArrayLength(env, pcm);
    if (length < 1 || length > 480000) {
        (*env)->ThrowNew(env, (*env)->FindClass(env, "java/lang/IllegalArgumentException"), "audio_limit");
        return NULL;
    }
    struct CODEC2 *codec = create(env, mode);
    if (!codec) return NULL;
    int samples = codec2_samples_per_frame(codec), bytes = (codec2_bits_per_frame(codec)+7)/8;
    int frames = (length+samples-1)/samples;
    short *input = calloc((size_t)frames*samples, sizeof(short));
    unsigned char *output = calloc((size_t)frames, bytes);
    jbyteArray result = NULL;
    if (input && output) {
        (*env)->GetShortArrayRegion(env, pcm, 0, length, input);
        int peak = 0;
        for (int sample = 0; sample < length; sample++) {
            int magnitude = abs((int)input[sample]);
            if (magnitude > peak) peak = magnitude;
        }
        if (peak > 8191) {
            for (int sample = 0; sample < length; sample++) input[sample] = (short)((int)input[sample]*8191/peak);
        }
        for (int frame = 0; frame < frames; frame++) codec2_encode(codec, output+frame*bytes, input+frame*samples);
        result = (*env)->NewByteArray(env, frames*bytes);
        if (result) (*env)->SetByteArrayRegion(env, result, 0, frames*bytes, (jbyte *)output);
    }
    if (input) { memset(input, 0, (size_t)frames*samples*sizeof(short)); free(input); }
    if (output) { memset(output, 0, (size_t)frames*bytes); free(output); }
    codec2_destroy(codec);
    return result;
}

JNIEXPORT jshortArray JNICALL Java_com_familyconnect_app_RadioCodec_decode(JNIEnv *env, jclass type, jbyteArray data, jint mode) {
    (void)type;
    if (!data) return NULL;
    struct CODEC2 *codec = create(env, mode);
    if (!codec) return NULL;
    int samples = codec2_samples_per_frame(codec), bytes = (codec2_bits_per_frame(codec)+7)/8;
    jsize length = (*env)->GetArrayLength(env, data);
    if (length < bytes || length%bytes || length/bytes > 480000/samples) {
        codec2_destroy(codec);
        (*env)->ThrowNew(env, (*env)->FindClass(env, "java/lang/IllegalArgumentException"), "invalid_audio_frames");
        return NULL;
    }
    int frames = length/bytes;
    unsigned char *input = malloc(length);
    short *output = calloc((size_t)frames*samples, sizeof(short));
    jshortArray result = NULL;
    if (input && output) {
        (*env)->GetByteArrayRegion(env, data, 0, length, (jbyte *)input);
        for (int frame = 0; frame < frames; frame++) codec2_decode(codec, output+frame*samples, input+frame*bytes);
        result = (*env)->NewShortArray(env, frames*samples);
        if (result) (*env)->SetShortArrayRegion(env, result, 0, frames*samples, output);
    }
    if (input) { memset(input, 0, length); free(input); }
    if (output) { memset(output, 0, (size_t)frames*samples*sizeof(short)); free(output); }
    codec2_destroy(codec);
    return result;
}
