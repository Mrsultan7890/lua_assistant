#!/bin/bash
# Generate keystore for Play Store signing

echo "Creating keystore for LUA Assistant..."

keytool -genkey -v -keystore lua-assistant-key.jks \
  -keyalg RSA -keysize 2048 -validity 10000 \
  -alias lua-assistant \
  -storepass lua123456 \
  -keypass lua123456 \
  -dname "CN=LUA Assistant, OU=Development, O=LUA, L=City, S=State, C=IN"

echo "Keystore created: lua-assistant-key.jks"
echo "Store Password: lua123456"
echo "Key Password: lua123456"
echo "Alias: lua-assistant"