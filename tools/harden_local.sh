#!/bin/sh
# Local-only, immutable input snapshot. Does not install tools or publish files.
set -eu
pio_root=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
cd "$pio_root"
pio_tag=${1:-$(date +%Y%m%d-%H%M%S)}
case "$pio_tag" in ''|*[!a-zA-Z0-9_-]*) echo 'Use an alphanumeric run name.' >&2; exit 2;; esac
pio_run="work/hardening-$pio_tag"
test ! -e "$pio_run" || { echo 'Run already exists; choose a new name.' >&2; exit 2; }
test -x work/eda-venv/bin/python
test -d work/pdk/ihp-sg13g2
PATH="$pio_root/work/eda-venv/bin:$PATH"
export PATH
work/eda-venv/bin/python tt/tt_tool.py --ihp --create-user-config
mkdir -p "$pio_run/src" "$pio_run/run"
cp src/*.v src/*.json src/*.tcl src/*.sdc "$pio_run/src/"
cp info.yaml "$pio_run/"
ln -s ../../tt "$pio_run/tt"
git rev-parse HEAD >"$pio_run/base-commit.txt"
git diff --binary HEAD >"$pio_run/tracked-changes.patch"
shasum -a 256 "$pio_run"/src/* "$pio_run/info.yaml" >"$pio_run/inputs.sha256"
pio_image=ghcr.io/librelane/librelane@sha256:ecabd075d0ddf6a2bd1cd4a32109c7dbb861ec007f7e4e423a9a081f8d23b8e2
docker image inspect "$pio_image" --format '{{json .RepoDigests}}' >"$pio_run/image-digest.json"
pio_exit=0
docker run --rm -v "$pio_root:/project" -w "/project/$pio_run" \
  -e PDK_ROOT=/project/work/pdk "$pio_image" librelane \
  --manual-pdk --pdk ihp-sg13g2 --pdk-root /project/work/pdk \
  --run-tag "$pio_tag" --force-run-dir "/project/$pio_run/run" \
  --hide-progress-bar -j 6 src/config_merged.json >"$pio_run/flow.log" 2>&1 || pio_exit=$?
printf '%s\n' "$pio_exit" >"$pio_run/exit-code.txt"
echo "Local report: $pio_run/flow.log (exit $pio_exit)"
exit "$pio_exit"
