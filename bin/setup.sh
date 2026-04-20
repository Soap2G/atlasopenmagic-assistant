#!/usr/bin/env bash
#
# open-data-assistant setup script.
#
# Sources idempotently, works from any CWD once sourced.
# Usage (local dev):
#   source ./bin/setup.sh
#
# Usage (CVMFS, once published):
#   source /cvmfs/<repo>/<path>/latest/bin/setup.sh
#
# Effect:
#   - exports OPENCODE_CONFIG_DIR pointing at this tree's config/
#   - exports OPENCODE_DISABLE_PROJECT_CONFIG=1 so opencode ignores any
#     .opencode/ dir walked up from CWD. Comment out the line below if
#     you want project-local config to still layer on top.
#   - exports OPEN_DATA_ASSISTANT_VERSION from the VERSION file.

# Resolve the directory this script lives in, handling symlinks.
_oda_src="${BASH_SOURCE[0]:-$0}"
while [ -L "$_oda_src" ]; do
  _oda_dir="$(cd -P "$(dirname "$_oda_src")" >/dev/null 2>&1 && pwd)"
  _oda_src="$(readlink "$_oda_src")"
  [[ "$_oda_src" != /* ]] && _oda_src="$_oda_dir/$_oda_src"
done
_oda_bin="$(cd -P "$(dirname "$_oda_src")" >/dev/null 2>&1 && pwd)"
_oda_root="$(cd -P "$_oda_bin/.." >/dev/null 2>&1 && pwd)"
_oda_config="$_oda_root/config"

if [ ! -d "$_oda_config" ]; then
  echo "ERROR: open-data-assistant config not found at $_oda_config" >&2
  unset _oda_src _oda_dir _oda_bin _oda_root _oda_config
  return 1 2>/dev/null || exit 1
fi

export OPENCODE_CONFIG_DIR="$_oda_config"

# Comment the next line out to keep project .opencode/ layering on top.
export OPENCODE_DISABLE_PROJECT_CONFIG=1

if [ -f "$_oda_root/VERSION" ]; then
  OPEN_DATA_ASSISTANT_VERSION="$(cat "$_oda_root/VERSION")"
else
  OPEN_DATA_ASSISTANT_VERSION="unknown"
fi
export OPEN_DATA_ASSISTANT_VERSION

echo "open-data-assistant v${OPEN_DATA_ASSISTANT_VERSION} ready"
echo "  OPENCODE_CONFIG_DIR=$OPENCODE_CONFIG_DIR"
echo "  OPENCODE_DISABLE_PROJECT_CONFIG=$OPENCODE_DISABLE_PROJECT_CONFIG"

unset _oda_src _oda_dir _oda_bin _oda_root _oda_config
