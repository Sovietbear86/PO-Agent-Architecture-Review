"""Read-only local SberProject adapter built on the existing ``sbt-project`` skill CLI.

Design (A230R3.41)
------------------
Instead of a second, independent authentication mechanism (a service-account
OIDC client), this adapter reuses the **official, already-approved** skill's
authorization. The skill keeps its token in the OS keychain and performs its
own silent ``refresh_token`` / auto-reauth internally. This adapter only:

* invokes the official CLI (``sbt-project.sh``) as a bounded subprocess, and
* parses its machine-readable JSON output.

It **never reads, copies, or logs** the token or any password, and it adds no
second auth mechanism. TLS stays ON: the skill verifies its own certificates,
and an operator-supplied corporate CA bundle (``SBERPROJECT_CA_BUNDLE``) is
forwarded as ``NODE_EXTRA_CA_CERTS`` — a *trust addition*, never a verification
bypass. If the host does not trust the corporate CA (self-signed-in-chain), the
skill fails and this adapter reports a typed ``sberproject_source_unavailable``;
verification is never disabled to work around it.

Disabled by default. Fail-closed with the same typed reason codes as the facade
(``app/routers/sberproject_read.py``).
"""
from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass

# --- Reason codes (shared verbatim with app.routers.sberproject_read) -------
REASON_AUTH = "sberproject_auth_required"
REASON_UNAVAILABLE = "sberproject_source_unavailable"
REASON_INCOMPLETE = "sberproject_incomplete"
REASON_PAGINATION = "sberproject_pagination_unknown"
REASON_INVALID_PRODUCT = "invalid_product"

_VALID_PRODUCTS = ("OLP", "DMS")
_MAX_ROWS = 20
_MAX_OFFSET = 500
_DEFAULT_TIMEOUT = 30.0

# Skill CLI error codes (from sbt-project.js): EXIT = {AUTH:2, API:4, ...};
# ERROR_CODES = {AUTH_REQUIRED, AUTH_EXPIRED, AUTH_FAILED, API_ERROR, ...}
_AUTH_ERROR_CODES = {"AUTH_REQUIRED", "AUTH_EXPIRED", "AUTH_FAILED"}
_AUTH_EXIT_CODE = 2

# Repo-relative location of the skill launcher.
_SKILL_MARKER = os.path.join(".gigacode", "skills", "sbt-project", "sbt-project.sh")


class SkillBridgeError(Exception):
    """Typed, fail-closed failure carrying a stable reason code for the facade."""

    def __init__(self, reason: str, hint: str | None = None) -> None:
        super().__init__(reason)
        self.reason = reason
        self.hint = hint


def _resolve_skill_cmd() -> str:
    explicit = os.environ.get("SBERPROJECT_SKILL_CMD", "").strip()
    if explicit:
        return explicit
    here = os.path.abspath(__file__)
    # task-api/app/services/sberproject/skill_bridge.py -> repo root (5 levels up)
    for _ in range(5):
        here = os.path.dirname(here)
    return os.path.join(here, _SKILL_MARKER)


@dataclass
class SkillBridgeConfig:
    """Operator configuration. No secrets are stored here; the skill owns its
    own credentials in the OS keychain and this config only references the CLI."""

    enabled: bool
    skill_cmd: str
    ca_bundle: str
    timeout: float

    @classmethod
    def from_env(cls, env: "os._Environ | dict") -> "SkillBridgeConfig":
        def get(name: str, default: str = "") -> str:
            val = env.get(name, "")
            return val.strip() if isinstance(val, str) else str(val)

        enabled = get("SBERPROJECT_SKILL_BRIDGE_ENABLED").lower() in {"1", "true", "yes", "on"}
        try:
            timeout = float(get("SBERPROJECT_SKILL_TIMEOUT") or str(_DEFAULT_TIMEOUT))
        except ValueError:
            timeout = _DEFAULT_TIMEOUT
        return cls(
            enabled=enabled,
            skill_cmd=_resolve_skill_cmd(),
            ca_bundle=get("SBERPROJECT_CA_BUNDLE"),
            timeout=timeout,
        )


def _run_skill(skill_cmd: str, args: list[str], timeout: float, ca_bundle: str) -> tuple[int, str, str]:
    """Run the official skill CLI. Bounded. Never touches the keychain itself;
    the skill manages its own auth. Returns (exit_code, stdout, stderr)."""
    env = dict(os.environ)
    if ca_bundle:
        # Trust-add the corporate CA chain. TLS verification remains ON (this is
        # an added trusted root, not `NODE_TLS_REJECT_UNAUTHORIZED=0`).
        env["NODE_EXTRA_CA_CERTS"] = ca_bundle
    cwd = os.path.dirname(skill_cmd)
    try:
        proc = subprocess.run(
            [skill_cmd, *args],
            capture_output=True, text=True, timeout=timeout, env=env, cwd=cwd, check=False,
        )
    except subprocess.TimeoutExpired:
        raise SkillBridgeError(REASON_UNAVAILABLE, "skill CLI timed out") from None
    except (OSError, FileNotFoundError):
        raise SkillBridgeError(REASON_UNAVAILABLE, "skill CLI unavailable") from None
    return proc.returncode, (proc.stdout or ""), (proc.stderr or "")


def _read_json(stdout: str) -> object | None:
    try:
        return json.loads(stdout)
    except (ValueError, TypeError):
        return None


def _map_row(item: object) -> dict | None:
    """Map one skill ``versions`` row to the facade's scalar-only DTO. Rows
    lacking a usable id + versionNumber are dropped (not fabricated)."""
    if not isinstance(item, dict):
        return None
    rid = item.get("id")
    version = item.get("versionNumber")
    if not isinstance(rid, str) or not rid:
        return None
    if not isinstance(version, str) or not version:
        return None
    return {
        "id": rid,
        "versionId": rid,
        "versionNumber": version,
        "workflowStatus": item.get("status"),
        "beginDate": item.get("beginDate"),
        "endDate": item.get("endDate"),
        # Not exposed by the CLI's versions projection; not invented.
        "releaseDate": None,
        "owner": item.get("owner"),
    }


def versions(product: str, limit: int, offset: int, cfg: SkillBridgeConfig) -> dict:
    """Return ``{"results": [...], "meta": {has_more, total, next_offset}}`` in the
    exact shape consumed by the facade ``_catalog_response``."""
    if product not in _VALID_PRODUCTS:
        raise SkillBridgeError(REASON_INVALID_PRODUCT)
    if not 1 <= limit <= _MAX_ROWS:
        raise SkillBridgeError(REASON_INCOMPLETE, "limit out of bounds")
    if not 0 <= offset <= _MAX_OFFSET:
        raise SkillBridgeError(REASON_INCOMPLETE, "offset out of bounds")
    # The CLI's productVersionListByPage call is fixed to offset 0 and cannot
    # reliably serve deeper pages. Fail closed rather than return the wrong page.
    if offset != 0:
        raise SkillBridgeError(REASON_PAGINATION, "skill CLI cannot page beyond offset 0")

    # A missing CLI surfaces as a subprocess FileNotFoundError -> source_unavailable
    # in _run_skill, so no separate pre-check is needed here.
    code, out, _ = _run_skill(cfg.skill_cmd, ["versions", product, "--max-results", str(limit)],
                              cfg.timeout, cfg.ca_bundle)
    data = _read_json(out)
    if code != 0:
        # Distinguish an auth/permission failure from a network/source failure.
        error_code = None
        if isinstance(data, dict) and isinstance(data.get("error"), dict):
            error_code = data["error"].get("code")
        if error_code in _AUTH_ERROR_CODES or code == _AUTH_EXIT_CODE:
            raise SkillBridgeError(REASON_AUTH, "skill reports missing/invalid SberProject auth")
        raise SkillBridgeError(REASON_UNAVAILABLE, "skill could not reach the SberProject source")
    if not isinstance(data, dict):
        raise SkillBridgeError(REASON_INCOMPLETE)
    meta = data.get("meta")
    if isinstance(meta, dict) and meta.get("error"):
        error_code = (data.get("error") or {}).get("code")
        if error_code in _AUTH_ERROR_CODES:
            raise SkillBridgeError(REASON_AUTH)
        raise SkillBridgeError(REASON_UNAVAILABLE)
    results = data.get("results")
    if not isinstance(results, list):
        raise SkillBridgeError(REASON_INCOMPLETE)
    if len(results) > limit:
        raise SkillBridgeError(REASON_INCOMPLETE, "source returned more than the bounded page")

    rows = [r for r in (_map_row(x) for x in results) if r is not None]

    meta = data.get("meta") if isinstance(data.get("meta"), dict) else {}
    total = meta.get("total")
    total_int = total if isinstance(total, int) and not isinstance(total, bool) else None
    has_more = meta.get("has_more")
    if not isinstance(has_more, bool):
        if total_int is not None:
            has_more = total_int > len(rows)
        else:
            raise SkillBridgeError(REASON_PAGINATION, "source did not confirm a total")
    # The CLI cannot serve page 2, so the next page is never confirmable: report
    # it honestly as "has more, next page not confirmed" rather than truncation.
    return {
        "results": rows,
        "meta": {"has_more": has_more, "total": total_int, "next_offset": None},
    }
