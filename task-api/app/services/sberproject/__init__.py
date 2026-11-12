"""Server-side read-only SberProject connector (A230R3.39).

A small, operator-configurable HTTPS service that satisfies the existing
``SBERPROJECT_CATALOG_READ_URL`` contract consumed by
``app.routers.sberproject_read``. It is **disabled by default** and only becomes
functional after SberTech IT/security provisions an approved confidential OIDC
service identity and corporate CA. It reuses the single already-registered
SberProject GraphQL operation ``productVersionListByPage`` byte-for-byte (no
invented operation/hash) and never handles a personal GigaCode token, browser
cookie, or password. TLS verification is always on.
"""
