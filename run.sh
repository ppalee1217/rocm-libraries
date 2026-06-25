#!/usr/bin/env bash
# Enter the `perlee` dev container with the agent runtime (Claude Code + Cursor
# agent) installed INSIDE the container, running as the host uid (perlee) with
# auto-approve enabled. host config dirs are mounted for auth reuse; agent
# settings/state stay isolated under /src/.agentconf so host agents are unaffected.
#
# Idempotent: running it just drops you into the container.
#   - container already running -> attach immediately (no rebuild).
#   - container stopped         -> start it, then attach.
#   - container missing         -> create + provision (node + CLIs), then attach.
# Pass --rebuild to force a clean recreate from the image.

set -euo pipefail

IMAGE="registry-sc-harbor.amd.com/rocm-ci-images/compute-rocm-rel-7.2:93-ubuntu-24.04"
NAME="perlee"

# `docker inspect` state: "running" / "exited" / "" (no such container).
state="$(docker inspect -f '{{.State.Status}}' "${NAME}" 2>/dev/null || true)"

if [ "${1:-}" = "--rebuild" ]; then
  echo "==> --rebuild: removing existing ${NAME} container"
  docker rm -f "${NAME}" 2>/dev/null || true
  state=""
fi

provision=0
case "${state}" in
  running)
    echo "==> ${NAME} already running; attaching."
    ;;
  exited|created|paused)
    echo "==> ${NAME} exists (${state}); starting."
    docker start "${NAME}" >/dev/null
    ;;
  *)
    echo "==> ${NAME} not found; creating + provisioning."
    # Corporate DNS so the container can resolve the AMD-internal LLM gateway
    # (llm-api.amd.com); Docker's default 8.8.8.8 cannot. --add-host is a static
    # fallback in case the resolver IP changes.
    CORP_DNS="10.7.79.85"
    GATEWAY_HOSTS="$(getent hosts llm-api.amd.com | awk '{print $1; exit}')"

    docker run -it -d --device=/dev/kfd --device=/dev/dri \
                --security-opt seccomp=unconfined \
                --group-add 44 --group-add 110 \
                --dns "${CORP_DNS}" \
                ${GATEWAY_HOSTS:+--add-host "llm-api.amd.com:${GATEWAY_HOSTS}"} \
                -v /data1/perlee:/src \
                -v /home/perlee/.claude.json:/home/perlee/.claude.json \
                -v /home/perlee/.cursor:/home/perlee/.cursor \
                --name "${NAME}" \
                "$IMAGE"
    provision=1
    ;;
esac

# Provision only on a fresh create (the steps are idempotent, but skipping the
# node/CLI install on every attach is what saves the time).
if [ "${provision}" = "1" ]; then
  docker exec "${NAME}" bash /src/rocm-libraries/container-setup.sh
fi

# Refresh the Anthropic gateway auth every run (cheap). These live in the host
# ~/.bashrc (not mounted) and contain a subscription-key secret, so we copy them
# into the container fs (/etc/profile.d, NOT the mounted /src). Keeping it on
# every run means rotating the host key just needs a re-run.
AUTH_ENV="$(grep -E '^export ANTHROPIC_' /home/perlee/.bashrc || true)"
if [ -n "${AUTH_ENV}" ]; then
  printf '%s\n' "${AUTH_ENV}" | \
    docker exec -i "${NAME}" bash -c 'cat > /etc/profile.d/agent-auth.sh && chmod 644 /etc/profile.d/agent-auth.sh'
else
  echo "WARN: no ANTHROPIC_* exports found in /home/perlee/.bashrc — container claude may be unauthenticated"
fi

# Enter as the perlee user (uid 1031) so files written to /src stay perlee-owned
# on the host and auto-approve does not require root. -l = login shell so PATH +
# CLAUDE_CONFIG_DIR + auth are loaded.
docker exec -it -u perlee -w /src/rocm-libraries "${NAME}" /bin/bash -l
