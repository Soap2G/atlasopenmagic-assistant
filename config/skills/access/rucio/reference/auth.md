# Rucio authentication

Full details on how the Rucio CLI locates its config and picks up
credentials. Read this file when `rucio whoami` fails, when the user
is setting up Rucio off-CVMFS, or when you need to switch auth methods.

## Contents
- Config file search order
- Minimum `rucio.cfg`
- Credentials per `auth_type`
- Environment variables
- Auth-aware prerequisite check

## 1. Config file (`rucio.cfg`)

The CLI searches, in order:

1. `$RUCIO_CONFIG` (explicit path)
2. `$RUCIO_HOME/etc/rucio.cfg`
3. `$VIRTUAL_ENV/etc/rucio.cfg`
4. `/opt/rucio/etc/rucio.cfg`

The CVMFS setup sources a working `rucio.cfg` for you — sourcing
`/cvmfs/sw.escape.eu/rucio/38.3.0/setup-minimal.sh` sets `RUCIO_HOME`
so `etc/rucio.cfg` is picked up automatically. On lxplus the ATLAS
setup (`setupATLAS && lsetup rucio`) does the same.

Off-CVMFS you need to provide your own `rucio.cfg`. Minimum contents:

```ini
[client]
rucio_host = https://rucio-lb-prod.cern.ch
auth_host  = https://rucio-auth-prod.cern.ch
account    = <your-account>
auth_type  = x509_proxy     ; or: oidc, userpass, ssh
ca_cert    = /etc/pki/tls/certs/CERN-bundle.pem
```

Point `RUCIO_CONFIG` at it if it lives outside the standard search
paths.

## 2. Credentials (depend on `auth_type`)

| `auth_type`  | What you need besides `rucio.cfg`                     |
|--------------|-------------------------------------------------------|
| `x509_proxy` | a valid VOMS proxy at `$X509_USER_PROXY` (default `/tmp/x509up_u$(id -u)`) — created by `voms-proxy-init -voms atlas` |
| `oidc`       | nothing on disk; `rucio` drives the device-code flow in the browser, caches the token under `~/.rucio_oidc/` |
| `userpass`   | `username` and `password` in `rucio.cfg` — discouraged, only for service accounts |
| `ssh`        | the SSH key pair registered with Rucio (matches `~/.ssh/id_rsa` by default) |

Rule of thumb: **if `auth_type = x509_proxy`, you need both the config
and a live proxy**; for `oidc`/`userpass`/`ssh`, the config plus the
relevant credential is enough — no proxy required.

## 3. Environment variables

- `RUCIO_ACCOUNT` — overrides `[client] account` in the config; often
  the CERN username for ATLAS users, or a group account.
- `RUCIO_CONFIG` — explicit path to `rucio.cfg` (takes priority over
  `RUCIO_HOME`).
- `RUCIO_HOME` — root of a Rucio install; `etc/rucio.cfg` under it is
  loaded if `RUCIO_CONFIG` is unset.
- `RUCIO_AUTH_TYPE` — overrides `[client] auth_type` for a single run
  (e.g. `RUCIO_AUTH_TYPE=oidc rucio whoami`).
- `X509_USER_PROXY` — path to the VOMS proxy (only consulted when
  `auth_type = x509_proxy`). Normally set by `voms-proxy-init`.

## 4. Auth-aware prerequisite check

```bash
command -v rucio >/dev/null 2>&1 || { echo "rucio CLI not on PATH"; exit 1; }

# Pick the check that matches your auth_type:
case "${RUCIO_AUTH_TYPE:-$(awk -F= '/^[[:space:]]*auth_type/{gsub(/ /,"",$2);print $2}' \
        "${RUCIO_CONFIG:-$RUCIO_HOME/etc/rucio.cfg}" 2>/dev/null)}" in
  x509_proxy|"")
    voms-proxy-info -exists -valid 0:30 >/dev/null 2>&1 || {
      echo "No valid VOMS proxy. Run: voms-proxy-init -voms atlas"; exit 1; }
    ;;
  oidc)
    : # rucio will prompt / use cached OIDC token
    ;;
esac

rucio whoami
```

`rucio whoami` is the cheapest end-to-end check: it prints the
account, identity, and e-mail on the active token. If it fails, stop
and surface the error — do not try to run real queries.
