Prompt

The xFusionCorp Industries ML platform team has implemented security enhancements before using Vault wiring: the MLflow boot wrapper no longer uses a static token for authentication. Instead, it now utilizes its own **AppRole** credentials to authenticate with Vault and acquires a short-lived token governed by the `mlflow-reader` policy. However, MLflow is currently unable to boot for two primary reasons: the AppRole authentication method is not configured, and the `mlflow-reader` policy contains errors that prevent even valid logins from accessing the secret.

Your task is to correct the `mlflow-reader` policy to ensure it provides `read` access on the KV v2 data path. Subsequently, enable the AppRole authentication method and establish an `mlflow` role that is bound to the adjusted policy. Once you have completed both tasks, the wrapper will log in, successfully read `secret/mlflow`, and MLflow will be operational on port `5000`.

  

1. The Vault UI is on port `8200` (**Vault** button). The dev-mode **root** token is at `/root/code/vault-root-token` — use it to log in to the UI and for the AppRole CLI steps (both are privileged operations). The `vault` CLI is on `PATH` and reaches the dev server at `VAULT_ADDR=http://127.0.0.1:8200`, authenticating with the root token from that file.
    
2. The wrapper authenticates via AppRole on its own: once the `mlflow` role exists it fetches the role's `role_id`/`secret_id`, logs in, and reads the secret with the **scoped** token it gets back. Within ~5 s of both fixes being in place it boots MLflow — click the **MLflow UI**button to confirm the tracker is live on port `5000`. There are no credential files to create by hand. While MLflow is still down, `tail /var/log/mlflow-wrapper.log` shows the wrapper looping on what it is waiting for.
    
3. The end state must include:
    
    - `GET /v1/sys/policies/acl/mlflow-reader` still returns the policy – Do not rename or delete it.
    - The policy's rules grant `read` on the KV v2 data path `secret/data/mlflow` (a `path "secret/data/mlflow"` block whose capabilities list contains `read`).
    - The AppRole auth method is enabled — `GET /v1/sys/auth` shows `approle/`.
    - An `mlflow` AppRole role exists whose `token_policies` include `mlflow-reader` — `GET /v1/auth/approle/role/mlflow`.
    - `http://localhost:5000/` answers `200`.

> Policies are Vault's **authorisation** layer; **AppRole** is one of its **authentication** methods. A policy's path rules resolve capabilities (`read`, `create`, …) for whatever token makes a call. AppRole is how a _machine_ logs in: a role bundles a set of policies, and a service proves its identity with a `role_id` (public, like a username) plus a `secret_id`(private, like a password), receiving a short-lived token scoped by that role's policies — no human and no static root token in the loop. This is the production replacement for the handed-out root token. A KV v2 subtlety also trips people here: secret **data** is served under a `secret/data/<name>` API path, distinct from the logical path you write to with `vault kv put` — a policy rule only grants access to the exact API path it names.

---

Solution

/root/code/vault-root-token

```
vault-lab-root-2026
```

Set token and address variables for the Vault CLI

```shell
export VAULT_TOKEN=$(cat /root/code/vault-root-token)
export VAULT_ADDR=http://127.0.0.1:8200
```

View Vault tokens

```shell
vault token lookup
```

Output

```shell
Key                 Value
---                 -----
accessor            3cANRy5APDVyddROp3LFBLqV
creation_time       1789053004
creation_ttl        0s
display_name        token
entity_id           n/a
expire_time         <nil>
explicit_max_ttl    0s
id                  vault-lab-root-2026
issue_time          2026-09-10T11:10:04.315710995-04:00
meta                <nil>
num_uses            0
orphan              true
path                auth/token/create
policies            [root]
renewable           false
ttl                 0s
type                service
```

Inspect "secret/" in Vault CLI

```shell
vault kv list "secret/"
```

Output

```shell
Keys
----
mlflow
```

Read the current policy

```shell
vault policy read mlflow-reader
```

Output

```shell
# MLflow boot-wrapper policy -- narrow KV access.
path "secret/mlflow" {
  capabilities = ["create", "update"]
}
```

- correct path "secret/mlflow" -> "secret/data/mlflow"
- update capabilities ["create", "update"] -> ["read"] 

Create policy file

```shell
cat > /tmp/mlflow-reader.hcl <<'EOF'
# MLflow boot-wrapper policy -- narrow KV access.
path "secret/data/mlflow" {
  capabilities = ["read"]
}
EOF
```

Write policy in Vault

```shell
vault policy write mlflow-reader /tmp/mlflow-reader.hcl
```

Verify the new policy

```shell
vault policy read mlflow-reader
```

Output

```shell
# MLflow boot-wrapper policy -- narrow KV access.
path "secret/data/mlflow" {
  capabilities = ["read"]
}
```

Check Vault auth list

```shell
vault auth list
```

Output

```shell
Path      Type     Accessor               Description                Version
----      ----     --------               -----------                -------
token/    token    auth_token_b4eb42aa    token based credentials    n/a
```

Add approle/ to auth list

```shell
vault auth enable approle
```

Output

```shell
Success! Enabled approle auth method at: approle/
```

Create role policy

```shell
vault write auth/approle/role/mlflow \
    token_policies="mlflow-reader"
```

Output

```shell
Success! Data written to: auth/approle/role/mlflow
```

Verify role policy

```shell
vault read auth/approle/role/mlflow
```

Output

```shell
Key                        Value
---                        -----
alias_metadata             map[]
bind_secret_id             true
local_secret_ids           false
secret_id_bound_cidrs      <nil>
secret_id_num_uses         0
secret_id_ttl              0s
token_bound_cidrs          []
token_explicit_max_ttl     0s
token_max_ttl              0s
token_no_default_policy    false
token_num_uses             0
token_period               0s
token_policies             [mlflow-reader]
token_ttl                  0s
token_type                 default
```

Check the wrapper log

```shell
tail -n 30 /var/log/mlflow-wrapper.log
```

Output

```shell
2026/09/10 11:44:43 INFO mlflow.server.jobs.utils: Registered trace_archival_scheduler periodic task (polls every 1 minute and no-ops when trace archival is disabled or unconfigured)
2026/09/10 11:48:39 INFO:     10.244.190.54:36972 - "GET / HTTP/1.1" 200 OK
2026/09/10 11:48:39 INFO:     10.244.190.54:36988 - "GET /static-files/manifest.json HTTP/1.1" 200 OK
2026/09/10 11:48:39 INFO:     10.244.190.54:36992 - "GET /static-files/static/js/main.2ce8870a.js HTTP/1.1" 200 OK
2026/09/10 11:48:39 INFO:     10.244.190.54:36998 - "GET /static-files/static/css/main.b0f58ef9.css HTTP/1.1" 200 OK
2026/09/10 11:48:42 INFO:     10.244.190.54:37000 - "GET /static-files/TelemetryLogger.telemetry-worker.d0f8ea2c83c08b63528f.worker.js HTTP/1.1" 200 OK
2026/09/10 11:48:42 INFO:     10.244.190.54:37012 - "GET /static-files/favicon.ico HTTP/1.1" 200 OK
2026/09/10 11:48:42 INFO:     10.244.190.54:37014 - "GET /ajax-api/3.0/mlflow/server-info HTTP/1.1" 200 OK
2026/09/10 11:48:42 INFO:     10.244.190.54:41098 - "GET /static-files/static/js/4205.9e750e7b.chunk.js HTTP/1.1" 200 OK
2026/09/10 11:48:42 INFO:     10.244.190.54:41106 - "GET /ajax-api/2.0/mlflow/users/current HTTP/1.1" 404 Not Found
2026/09/10 11:48:42 INFO:     10.244.190.54:41116 - "GET /ajax-api/3.0/mlflow/assistant/config HTTP/1.1" 403 Forbidden
2026/09/10 11:48:42 INFO:     10.244.190.54:41086 - "GET /ajax-api/3.0/mlflow/ui-telemetry HTTP/1.1" 200 OK
2026/09/10 11:48:43 INFO:     10.244.190.54:41132 - "GET /static-files/static/js/3877.d54c9d2c.chunk.js HTTP/1.1" 200 OK
2026/09/10 11:48:43 INFO:     10.244.190.54:41146 - "GET /static-files/static/media/demo-tracing-screenshot-dark.5cb0c24b165d2ed2fef0.png HTTP/1.1" 200 OK
2026/09/10 11:48:43 INFO:     10.244.190.54:41148 - "GET /static-files/static/js/4448.684e4843.chunk.js HTTP/1.1" 200 OK
2026/09/10 11:48:43 INFO:     10.244.190.54:41158 - "GET /static-files/static/css/5027.26533251.chunk.css HTTP/1.1" 200 OK
2026/09/10 11:48:43 INFO:     10.244.190.54:41162 - "GET /static-files/static/js/5027.9d51a16a.chunk.js HTTP/1.1" 200 OK
2026/09/10 11:48:43 INFO:     10.244.190.54:41178 - "GET /ajax-api/2.0/mlflow/experiments/search?max_results=5&order_by=last_update_time+DESC HTTP/1.1" 200 OK
```

Verify http://localhost:5000 answers '200'

```shell
curl -I http://localhost:5000/
```

Output

```shell
HTTP/1.1 200 OK
```

MLflow UI should now load

![screenshot](<../screenshots/Screenshot Day 45 MLflow UI.png>)