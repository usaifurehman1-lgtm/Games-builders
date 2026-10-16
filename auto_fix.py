import os
import sys
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path.home() / "Project100"
ANDROID = ROOT / "android"
WWW = ROOT / "www"
REPORT = ROOT / "auto_fix_report.txt"

log = []

def say(message):
    print(message)
    log.append(message)

def run(command, cwd=ROOT):
    say("\n$ " + " ".join(map(str, command)))
    try:
        result = subprocess.run(
            command,
            cwd=str(cwd),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=1800
        )
        output = result.stdout or ""
        print(output[-7000:])
        log.append(output[-7000:])
        return result.returncode
    except Exception as error:
        say("ERROR: " + str(error))
        return 1

def check_file(path):
    return path.exists() and path.is_file()

os.chdir(ROOT)
say("=== PROJECT100 AUTO CHECK AND BUILD ===")
say("Project: " + str(ROOT))

# 1. Check essential files
required = [
    ROOT / "package.json",
    ROOT / "capacitor.config.json",
    WWW / "index.html",
    ANDROID / "gradlew",
    ANDROID / "app/build.gradle",
    ANDROID / "app/src/main/AndroidManifest.xml",
]

missing = [str(p.relative_to(ROOT)) for p in required if not check_file(p)]
if missing:
    say("MISSING REQUIRED FILES:")
    for item in missing:
        say(" - " + item)
    say("Cannot safely build until required files are restored.")
    REPORT.write_text("\n".join(log))
    sys.exit(1)

# 2. Confirm project identity
try:
    package = json.loads((ROOT / "package.json").read_text())
    say("Package name: " + str(package.get("name", "unknown")))
except Exception as error:
    say("Could not parse package.json: " + str(error))

# 3. Check all original plugin source files without overwriting them
plugin_dir = ROOT / "plugin-source"
plugin_files = [
    "admob longin",
    "facebook.longin",
    "start_io_longin",
    "unity.longin",
]
for name in plugin_files:
    path = plugin_dir / name
    if path.exists():
        say("SOURCE OK: " + name)
    else:
        say("SOURCE MISSING: " + name)

# 4. Check Android Java files
java_dir = ANDROID / "app/src/main/java/com/project100/app"
java_dir.mkdir(parents=True, exist_ok=True)

for name in [
    "MainActivity.java",
    "FacebookRewardedPlugin.java",
    "UnityAdsPlugin.java",
    "StartIoAdsPlugin.java",
]:
    path = java_dir / name
    say(("JAVA OK: " if path.exists() else "JAVA MISSING: ") + name)

# 5. Check Gradle, Java, and Android SDK
for tool in ["java", "node", "npm", "git"]:
    say(f"{tool}: {shutil.which(tool) or 'NOT FOUND'}")

sdk_paths = [
    os.environ.get("ANDROID_HOME"),
    os.environ.get("ANDROID_SDK_ROOT"),
    str(Path.home() / "Android/Sdk"),
]
sdk = next((Path(p) for p in sdk_paths if p and Path(p).exists()), None)
say("Android SDK: " + (str(sdk) if sdk else "NOT FOUND"))

if sdk:
    os.environ["ANDROID_HOME"] = str(sdk)
    os.environ["ANDROID_SDK_ROOT"] = str(sdk)

# 6. Sync existing Capacitor project
if shutil.which("npx"):
    sync_code = run(["npx", "cap", "sync", "android"])
    say("Capacitor sync exit code: " + str(sync_code))
else:
    say("npx unavailable; skipping Capacitor sync.")

# 7. Try local APK build only if Java and SDK are present
java_ok = shutil.which("java") is not None
gradlew = ANDROID / "gradlew"

if java_ok and sdk and gradlew.exists():
    gradlew.chmod(gradlew.stat().st_mode | 0o111)
    build_code = run(
        ["./gradlew", "assembleDebug", "--stacktrace"],
        cwd=ANDROID
    )
    apk = ANDROID / "app/build/outputs/apk/debug/app-debug.apk"
    if build_code == 0 and apk.exists():
        say("BUILD SUCCESS")
        say("APK PATH: " + str(apk))
    else:
        say("LOCAL BUILD FAILED. See Gradle output above.")
else:
    say("LOCAL APK BUILD SKIPPED: Java or Android SDK is missing.")
    say("A remote Android build runner, such as GitHub Actions, may be needed.")

# 8. Report results
REPORT.write_text("\n".join(log), encoding="utf-8")
say("REPORT SAVED: " + str(REPORT))
say("=== AUTO CHECK FINISHED ===")
say("This script does not invent ad IDs or claim unverified SDKs work.")
