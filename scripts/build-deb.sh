#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

if [[ -n "${GITHUB_REF:-}" && "$GITHUB_REF" == refs/tags/v* ]]; then
    export HATCH_VCS_VERSION="${GITHUB_REF#refs/tags/v}"
fi

version=$(cd "$PROJECT_DIR" && python3 - <<'PY'
from setuptools_scm import get_version
print(
    get_version(
        root=".",
        fallback_version="0.0.0",
        tag_regex=r"^v(?P<version>\d+\.\d+\.\d+)$",
        git_describe_command="git describe --dirty --tags --long --match v[0-9]*",
    )
)
PY
)

if [[ -z "$version" ]]; then
    echo "Could not determine version from package metadata" >&2
    exit 1
fi

mkdir -p "$PROJECT_DIR/dist/deb"

# Patch homebridge plugin version to match the package version (x.y.z only)
plugin_pkg="$PROJECT_DIR/homebridge-sleep-manager/package.json"
semver="${version%%[^0-9.]*}"  # strip dev/dirty suffix, keep x.y.z
plugin_pkg_orig=$(cat "$plugin_pkg")
cleanup_plugin_pkg() { echo "$plugin_pkg_orig" > "$plugin_pkg"; }
trap cleanup_plugin_pkg EXIT
sed -i "s/\"version\": \"[^\"]*\"/\"version\": \"$semver\"/" "$plugin_pkg"

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

built_deb=$(find "$PROJECT_DIR/.." -maxdepth 1 -type f -name "sleep-manager_${version}_all.deb" -print 2>/dev/null | head -n1 || true)
if [[ -z "$built_deb" ]]; then
    echo "Could not find built .deb in parent directory" >&2
    exit 1
fi

cp "$built_deb" "$PROJECT_DIR/dist/deb/"

echo "Built: $PROJECT_DIR/dist/deb/$(basename "$built_deb")"
