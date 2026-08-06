#!/usr/bin/env python3
"""Compile and run Java tests without Maven."""

import os
import subprocess
import glob

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_DIR = os.path.join(PROJECT_DIR, "src", "test", "java")
MAIN_DIR = os.path.join(PROJECT_DIR, "src", "main", "java")
TARGET_DIR = os.path.join(PROJECT_DIR, "target")
M2_REPO = os.path.expanduser("~/.m2/repository")

# Create target directories
os.makedirs(os.path.join(TARGET_DIR, "classes"), exist_ok=True)
os.makedirs(os.path.join(TARGET_DIR, "test-classes"), exist_ok=True)

# Find all JAR dependencies
def find_jars(patterns):
    jars = []
    for pattern in patterns:
        jar_path = os.path.join(M2_REPO, pattern)
        if os.path.isfile(jar_path):
            jars.append(jar_path)
    return jars

# JAR patterns (relative to M2_REPO)
jar_patterns = [
    # JUnit Jupiter
    "org/junit/jupiter/junit-jupiter-api/5.10.2/junit-jupiter-api-5.10.2.jar",
    "org/junit/jupiter/junit-jupiter-engine/5.10.2/junit-jupiter-engine-5.10.2.jar",
    "org/junit/platform/junit-platform-commons/1.10.2/junit-platform-commons-1.10.2.jar",
    "org/junit/platform/junit-platform-launcher/1.10.2/junit-platform-launcher-1.10.2.jar",
    "org/opentest4j/opentest4j/1.3.0/opentest4j-1.3.0.jar",
    "org/junit/jupiter/junit-jupiter-params/5.10.2/junit-jupiter-params-5.10.2.jar",
    # AssertJ
    "org/assertj/assertj-core/3.24.2/assertj-core-3.24.2.jar",
    # Mockito
    "org/mockito/mockito-core/5.11.0/mockito-core-5.11.0.jar",
    "org/mockito/mockito-junit-jupiter/5.11.0/mockito-junit-jupiter-5.11.0.jar",
    "net/bytebuddy/byte-buddy/1.14.15/byte-buddy-1.14.15.jar",
    "net/bytebuddy/byte-buddy-agent/1.14.15/byte-buddy-agent-1.14.15.jar",
    "org/objenesis/objenesis/3.3/objenesis-3.3.jar",
    # Hamcrest
    "org/hamcrest/hamcrest/2.2/hamcrest-2.2.jar",
    # Spring
    "org/springframework/spring-web/6.1.1/spring-web-6.1.1.jar",
    "org/springframework/spring-context/6.1.1/spring-context-6.1.1.jar",
    "org/springframework/spring-beans/6.1.1/spring-beans-6.1.1.jar",
    "org/springframework/spring-core/6.1.1/spring-core-6.1.1.jar",
    "org/springframework/spring-tx/6.1.1/spring-tx-6.1.1.jar",
    "org/springframework/spring-jcl/6.1.1/spring-jcl-6.1.1.jar",
    "ch/qos/logback/logback-classic/1.4.14/logback-classic-1.4.14.jar",
    "ch/qos/logback/logback-core/1.4.14/logback-core-1.4.14.jar",
    # Jakarta
    "jakarta/validation/jakarta.validation-api/3.0.2/jakarta.validation-api-3.0.2.jar",
    "org/springframework/spring-webmvc/6.1.1/spring-webmvc-6.1.1.jar",
    "org/springframework/spring-expression/6.1.1/spring-expression-6.1.1.jar",
]

CP = ":".join(find_jars(jar_patterns))

print("Compiling main sources...")
main_files = []
for root, dirs, files in os.walk(MAIN_DIR):
    for f in files:
        if f.endswith(".java"):
            main_files.append(os.path.join(root, f))

result = subprocess.run(
    ["javac", "-d", os.path.join(TARGET_DIR, "classes")] + main_files,
    capture_output=True,
    text=True
)
if result.returncode != 0:
    print(f"Compilation failed: {result.stderr}")
    exit(1)
print(f"Compiled {len(main_files)} main source files")

print("Compiling test sources...")
test_files = []
for root, dirs, files in os.walk(TEST_DIR):
    for f in files:
        if f.endswith(".java"):
            test_files.append(os.path.join(root, f))

result = subprocess.run(
    ["javac", "-d", os.path.join(TARGET_DIR, "test-classes"), "-cp", CP] + test_files,
    capture_output=True,
    text=True
)
if result.returncode != 0:
    print(f"Test compilation failed: {result.stderr}")
    exit(1)
print(f"Compiled {len(test_files)} test source files")

print("Running tests...")
test_result = subprocess.run(
    ["java", "-cp", f"{CP}:{os.path.join(TARGET_DIR, 'test-classes')}",
     "org.junit.platform.console.ConsoleLauncher",
     "--class-path", os.path.join(TARGET_DIR, "test-classes"),
     "--select-class", "com.example.taskapi.repositories.TaskRepositoryTest",
     "--select-class", "com.example.taskapi.services.TaskServiceTest",
     "--include-classname", ".*Tests",
     "--include-classname", ".*Test"],
    capture_output=True,
    text=True
)

print(test_result.stdout)
if test_result.stderr:
    print(test_result.stderr)

exit(test_result.returncode)
