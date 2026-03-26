# Android build environment
FROM eclipse-temurin:17-jdk-jammy

# Install Android SDK
ENV ANDROID_SDK_ROOT=/opt/android-sdk
ENV PATH=${PATH}:${ANDROID_SDK_ROOT}/cmdline-tools/latest/bin:${ANDROID_SDK_ROOT}/platform-tools

WORKDIR /app

# Install Android command line tools
RUN apt-get update && \
    apt-get install -y wget unzip && \
    mkdir -p ${ANDROID_SDK_ROOT}/cmdline-tools && \
    wget -q https://dl.google.com/android/repository/commandlinetools-linux-9477386_latest.zip && \
    unzip -q commandlinetools-linux-9477386_latest.zip -d ${ANDROID_SDK_ROOT}/cmdline-tools && \
    mv ${ANDROID_SDK_ROOT}/cmdline-tools/cmdline-tools ${ANDROID_SDK_ROOT}/cmdline-tools/latest && \
    rm commandlinetools-linux-9477386_latest.zip && \
    apt-get clean

# Accept licenses and install SDK components
RUN yes | sdkmanager --licenses && \
    sdkmanager "platform-tools" "platforms;android-36" "build-tools;35.0.0"

# Copy gradle wrapper and dependencies
COPY gradlew gradle.properties settings.gradle.kts build.gradle.kts ./
COPY gradle ./gradle
RUN sed -i 's/\r$//' gradlew && chmod +x gradlew

# Copy app source
COPY app ./app

# Build the app
RUN ./gradlew assembleDebug --no-daemon

# Run tests
CMD ["./gradlew", "test", "--no-daemon"]
