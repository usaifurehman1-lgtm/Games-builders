from pathlib import Path
import subprocess
import sys
import re

ROOT = Path.home() / "Project100"
REPO = "https://github.com/usaifurehman1-lgtm/Games-builders.git"

def run(args, check=True):
    print("\n$", " ".join(map(str, args)))
    result = subprocess.run(
        args, cwd=ROOT, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    print(result.stdout[-5000:])
    if check and result.returncode:
        raise RuntimeError("Command failed: " + args[0])
    return result

try:
    # Confirm important project files
    for name in [
        "www/index.html",
        "package.json",
        "package-lock.json",
        "android/gradlew",
        "android/app/build.gradle",
    ]:
        if not (ROOT / name).exists():
            raise RuntimeError("Required file missing: " + name)

    # Add safe ignore rules without replacing existing rules
    ignore = ROOT / ".gitignore"
    rules = [
        "node_modules/",
        "android/.gradle/",
        "android/build/",
        "android/app/build/",
        "android/local.properties",
        ".env",
        ".env.*",
        "*.keystore",
        "*.jks",
        "auto_fix_report.txt",
        "__pycache__/",
    ]
    old = ignore.read_text() if ignore.exists() else ""
    with ignore.open("a") as f:
        for rule in rules:
            if rule not in old.splitlines():
                f.write(rule + "\n")

    # Create the GitHub Actions Android build workflow
    workflow = ROOT / ".github/workflows/android-apk.yml"
    workflow.parent.mkdir(parents=True, exist_ok=True)
    workflow.write_text("""name: Project100 Android APK

on:
  workflow_dispatch:
  push:
    branches: [main]

permissions:
  contents: read

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout project
        uses: actions/checkout@v4

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: npm

      - name: Set up Java
        uses: actions/setup-java@v4
        with:
          distribution: temurin
          java-version: '17'

      - name: Set up Android SDK
        uses: android-actions/setup-android@v3

      - name: Install project dependencies
        run: npm ci

      - name: Sync Capacitor Android project
        run: npx cap sync android

      - name: Build debug APK
        run: |
          chmod +x android/gradlew
          cd android
          ./gradlew assembleDebug --stacktrace

      - name: Save APK as downloadable artifact
        uses: actions/upload-artifact@v4
        with:
          name: Project100-debug-APK
          path: android/app/build/outputs/apk/debug/app-debug.apk
          if-no-files-found: error
          retention-days: 14
""")
    print("Created Android build workflow.")

    # Check GitHub authentication
    run(["gh", "auth", "status"])

    # Initialize Git if needed
    if not (ROOT / ".git").exists():
        run(["git", "init"])

    # Ensure main is the working branch
    head_exists = run(
        ["git", "rev-parse", "--verify", "HEAD"], check=False
    ).returncode == 0

    if head_exists:
        branch = run(
            ["git", "branch", "--show-current"]
        ).stdout.strip()
        if branch != "main":
            run(["git", "branch", "-M", "main"])
    else:
        run(["git", "symbolic-ref", "HEAD", "refs/heads/main"])

    # Configure commit identity only if absent
    name = run(["git", "config", "user.name"], check=False).stdout.strip()
    email = run(["git", "config", "user.email"], check=False).stdout.strip()
    if not name:
        run(["git", "config", "user.name", "Project100"])
    if not email:
        run(["git", "config", "user.email", "project100@users.noreply.github.com"])

    # Configure repository remote
    remote = run(["git", "remote", "get-url", "origin"], check=False)
    if remote.returncode:
        run(["git", "remote", "add", "origin", REPO])
    elif remote.stdout.strip() != REPO:
        run(["git", "remote", "set-url", "origin", REPO])

    # Stage files, excluding ignored files
    run(["git", "add", "-A"])

    # Scan staged text files for common credential patterns
    names = run([
        "git", "diff", "--cached", "--name-only",
        "--diff-filter=ACMR"
    ]).stdout.splitlines()

    patterns = [
        re.compile(r"AIza[0-9A-Za-z_-]{30,}"),
        re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
        re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),
        re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
        re.compile(r"""(?i)(?:api[_-]?key|gemini_api_key)\s*[:=]\s*['"][^'"]{16,}['"]"""),
    ]

    found = []
    for filename in names:
        content = run(["git", "show", ":" + filename], check=False)
        if content.returncode:
            continue
        for pattern in patterns:
            if pattern.search(content.stdout):
                found.append(filename)
                break

    if found:
        print("\nSTOPPED: Possible credentials detected in these staged files:")
        for filename in sorted(set(found)):
            print(" -", filename)
        print("Nothing was committed or pushed. Review these files and remove secrets first.")
        sys.exit(2)

    # Commit staged project files
    staged = run(["git", "diff", "--cached", "--quiet"], check=False)
    if staged.returncode != 0:
        run(["git", "commit", "-m", "Set up Project100 Android APK build"])

    # Upload project to GitHub
    pushed = run(["git", "push", "-u", "origin", "main"], check=False)
    if pushed.returncode:
        print("\nPush did not complete. No successful upload is being claimed.")
        print("Check the Git error above before retrying.")
        sys.exit(3)

    print("\nSUCCESS: Project uploaded and build workflow pushed.")
    print("Repository: https://github.com/usaifurehman1-lgtm/Games-builders")
    print("Build runs: https://github.com/usaifurehman1-lgtm/Games-builders/actions")
    print("Open Actions to check whether the APK build succeeds.")
    print("On success, open the completed run and download Project100-debug-APK.")

except Exception as error:
    print("\nSTOPPED:", error)
    sys.exit(1)
