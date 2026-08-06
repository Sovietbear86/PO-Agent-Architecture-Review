#!/bin/bash

# Script to run Java tests without Maven (unit tests only)
# Requires: Java 17+, JAR files in ~/.m2/repository
#
# Note: The preferred way to run tests is with Maven: mvn test
# This script is a fallback for environments without Maven installed.

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_DIR="$PROJECT_DIR/src/test/java"
MAIN_DIR="$PROJECT_DIR/src/main/java"
TARGET_DIR="$PROJECT_DIR/target"

# Create target directory
mkdir -p "$TARGET_DIR/classes"
mkdir -p "$TARGET_DIR/test-classes"

# Find all JAR dependencies from Maven repository
M2_REPO="$HOME/.m2/repository"
CP=""

# Add JUnit Jupiter API
for jar in "$M2_REPO/org/junit/jupiter/junit-jupiter-api/5.10.2/junit-jupiter-api-5.10.2.jar" \
           "$M2_REPO/org/junit/jupiter/junit-jupiter-engine/5.10.2/junit-jupiter-engine-5.10.2.jar" \
           "$M2_REPO/org/junit/platform/junit-platform-commons/1.10.2/junit-platform-commons-1.10.2.jar" \
           "$M2_REPO/org/junit/platform/junit-platform-launcher/1.10.2/junit-platform-launcher-1.10.2.jar" \
           "$M2_REPO/org/opentest4j/opentest4j/1.3.0/opentest4j-1.3.0.jar" \
           "$M2_REPO/org/junit/jupiter/junit-jupiter-params/5.10.2/junit-jupiter-params-5.10.2.jar"; do
    if [ -f "$jar" ]; then
        CP="$CP:$jar"
    fi
done

# Add AssertJ
for jar in "$M2_REPO/org/assertj/assertj-core/3.24.2/assertj-core-3.24.2.jar"; do
    if [ -f "$jar" ]; then
        CP="$CP:$jar"
    fi
done

# Add Mockito
for jar in "$M2_REPO/org/mockito/mockito-core/5.11.0/mockito-core-5.11.0.jar" \
           "$M2_REPO/org/mockito/mockito-junit-jupiter/5.11.0/mockito-junit-jupiter-5.11.0.jar"; do
    if [ -f "$jar" ]; then
        CP="$CP:$jar"
    fi
done

# Add Byte Buddy and Objenesis
for jar in "$M2_REPO/net/bytebuddy/byte-buddy/1.14.15/byte-buddy-1.14.15.jar" \
           "$M2_REPO/net/bytebuddy/byte-buddy-agent/1.14.15/byte-buddy-agent-1.14.15.jar" \
           "$M2_REPO/org/objenesis/objenesis/3.3/objenesis-3.3.jar"; do
    if [ -f "$jar" ]; then
        CP="$CP:$jar"
    fi
done

# Add Hamcrest
for jar in "$M2_REPO/org/hamcrest/hamcrest/2.2/hamcrest-2.2.jar"; do
    if [ -f "$jar" ]; then
        CP="$CP:$jar"
    fi
done

# Add Spring Boot dependencies
for jar in "$M2_REPO/org/springframework/spring-web/6.1.1/spring-web-6.1.1.jar" \
           "$M2_REPO/org/springframework/spring-context/6.1.1/spring-context-6.1.1.jar" \
           "$M2_REPO/org/springframework/spring-beans/6.1.1/spring-beans-6.1.1.jar" \
           "$M2_REPO/org/springframework/spring-core/6.1.1/spring-core-6.1.1.jar" \
           "$M2_REPO/org/springframework/spring-tx/6.1.1/spring-tx-6.1.1.jar" \
           "$M2_REPO/org/springframework/spring-jcl/6.1.1/spring-jcl-6.1.1.jar" \
           "$M2_REPO/ch/qos/logback/logback-classic/1.4.14/logback-classic-1.4.14.jar" \
           "$M2_REPO/ch/qos/logback/logback-core/1.4.14/logback-core-1.4.14.jar"; do
    if [ -f "$jar" ]; then
        CP="$CP:$jar"
    fi
done

# Add Jakarta Validation
for jar in "$M2_REPO/jakarta/validation/jakarta.validation-api/3.0.2/jakarta.validation-api-3.0.2.jar"; do
    if [ -f "$jar" ]; then
        CP="$CP:$jar"
    fi
done

# Add Spring Web
for jar in "$M2_REPO/org/springframework/spring-webmvc/6.1.1/spring-webmvc-6.1.1.jar" \
           "$M2_REPO/org/springframework/spring-expression/6.1.1/spring-expression-6.1.1.jar"; do
    if [ -f "$jar" ]; then
        CP="$CP:$jar"
    fi
done

echo "Compiling main sources..."
python3 -c "
import os
import glob
files = []
for root, dirs, filenames in os.walk('$MAIN_DIR'):
    files.extend(glob.glob(os.path.join(root, '*.java')))
print(' '.join(['\"' + f + '\"' for f in files]))
" > /tmp/java_sources.txt

javac -d "$TARGET_DIR/classes" $(cat /tmp/java_sources.txt)

echo "Compiling test sources..."
python3 -c "
import os
import glob
files = []
for root, dirs, filenames in os.walk('$TEST_DIR'):
    files.extend(glob.glob(os.path.join(root, '*.java')))
print(' '.join(['\"' + f + '\"' for f in files]))
" > /tmp/java_test_sources.txt

javac -d "$TARGET_DIR/test-classes" -cp "$TARGET_DIR/classes:$CP" $(cat /tmp/java_test_sources.txt)

echo "Running tests..."
java -cp "$CP:$TARGET_DIR/test-classes" \
    org.junit.platform.console.ConsoleLauncher \
    --class-path "$TARGET_DIR/test-classes" \
    --select-class "com.example.taskapi.repositories.TaskRepositoryTest" \
    --select-class "com.example.taskapi.services.TaskServiceTest" \
    --include-classname ".*Tests" \
    --include-classname ".*Test"
