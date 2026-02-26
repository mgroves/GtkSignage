#!/usr/bin/env bash
set -e

APP_ID="com.mgroves.GtkSignage"
MANIFEST="com.mgroves.GtkSignage.yml"
DIST_DIR="dist"
INSTALL_SCRIPT="install.sh"

echo "GtkSignage publish"
echo "=================="
echo

# -----------------------------
# Preconditions
# -----------------------------
if ! command -v flatpak-builder >/dev/null 2>&1; then
  echo "ERROR: flatpak-builder not found."
  echo "Install it with:"
  echo "  sudo apt install flatpak-builder"
  exit 1
fi

if [ ! -f "$MANIFEST" ]; then
  echo "ERROR: Flatpak manifest not found:"
  echo "  $MANIFEST"
  exit 1
fi

if [ ! -f "$INSTALL_SCRIPT" ]; then
  echo "ERROR: install.sh not found in repo root."
  exit 1
fi

# -----------------------------
# Version input
# -----------------------------
read -rp "Version to publish (e.g. 1.2.0): " VERSION

if [[ -z "$VERSION" ]]; then
  echo "Version is required."
  exit 1
fi

BUNDLE_NAME="GtkSignage-${VERSION}.flatpak"
ZIP_NAME="GtkSignage-${VERSION}.zip"

BUNDLE_PATH="$DIST_DIR/$BUNDLE_NAME"
ZIP_PATH="$DIST_DIR/$ZIP_NAME"

# -----------------------------
# Release notes
# -----------------------------
read -rp "Release notes Markdown file (optional): " NOTES_FILE

if [[ -n "$NOTES_FILE" && ! -f "$NOTES_FILE" ]]; then
  echo "ERROR: Release notes file not found:"
  echo "  $NOTES_FILE"
  exit 1
fi

# -----------------------------
# Build Flatpak bundle
# -----------------------------
echo
echo "Building Flatpak bundle..."
echo

mkdir -p "$DIST_DIR"

rm -rf build-dir repo

flatpak-builder \
  --force-clean \
  --repo=repo \
  build-dir \
  "$MANIFEST"

flatpak build-bundle \
  repo \
  "$BUNDLE_PATH" \
  "$APP_ID"

echo
echo "Flatpak bundle created:"
echo "  $BUNDLE_PATH"

# -----------------------------
# Prepare ZIP payload
# -----------------------------
echo
echo "Creating release ZIP..."

zip -j "$ZIP_PATH" \
  "$BUNDLE_PATH" \
  "$INSTALL_SCRIPT"

echo "Release ZIP created:"
echo "  $ZIP_PATH"

# -----------------------------
# Optional: GitHub release
# -----------------------------
echo
read -rp "Publish GitHub release? (y/N): " PUBLISH

if [[ "$PUBLISH" =~ ^[Yy]$ ]]; then
  if ! command -v gh >/dev/null 2>&1; then
    echo "ERROR: GitHub CLI (gh) not installed."
    echo "Install from https://cli.github.com/"
    exit 1
  fi

  if ! gh auth status >/dev/null 2>&1; then
    echo "ERROR: gh is not authenticated."
    echo "Run:"
    echo "  gh auth login"
    exit 1
  fi

  TAG="v$VERSION"

  echo
  echo "Creating GitHub release $TAG..."

  if [[ -n "$NOTES_FILE" ]]; then
    gh release create "$TAG" \
      "$ZIP_PATH" \
      "$BUNDLE_PATH" \
      --title "GtkSignage $VERSION" \
      --notes-file "$NOTES_FILE"
  else
    gh release create "$TAG" \
      "$ZIP_PATH" \
      "$BUNDLE_PATH" \
      --title "GtkSignage $VERSION" \
      --notes "Release $VERSION"
  fi

  echo
  echo "GitHub release published."
fi

# -----------------------------
# Done
# -----------------------------
echo
echo "Publish complete."
echo
echo "Artifacts:"
echo "  $BUNDLE_PATH"
echo "  $ZIP_PATH"
echo