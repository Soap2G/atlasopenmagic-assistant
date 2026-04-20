#!/usr/bin/env bash
#
# Stage (and optionally publish) the open-data-assistant config to CVMFS.
#
# Usage:
#   ./script/cvmfs-deploy.sh                                          # stage only (default)
#   ./script/cvmfs-deploy.sh --stage-only                             # stage only, explicit
#   ./script/cvmfs-deploy.sh --cvmfs-base /cvmfs/<repo>/<path> \
#                            --cvmfs-repo <repo>                      \
#                            --publish                                # publish
#
# No CVMFS path is baked in. Pass --cvmfs-base to name the target
# directory and --cvmfs-repo to name the CVMFS repository on which to
# run the transaction.
#
# Layout produced under dist/cvmfs-stage/ (and mirrored on CVMFS):
#   <VERSION>/
#     VERSION
#     bin/setup.sh
#     config/...       (OPENCODE_CONFIG_DIR target)
#     README.md
#   latest -> <VERSION>

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STAGE_DIR="${REPO_ROOT}/dist/cvmfs-stage"
PUBLISH=false
CVMFS_BASE=""
CVMFS_REPO=""

usage() {
  cat <<EOF
Usage: $0 [options]

  --cvmfs-base PATH   Target directory on CVMFS, e.g.
                        /cvmfs/sw.escape.eu/open-data-assistant
                        /cvmfs/atlas.cern.ch/repo/sw/open-data-assistant
  --cvmfs-repo NAME   CVMFS repository name for cvmfs_server, e.g.
                        sw.escape.eu
                        atlas.cern.ch
  --publish           Run cvmfs_server transaction + rsync + publish
                      (requires --cvmfs-base and --cvmfs-repo)
  --stage-only        (default) Only stage locally under dist/cvmfs-stage
  -h, --help          Show this help
EOF
}

while (( $# > 0 )); do
  case "$1" in
    --cvmfs-base) CVMFS_BASE="$2"; shift 2 ;;
    --cvmfs-repo) CVMFS_REPO="$2"; shift 2 ;;
    --publish)    PUBLISH=true; shift ;;
    --stage-only) PUBLISH=false; shift ;;
    -h|--help)    usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage >&2; exit 1 ;;
  esac
done

if [ ! -f "${REPO_ROOT}/VERSION" ]; then
  echo "ERROR: ${REPO_ROOT}/VERSION is missing" >&2
  exit 1
fi

VERSION="$(cat "${REPO_ROOT}/VERSION" | tr -d '[:space:]')"
DEST="${STAGE_DIR}/${VERSION}"

echo "==> Staging open-data-assistant v${VERSION}"
rm -rf "${DEST}"
mkdir -p "${DEST}"

# Copy the release payload only. Exclude dev-only files.
rsync -a \
  --exclude '.git' \
  --exclude 'dist' \
  --exclude '.gitignore' \
  --exclude '.DS_Store' \
  --exclude 'script/cvmfs-deploy.sh' \
  "${REPO_ROOT}/" "${DEST}/"

# Ensure the entrypoint is executable.
chmod +x "${DEST}/bin/setup.sh"

# Maintain a "latest" symlink alongside the versioned tree.
ln -sfn "${VERSION}" "${STAGE_DIR}/latest"

echo "==> Staged at ${DEST}"
echo "    ${DEST}/config/      (OPENCODE_CONFIG_DIR target)"
echo "    ${DEST}/bin/setup.sh (users source this)"
echo "    ${STAGE_DIR}/latest  -> ${VERSION}"

if [ "$PUBLISH" != true ]; then
  cat <<EOF

==> Dry run complete. To publish:
    1. Copy ${STAGE_DIR}/ to a machine with CVMFS publisher access, OR
       rerun this script on the publisher node.
    2. Invoke:
         $0 --cvmfs-base /cvmfs/<repo>/<path> \\
             --cvmfs-repo <repo> --publish
EOF
  exit 0
fi

# ---------------------------------------------------------------------------
# Publish path
# ---------------------------------------------------------------------------
if [ -z "$CVMFS_BASE" ] || [ -z "$CVMFS_REPO" ]; then
  echo "ERROR: --publish requires both --cvmfs-base and --cvmfs-repo" >&2
  exit 1
fi

if ! command -v cvmfs_server >/dev/null 2>&1; then
  echo "ERROR: cvmfs_server not in PATH. Run --publish on a CVMFS publisher node." >&2
  exit 1
fi

echo "==> Publishing to ${CVMFS_BASE} on CVMFS repo ${CVMFS_REPO}"

cvmfs_server transaction "${CVMFS_REPO}"

mkdir -p "${CVMFS_BASE}"
rsync -a --delete "${STAGE_DIR}/" "${CVMFS_BASE}/"

cvmfs_server publish "${CVMFS_REPO}"

echo "==> Published open-data-assistant v${VERSION} to ${CVMFS_BASE}"
echo "    Users can now run:"
echo "      source ${CVMFS_BASE}/latest/bin/setup.sh"
