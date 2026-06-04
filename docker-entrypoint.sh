#!/bin/sh
set -e

# ============================================================================
# FastBlog Docker Entrypoint
# Creates missing runtime directories, then drops to appuser.
#
# Permission strategy:
#   - All writable directories use Docker named volumes, which inherit
#     ownership from the image layer (appuser:appuser). No chown needed.
#   - This script only creates directories that might be missing at runtime
#     (e.g., new directories added in code updates not yet in the volume).
#
# Usage in docker-compose:
#   entrypoint: ["/docker-entrypoint.sh"]
#   # No user directive needed — script runs as root (Dockerfile has no USER),
#   # then drops to appuser via gosu.
# ============================================================================

echo "[entrypoint] Ensuring runtime directories exist..."

# Runtime directories the application may need
RUNTIME_DIRS="
/app/static_generated
/app/plugins_data
/app/plugins
/app/storage
/app/storage/cache
/app/storage/objects
/app/storage/thumbnails
/app/storage/subscriptions
/app/storage/critical-css
/app/backups
/app/backups/automated
/app/logs
/app/media
/app/uploads
/app/upload_chunks
/app/translations
/app/config
/app/temp
/app/temp/search
/app/custom-patterns
/app/static
/app/static/uploads
/app/static/uploads/mobile
/app/static/uploads/covers
"

# Create missing directories and ensure correct ownership for all.
# Named volumes may inherit root:root if initialized from empty image dirs,
# so we must unconditionally chown every listed directory.
for dir in $RUNTIME_DIRS; do
    [ -z "$dir" ] && continue
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        echo "[entrypoint] Created: $dir"
    fi
    chown appuser:appuser "$dir"
done

echo "[entrypoint] Dropping to appuser and starting application..."

# Drop privileges and execute the original CMD
if command -v gosu >/dev/null 2>&1; then
    exec tini -- gosu appuser "$@"
else
    exec tini -- runuser -u appuser -- "$@"
fi
