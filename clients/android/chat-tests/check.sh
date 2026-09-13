#!/bin/sh
set -eu
# JDK17 and Android35 SDK required; compile only, no APK or emulator installation.
: "${ANDROID_JAR:?Path to Android SDK android.jar}"
: "${CHAT_CHECK_OUTPUT:?Disposable compilation output directory}"
mkdir -p "$CHAT_CHECK_OUTPUT"
main=clients/android/app/src/main/java/com/familyconnect/app
javac -encoding UTF-8 -cp "$ANDROID_JAR" -d "$CHAT_CHECK_OUTPUT" \
 "$main/ChatKeyEnvelope.java" "$main/ChatKeyVault.java" \
 "$main/ChatSmileys.java" "$main/ChatSmileyTextView.java" clients/android/chat-tests/ChatChecks.java
java -cp "$CHAT_CHECK_OUTPUT" com.familyconnect.app.ChatChecks
