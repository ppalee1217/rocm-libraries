#!/usr/bin/env bash
# One-time (idempotent) provisioning inside the `perlee` container. Run as root
# via run.sh. Sets up: the perlee user, node v24, Claude Code + Cursor agent
# CLIs, auto-approve wrappers, and an isolated agent config dir under /src.
#
# Safe to re-run: every step checks before acting.

set -euo pipefail

PERLEE_UID=1031
PERLEE_GID=1032
PERLEE_HOME=/home/perlee
CONF_DIR=/src/.agentconf/claude

echo "==> [1/7] ensure perlee group/user (uid=${PERLEE_UID} gid=${PERLEE_GID})"
if ! getent group "${PERLEE_GID}" >/dev/null; then
  groupadd -g "${PERLEE_GID}" perlee
fi
if ! id -u perlee >/dev/null 2>&1; then
  # -M: do not create/manage home (it is bind-mounted from the host).
  useradd -u "${PERLEE_UID}" -g "${PERLEE_GID}" -d "${PERLEE_HOME}" -M -s /bin/bash perlee
fi
# GPU access groups (video=44 owns /dev/kfd, render=110 owns renderD*).
# The base image may lack a `render` group entry; create it at gid 110 so
# membership has a name (cosmetic) and matches the host.
getent group 110 >/dev/null || groupadd -g 110 render
for g in video render; do
  getent group "$g" >/dev/null && usermod -aG "$g" perlee || true
done
# The container's /home/perlee dir is root-owned (only .cursor / .claude.json are
# bind-mounted into it). chown the dir itself (NON-recursive, so mounted subdirs
# and their host files are untouched) so perlee can create ~/.local etc.
mkdir -p "${PERLEE_HOME}"
chown "${PERLEE_UID}:${PERLEE_GID}" "${PERLEE_HOME}"
install -d -o "${PERLEE_UID}" -g "${PERLEE_GID}" "${PERLEE_HOME}/.local" "${PERLEE_HOME}/.local/bin"

echo "==> [2/7] install node v24 (NodeSource) if missing"
if ! command -v node >/dev/null 2>&1; then
  curl -fsSL https://deb.nodesource.com/setup_24.x | bash -
  DEBIAN_FRONTEND=noninteractive apt-get install -y nodejs
fi
echo "    node $(node -v), npm $(npm -v)"

echo "==> [3/7] install Claude Code CLI if missing"
if ! npm ls -g --depth=0 @anthropic-ai/claude-code >/dev/null 2>&1; then
  npm install -g @anthropic-ai/claude-code
fi
# Target the npm-installed bin shim DIRECTLY (npm prefix -g => /usr). Do NOT use
# `command -v claude`: our /usr/local/bin/claude wrapper shadows it and would make
# the wrapper exec itself (infinite loop).
CLAUDE_BIN="$(npm prefix -g)/bin/claude"

echo "==> [4/8] install Cursor agent CLI if missing"
# Check the real install path, NOT `command -v` — our /usr/local/bin wrapper
# would otherwise short-circuit this and skip the install.
CURSOR_BIN="${PERLEE_HOME}/.local/bin/cursor-agent"
if [ ! -e "${CURSOR_BIN}" ]; then
  # Official installer; installs under the invoking user's home (~/.local/...).
  sudo -u perlee bash -lc 'curl https://cursor.com/install -fsS | bash' || \
    echo "    WARN: cursor-agent install failed; continue (Claude still set up)"
fi

echo "==> [5/8] install Codex CLI if missing"
# Claude Code drives Codex as an MCP subagent (repo .mcp.json runs `codex mcp-server`),
# so codex must be on PATH inside the container. Installed as an npm global, matching
# the host (@openai/codex). Codex auth (~/.codex) is bind-mounted by run.sh so the
# host login is reused; no separate auth step here.
if ! npm ls -g --depth=0 @openai/codex >/dev/null 2>&1; then
  npm install -g @openai/codex
fi
echo "    codex $("$(npm prefix -g)/bin/codex" --version 2>/dev/null || echo '(version unknown)')"

echo "==> [6/8] write auto-approve wrappers to /usr/local/bin (container-only)"
# Both wrappers guard against being run as root: the auto-approve flags
# (--dangerously-skip-permissions / --force) are refused under root, so instead
# of the cryptic upstream error we print how to re-enter as perlee.
ROOT_GUARD='if [ "$(id -u)" = "0" ]; then
  echo "[wrapper] 偵測到 root 身份，auto-approve 會被擋。" >&2
  echo "[wrapper] 請改用 perlee 進入容器：" >&2
  echo "    docker exec -it -u perlee -w /src/rocm-libraries perlee bash -l" >&2
  echo "  或直接執行： bash /src/rocm-libraries/run.sh" >&2
  exit 1
fi'

# Claude: always bypass permission prompts. Running as non-root perlee means
# --dangerously-skip-permissions does NOT require IS_SANDBOX.
cat > /usr/local/bin/claude <<EOF
#!/usr/bin/env bash
${ROOT_GUARD}
exec "${CLAUDE_BIN}" --dangerously-skip-permissions "\$@"
EOF
chmod 755 /usr/local/bin/claude

# Cursor agent: --force = "run everything unless explicitly denied" (its
# auto-approve); --approve-mcps auto-approves MCP servers too.
cat > /usr/local/bin/cursor-agent <<EOF
#!/usr/bin/env bash
${ROOT_GUARD}
exec "${CURSOR_BIN}" --force --approve-mcps "\$@"
EOF
chmod 755 /usr/local/bin/cursor-agent

echo "==> [7/8] isolated Claude config dir at ${CONF_DIR}"
mkdir -p "${CONF_DIR}"
# model: Claude-Opus-4.8 is the newest model the AMD gateway offers (1M context).
# Claude Code prints a false "Opus 4 retired" warning because it prefix-matches the
# gateway's non-standard id; the model is real and current. Pin it explicitly plus
# xhigh effort (matches the host preference). ANTHROPIC_MODEL env still wins at
# runtime; this keeps config self-consistent.
cat > "${CONF_DIR}/settings.json" <<'EOF'
{
  "permissions": {
    "defaultMode": "bypassPermissions"
  },
  "model": "Claude-Opus-4.8",
  "effortLevel": "xhigh"
}
EOF
chown -R "${PERLEE_UID}:${PERLEE_GID}" /src/.agentconf

echo "==> [8/8] container-only profile (PATH + CLAUDE_CONFIG_DIR)"
# Lives in /etc (not the bind-mounted home), so host is unaffected.
cat > /etc/profile.d/agent.sh <<EOF
export CLAUDE_CONFIG_DIR=${CONF_DIR}
export PATH="/usr/local/bin:${PERLEE_HOME}/.local/bin:\$PATH"
EOF
chmod 644 /etc/profile.d/agent.sh

echo "==> done. enter with: docker exec -it -u perlee perlee bash -l"
