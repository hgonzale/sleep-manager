#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

version=$(awk -F'"' '/^version = /{print $2; exit}' "$PROJECT_DIR/pyproject.toml")
if [[ -z "$version" ]]; then
    echo "Could not determine version from pyproject.toml" >&2
    exit 1
fi

mkdir -p "$PROJECT_DIR/dist/deb"

changelog_date=$(date -R)
cat > "$PROJECT_DIR/debian/changelog" <<EOF_CHANGELOG
sleep-manager (${version}) unstable; urgency=medium

  * Automated build.

 -- Sleep Manager Maintainers <ops@example.com>  ${changelog_date}
EOF_CHANGELOG

(
    cd "$PROJECT_DIR"
    dpkg-buildpackage -b -us -uc
)

built_deb=$(ls -t "$PROJECT_DIR/"../sleep-manager_${version}_all.deb 2>/dev/null | head -n1 || true)
if [[ -z "$built_deb" ]]; then
    echo "Could not find built .deb in parent directory" >&2
    exit 1
fi

cp "$built_deb" "$PROJECT_DIR/dist/deb/"

echo "Built: $PROJECT_DIR/dist/deb/$(basename "$built_deb")"
