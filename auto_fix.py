import os
import sys
import json
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

ROOT = Path.home() / "Project100"
os.chdir(ROOT)

def run(args, timeout=None):
    print("\n>>>", " ".join(map(str, args)), flush=True)
    try:
        return subprocess.run(
            args, cwd=ROOT, text=True,
            timeout=timeout
        ).returncode
    except subprocess.TimeoutExpired:
        print("Command timed out.")
        return 124
    except FileNotFoundError:
        print("Command not found:", args[0])
        return 127

def backup(path):
    path = Path(path)
    if path.exists():
        target = path.with_name(
            path.name + ".backup-" +
            datetime.now().strftime("%Y%m%d-%H%M%S")
        )
        shutil.copy2(path, target)
        print("Backup:", target)

def stop(message):
    print("\nSTOP:", message)
    sys.exit(1)

print("=" * 55)
print("PROJECT100 AUTO CHECK AND REPAIR")
print("=" * 55)

# 1. Check important files
required = [
    "package.json",
    "capacitor.config.json",
    "www/index.html",
    "android/app/build.gradle",
    "android/gradlew",
    "android/app/src/main/java/com/project100/app/MainActivity.java",
    "android/app/src/main/java/com/project100/app/FacebookRewardedPlugin.java",
    "android/app/src/main/java/com/project100/app/UnityAdsPlugin.java",
    ".github/workflows/android-apk.yml",
]
missing = [x for x in required if not (ROOT / x).is_file()]
if missing:
    print("Missing files:")
    for x in missing:
        print(" -", x)
    stop("Missing files cannot safely be recreated without their contents.")

# 2. Validate JSON files
for name in ["package.json", "capacitor.config.json"]:
    try:
        json.loads((ROOT / name).read_text())
        print("JSON OK:", name)
    except Exception as e:
        stop(f"{name} is invalid: {e}")

# 3. Check tools
for tool in ["node", "npm", "git", "java"]:
    print(tool + ":", shutil.which(tool) or "NOT FOUND")

if not shutil.which("npm"):
    stop("Install Node.js/npm in Termux first.")

# 4. Back up project config and custom plugins
for name in [
    "android/app/build.gradle",
    "android/app/src/main/java/com/project100/app/MainActivity.java",
    "android/app/src/main/java/com/project100/app/FacebookRewardedPlugin.java",
    "android/app/src/main/java/com/project100/app/UnityAdsPlugin.java",
]:
    backup(ROOT / name)

# 5. Fix missing SDK dependencies if absent
gradle = ROOT / "android/app/build.gradle"
content = gradle.read_text()
changed = False

deps = [
    'implementation "com.facebook.android:audience-network-sdk:6.20.0"',
    'implementation "com.unity3d.ads:unity-ads:4.16.0"',
]
for dep in deps:
    if dep not in content:
        marker = "dependencies {"
        if marker not in content:
            stop("Cannot locate dependencies block in app/build.gradle.")
        content = content.replace(marker, marker + "\n    " + dep, 1)
        changed = True

if changed:
    gradle.write_text(content)
    print("Added missing SDK dependencies.")

# 6. Ensure custom Capacitor plugins are registered
main = ROOT / "android/app/src/main/java/com/project100/app/MainActivity.java"
main_text = main.read_text()
if "registerPlugin(FacebookRewardedPlugin.class)" not in main_text:
    print("Facebook plugin is not registered.")
if "registerPlugin(UnityAdsPlugin.class)" not in main_text:
    print("Unity plugin is not registered.")
print("MainActivity checked.")

# 7. Install JS dependencies
if (ROOT / "package-lock.json").exists():
    code = run(["npm", "ci"], timeout=600)
else:
    code = run(["npm", "install"], timeout=600)
if code:
    stop("npm dependencies failed; check the npm error above.")

# 8. Sync Capacitor
code = run(["npx", "cap", "sync", "android"], timeout=600)
if code:
    stop("Capacitor sync failed; see error above.")

# 9. Make Gradle wrapper executable
wrapper = ROOT / "android/gradlew"
wrapper.chmod(wrapper.stat().st_mode | 0o111)

# 10. Build APK
code = run([
    str(wrapper), "-p", "android",
    "assembleDebug", "--stacktrace"
], timeout=1800)

if code:
    print("\nBUILD FAILED.")
    print("Automatic dependency/config fixes were attempted.")
    print("The remaining Java SDK/API errors require matching the exact SDK interfaces.")
    print("No custom Java source was overwritten automatically.")
    sys.exit(code)

apk = ROOT / "android/app/build/outputs/apk/debug/app-debug.apk"
if not apk.is_file():
    stop("Build ended without finding the APK.")

print("\nSUCCESS: APK CREATED")
print("File:", apk)
print("Size:", apk.stat().st_size, "bytes")
print("\nBuild complete.")
