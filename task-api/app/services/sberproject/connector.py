"""Read-only SberProject connector: minimal maintainable HTTPS adapter.

Satisfies the ``SBERPROJECT_CATALOG_READ_URL`` contract consumed by
``app.routers.sberproject_read``. Disabled by default; requires an operator-
approved confidential OIDC service identity and corporate CA before it will
return real data. Reuses the single registered SberProject GraphQL operation
``productVersionListByPage`` byte-for-byte (see ``REGISTERED_QUERY_SHA256``);
it does not invent any operation, hash, secret, or domain fallback.

Security invariants (spec A230R3.39):
- No personal GigaCode token / browser cookie / keychain / password reuse.
- Credentials (client secret) come from the process environment, injected by an
  approved runtime secret provider; never logged, never committed, never from
  a browser or shared keychain.
- TLS verification is always ON. A corporate CA bundle may be supplied via
  ``SBERPROJECT_CA_BUNDLE``; verification is never disabled.
- Read-only, OLP/DMS only, bounded (<=20 rows/page). No issueKey/percentDone.
"""
from __future__ import annotations

import hashlib
import os
import time
from dataclasses import dataclass
from urllib.parse import urlsplit

import httpx
from fastapi import FastAPI, HTTPException, Query

# --- Reason codes (shared verbatim with app.routers.sberproject_read) ------
REASON_AUTH = "sberproject_auth_required"
REASON_UNAVAILABLE = "sberproject_source_unavailable"
REASON_INCOMPLETE = "sberproject_incomplete"
REASON_OVER_LIMIT = "sberproject_page_over_limit"
REASON_PAGINATION = "sberproject_pagination_unknown"
REASON_INVALID_PRODUCT = "invalid_product"

_VALID_PRODUCTS = ("OLP", "DMS")
_MAX_ROWS = 20
_MAX_OFFSET = 500

# The single already-registered SberProject operation, byte-identical to the
# local skill's PRODUCT_VERSION_LIST_QUERY. Its sha256 is locked in tests so any
# accidental edit to this operation fails CI.
REGISTERED_QUERY = """query productVersionListByPage($sort: [_SortCriterionSpecification!], $limit: Int, $offset: Int, $searchCond: String) {
  searchProductVersion(
    cond: $searchCond
    sort: $sort
    limit: $limit
    offset: $offset
  ) {
    count
    elems {
      ...ProductVersionListAttributes
      ... on _E_ProductVersionAlfa {
        isAlfa
        __typename
      }
      ... on _E_ProductVersionBeta {
        isBeta
        __typename
      }
      ... on _E_ProductVersionPatch {
        isPatch
        __typename
      }
      __typename
    }
    __typename
  }
}

fragment ProductVersionListAttributes on ProductVersion {
  ...ProductVersionAttributes
  product {
    entity {
      id
      productType
      solutionType
      name
      __typename
    }
    __typename
  }
  structUnit {
    entity {
      id
      name
      __typename
    }
    __typename
  }
  owner {
    entity {
      name
      personnelNumber
      id
      __typename
    }
    __typename
  }
  isPatch
  manager: members(cond: "it.projectRole.entityId == 'MANAGER'") {
    elems {
      id
      subject {
        entityId
        entity {
          name
          __typename
        }
        __typename
      }
      roles {
        elems
        __typename
      }
      __typename
    }
    __typename
  }
  architect: members(cond: "it.projectRole.entityId == 'ARCHITECT'") {
    elems {
      id
      subject {
        entityId
        entity {
          name
          __typename
        }
        __typename
      }
      roles {
        elems
        __typename
      }
      __typename
    }
    __typename
  }
  tags {
    elems {
      reference {
        entity {
          ...TagAttributes
          __typename
        }
        __typename
      }
      __typename
    }
    __typename
  }
  installationName {
    entityId
    __typename
  }
  __typename
}

fragment ProductVersionAttributes on ProductVersion {
  id
  description
  name
  type
  beginDate
  endDate
  currency
  workflow {
    id
    __typename
  }
  workflowStatus {
    id
    code
    name
    label
    __typename
  }
  testingEndDateIFT
  testingEndDateNT
  developEndDate
  acceptanceStartDate
  acceptanceEndDate
  transferDate
  releaseDate
  outputDate
  installationDate
  factEndDate
  fixDate
  distributionLink
  isMajorVersion
  isLTS
  versionNumber
  lastModifyDate
  lastModifyUser
  isInBundle
  isPatch
  needInstallation
  productVersion {
    id
    versionNumber
    name
    __typename
  }
  isAutoCreated
  __typename
}

fragment TagAttributes on _E_Tag {
  id
  __typename
  name
  description
}"""
OPERATION_NAME = "productVersionListByPage"
REGISTERED_QUERY_SHA256 = hashlib.sha256(REGISTERED_QUERY.encode("utf-8")).hexdigest()

# Canonical base URL / realm / tenant for the SberProject deployment. The base
# URL is operator-overridable but must stay HTTPS with no embedded credentials.
_DEFAULT_BASE_URL = "https://project.sbertech.ru"
_DEFAULT_REALM = "SberProject"
_DEFAULT_TENANT = "SBT-TNT"


class _FailClosed(Exception):
    """Internal: convert to a typed HTTPException with a stable reason code."""

    def __init__(self, status: int, reason: str) -> None:
        super().__init__(reason)
        self.status = status
        self.reason = reason


def _fail(status: int, reason: str) -> None:
    raise _FailClosed(status, reason)


@dataclass
class ConnectorConfig:
    """Operator configuration. Secret value (client secret) is read from the
    environment and never stored on the object beyond the token provider."""

    enabled: bool
    base_url: str
    realm: str
    tenant: str
    client_id: str
    ca_bundle: str
    timeout: float

    @classmethod
    def from_env(cls, env: "os._Environ" | dict) -> "ConnectorConfig":
        def get(name: str, default: str = "") -> str:
            val = env.get(name, "")
            return val.strip() if isinstance(val, str) else str(val)

        base = get("SBERPROJECT_BASE_URL") or _DEFAULT_BASE_URL
        realm = get("SBERPROJECT_REALM") or _DEFAULT_REALM
        tenant = get("SBERPROJECT_TENANT") or _DEFAULT_TENANT
        ca = get("SBERPROJECT_CA_BUNDLE")
        try:
            timeout = float(get("SBERPROJECT_TIMEOUT") or "20")
        except ValueError:
            timeout = 20.0
        return cls(
            enabled=_truthy(get("SBERPROJECT_CONNECTOR_ENABLED")),
            base_url=base,
            realm=realm,
            tenant=tenant,
            client_id=get("SBERPROJECT_CLIENT_ID"),
            ca_bundle=ca,
            timeout=timeout,
        )


def _truthy(v: str) -> bool:
    return v.strip().lower() in {"1", "true", "yes", "on"}


def _validate_base_url(base: str) -> None:
    parsed = urlsplit(base)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.fragment:
        _fail(503, REASON_UNAVAILABLE)


class TokenProvider:
    """Client-credentials OIDC token acquisition with in-memory cache + renewal.

    Modular: only the SberProject Keycloak realm is targeted. A 401/403 on a data
    call forces a one-time refresh. If no client secret is provisioned it fails
    closed with the auth reason (never fabricates a token).
    """

    _RENEW_BUFFER = 60  # seconds before expiry to proactively renew

    def __init__(self, config: ConnectorConfig, client_secret: str, client: httpx.AsyncClient) -> None:
        self._config = config
        self._client_secret = client_secret
        self._http = client
        self._token: str | None = None
        self._expires_at: float = 0.0

    @property
    def token_endpoint(self) -> str:
        return f"{self._config.base_url}/auth/realms/{self._config.realm}/protocol/openid-connect/token"

    def _is_valid(self) -> bool:
        return bool(self._token) and time.time() < (self._expires_at - self._RENEW_BUFFER)

    async def get_token(self, force: bool = False) -> str:
        if not force and self._is_valid():
            assert self._token is not None
            return self._token
        if not self._client_secret:
            _fail(503, REASON_AUTH)
        resp = await self._http.post(
            self.token_endpoint,
            data={
                "grant_type": "client_credentials",
                "client_id": self._config.client_id,
                "client_secret": self._client_secret,
            },
            headers={"Accept": "application/json"},
        )
        if resp.status_code != 200:
            _fail(503, REASON_AUTH)
        try:
            payload = resp.json()
        except ValueError:
            _fail(502, REASON_INCOMPLETE)
        token = payload.get("access_token")
        if not isinstance(token, str) or not token:
            _fail(502, REASON_INCOMPLETE)
        try:
            expires_in = int(payload.get("expires_in", 300))
        except (TypeError, ValueError):
            expires_in = 300
        self._token = token
        self._expires_at = time.time() + max(expires_in, 0)
        return token


def _owner_name(owner: object) -> str | None:
    if isinstance(owner, dict):
        entity = owner.get("entity")
        if isinstance(entity, dict):
            name = entity.get("name")
            if isinstance(name, str) and name:
                return name
    return None


def _role_name(members: object) -> str | None:
    if isinstance(members, dict):
        elems = members.get("elems")
        if isinstance(elems, list):
            for e in elems:
                if isinstance(e, dict):
                    subject = e.get("subject")
                    if isinstance(subject, dict):
                        entity = subject.get("entity")
                        if isinstance(entity, dict):
                            name = entity.get("name")
                            if isinstance(name, str) and name:
                                return name
    return None


def _normalize_element(elem: object) -> dict:
    if not isinstance(elem, dict):
        _fail(502, REASON_INCOMPLETE)
    code = elem.get("id")
    if not isinstance(code, str) or not code:
        _fail(502, REASON_INCOMPLETE)
    version = elem.get("versionNumber")
    if not isinstance(version, str) or not version:
        _fail(502, REASON_INCOMPLETE)
    ws = elem.get("workflowStatus")
    ws_code = ws.get("code") if isinstance(ws, dict) else None
    row = {
        "id": code,
        "versionId": code,
        "versionNumber": version,
        "workflowStatus": ws_code if isinstance(ws_code, str) else None,
    }
    for key in ("beginDate", "endDate", "releaseDate"):
        val = elem.get(key)
        row[key] = val if isinstance(val, (str, type(None))) else None
    row["owner"] = _owner_name(elem.get("owner"))
    row["manager"] = _role_name(elem.get("manager"))
    row["architect"] = _role_name(elem.get("architect"))
    return row


class SberProjectClient:
    def __init__(self, config: ConnectorConfig, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self._config = config
        self._transport = transport
        # TLS verification is always ON: use the operator CA bundle when given,
        # otherwise the system trust store. Never disabled.
        self._verify = config.ca_bundle if config.ca_bundle else True

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            verify=self._verify,
            timeout=self._config.timeout,
            follow_redirects=False,
            transport=self._transport,
        )

    def _graphqL_url(self) -> str:
        return f"{self._config.base_url}/api/v1/dataspace/graphql/graphql-{OPERATION_NAME}"

    async def versions(self, product: str, limit: int, offset: int) -> dict:
        async with self._client() as http:
            tokens = TokenProvider(
                self._config,
                os.environ.get("SBERPROJECT_CLIENT_SECRET", "").strip(),
                http,
            )
            token = await tokens.get_token()
            body = {
                "operationName": OPERATION_NAME,
                "query": REGISTERED_QUERY,
                "variables": {
                    "searchCond": f"(it.product.entityId=='{product}')",
                    "sort": [{"crit": "it.$id", "order": "DESC"}],
                    "limit": limit,
                    "offset": offset,
                },
            }
            headers = {
                "x-operation-name": OPERATION_NAME,
                "Authorization": f"Bearer {token}",
                "x-dspc-tenant": self._config.tenant,
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
            resp = await http.post(self._graphqL_url(), json=body, headers=headers)
            if resp.status_code in (401, 403):
                # One bounded token refresh + retry, then fail closed.
                token = await tokens.get_token(force=True)
                headers["Authorization"] = f"Bearer {token}"
                resp = await http.post(self._graphqL_url(), json=body, headers=headers)
            if resp.status_code == 401 or resp.status_code == 403:
                _fail(503, REASON_AUTH)
            if resp.status_code != 200:
                _fail(503, REASON_UNAVAILABLE)
            try:
                envelope = resp.json()
            except ValueError:
                _fail(502, REASON_INCOMPLETE)
            return self._normalize(envelope, limit, offset)

    def _normalize(self, envelope: object, limit: int, offset: int) -> dict:
        if not isinstance(envelope, dict) or not isinstance(envelope.get("data"), dict):
            _fail(502, REASON_INCOMPLETE)
        data = envelope["data"]
        # The registered operation selects the "searchProductVersion" field.
        result = data.get("searchProductVersion")
        if not isinstance(result, dict):
            _fail(502, REASON_INCOMPLETE)
        elems = result.get("elems")
        count = result.get("count")
        if not isinstance(elems, list):
            _fail(502, REASON_INCOMPLETE)
        if not isinstance(count, int) or isinstance(count, bool) or count < 0:
            _fail(502, REASON_PAGINATION)
        if len(elems) > limit:
            _fail(502, REASON_OVER_LIMIT)
        rows = [_normalize_element(e) for e in elems]
        has_more = (offset + limit) < count
        return {
            "results": rows,
            "meta": {
                "has_more": has_more,
                "total": count,
                "next_offset": (offset + limit) if has_more else None,
            },
        }


def create_app(
    config: "ConnectorConfig | None" = None,
    client_transport: httpx.AsyncBaseTransport | None = None,
) -> FastAPI:
    """Build the connector FastAPI app. When not explicitly enabled (or secret
    not provisioned) the endpoint fails closed with a typed auth/unavailable
    state — it never simulates a working source.

    ``client_transport`` is a test seam for controlled fixtures (httpx
    ``MockTransport``); production leaves it ``None``.
    """

    app = FastAPI(title="SberProject Catalog Connector", version="0.1.0")
    cfg = config if config is not None else ConnectorConfig.from_env(os.environ)

    @app.get("/health")
    async def health():
        return {
            "status": "ok",
            "enabled": cfg.enabled,
            "client_id_provisioned": bool(cfg.client_id),
        }

    @app.get("/versions")
    async def versions(
        product: str = Query(...),
        limit: int = Query(20, ge=1, le=_MAX_ROWS),
        offset: int = Query(0, ge=0, le=_MAX_OFFSET),
    ):
        product = product.strip().upper()
        if product not in _VALID_PRODUCTS:
            raise HTTPException(400, detail={"reason": REASON_INVALID_PRODUCT})
        if not cfg.enabled:
            raise HTTPException(503, detail={"reason": REASON_AUTH})
        if not cfg.client_id:
            raise HTTPException(503, detail={"reason": REASON_AUTH})
        try:
            _validate_base_url(cfg.base_url)
            client = SberProjectClient(cfg, transport=client_transport)
            return await client.versions(product, limit, offset)
        except _FailClosed as exc:
            raise HTTPException(exc.status, detail={"reason": exc.reason}) from None
        except httpx.TimeoutException:
            raise HTTPException(503, detail={"reason": REASON_UNAVAILABLE}) from None
        except httpx.TransportError:
            raise HTTPException(503, detail={"reason": REASON_UNAVAILABLE}) from None

    return app


def main() -> FastAPI:
    return create_app()
