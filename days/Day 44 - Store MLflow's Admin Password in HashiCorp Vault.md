Prompt

The xFusionCorp Industries ML platform team requires that all credentials necessary for the lab-ops service—including MLflow's admin password, SeaweedFS's access keys, and PostgreSQL passwords—be retrieved from HashiCorp Vault at service startup, rather than being hardcoded into a startup script. A development Vault is currently operational on port `8200`, and its web UI can be accessed via the **Vault** button. Additionally, an MLflow boot wrapper on the host is polling Vault every 5 seconds for the `secret/mlflow.admin_password`. However, the wrapper can only initiate MLflow once this KV entry is available. Your task is to enable the KV v2 engine in Vault, create the secret, and observe the successful startup of MLflow on port `5000`.

  

1. The Vault UI is on port `8200` (**Vault** button opens the login page). The dev-mode root token is pre-created and written to `/root/code/vault-token`; paste the file's contents into the Vault **Token** login field. (Production deployments would use userpass / AppRole / OIDC instead, but the root token is the shortest path for a dev server.)
    
2. The MLflow wrapper picks up the new KV entry within ~5 s and execs `mlflow server` on port `5000`. The **MLflow UI** button then opens the live tracker.
    
3. The end state must include:
    
    - A KV v2 secrets engine is enabled at path `secret/` — `GET /v1/sys/mounts` returns `secret/` with `type: kv` and `options.version: "2"`.
    - The secret at path `secret/mlflow` carries a non-empty `admin_password` key — `GET /v1/secret/data/mlflow` (with the root token) returns a JSON body whose `data.data.admin_password` is a non-empty string.
    - `GET http://localhost:5000/` answers `200` – MLflow is running because the wrapper found the password.

> Running services should not know their own secrets at image-build time. A Vault-first pattern lets you rotate a credential in Vault and restart the consumer to pick up the new value—no rebuild, no config patch, no secret in the commit history. This task's single-service wrapper is the minimum viable version of that pattern; a real deployment replaces the root token with an AppRole login and adds audit logging.

---

Solution

/root/code/vault-token

```
vault-lab-root-2026
```

Check the Vault mounts and what secrets exist

```shell
export VAULT_TOKEN=$(cat /root/code/vault-token)

curl -s \
  -H "X-Vault-Token: $VAULT_TOKEN" \
  http://127.0.0.1:8200/v1/sys/mounts | jq
```

Output

```shell
{
  "agent-registry/": {
    "accessor": "agent-registry_cfe4bd31",
    "config": {
      "default_lease_ttl": 0,
      "force_no_cache": false,
      "max_lease_ttl": 0,
      "passthrough_request_headers": [
        "Authorization"
      ]
    },
    "description": "agent registry",
    "external_entropy_access": false,
    "local": false,
    "options": null,
    "plugin_version": "",
    "running_plugin_version": "v2.0.3+builtin.vault",
    "running_sha256": "",
    "seal_wrap": false,
    "type": "agent_registry",
    "uuid": "49b07f2f-e4e4-1a02-554d-b7777d084d77"
  },
  "cubbyhole/": {
    "accessor": "cubbyhole_321c244c",
    "config": {
      "default_lease_ttl": 0,
      "force_no_cache": false,
      "max_lease_ttl": 0
    },
    "description": "per-token private secret storage",
    "external_entropy_access": false,
    "local": true,
    "options": null,
    "plugin_version": "",
    "running_plugin_version": "v2.0.3+builtin.vault",
    "running_sha256": "",
    "seal_wrap": false,
    "type": "cubbyhole",
    "uuid": "63455263-b9f4-3cb1-5653-9541ee3d6830"
  },
  "sys/": {
    "accessor": "system_f4737e2b",
    "config": {
      "default_lease_ttl": 0,
      "force_no_cache": false,
      "max_lease_ttl": 0,
      "passthrough_request_headers": [
        "Accept"
      ]
    },
    "description": "system endpoints used for control, policy and debugging",
    "external_entropy_access": false,
    "local": false,
    "options": null,
    "plugin_version": "",
    "running_plugin_version": "v2.0.3+builtin.vault",
    "running_sha256": "",
    "seal_wrap": true,
    "type": "system",
    "uuid": "d7f0ba4b-bd32-7497-5832-c987114b642a"
  },
  "identity/": {
    "accessor": "identity_89badc2d",
    "config": {
      "allowed_response_headers": [
        "Location"
      ],
      "default_lease_ttl": 0,
      "force_no_cache": false,
      "max_lease_ttl": 0,
      "passthrough_request_headers": [
        "Authorization"
      ]
    },
    "description": "identity store",
    "external_entropy_access": false,
    "local": false,
    "options": null,
    "plugin_version": "",
    "running_plugin_version": "v2.0.3+builtin.vault",
    "running_sha256": "",
    "seal_wrap": false,
    "type": "identity",
    "uuid": "7c1df2ef-4b80-9e94-4f40-d0b54ec195f8"
  },
  "request_id": "2a649788-b0f0-0b31-dd90-bd0204eed3f8",
  "lease_id": "",
  "renewable": false,
  "lease_duration": 0,
  "data": {
    "agent-registry/": {
      "accessor": "agent-registry_cfe4bd31",
      "config": {
        "default_lease_ttl": 0,
        "force_no_cache": false,
        "max_lease_ttl": 0,
        "passthrough_request_headers": [
          "Authorization"
        ]
      },
      "description": "agent registry",
      "external_entropy_access": false,
      "local": false,
      "options": null,
      "plugin_version": "",
      "running_plugin_version": "v2.0.3+builtin.vault",
      "running_sha256": "",
      "seal_wrap": false,
      "type": "agent_registry",
      "uuid": "49b07f2f-e4e4-1a02-554d-b7777d084d77"
    },
    "cubbyhole/": {
      "accessor": "cubbyhole_321c244c",
      "config": {
        "default_lease_ttl": 0,
        "force_no_cache": false,
        "max_lease_ttl": 0
      },
      "description": "per-token private secret storage",
      "external_entropy_access": false,
      "local": true,
      "options": null,
      "plugin_version": "",
      "running_plugin_version": "v2.0.3+builtin.vault",
      "running_sha256": "",
      "seal_wrap": false,
      "type": "cubbyhole",
      "uuid": "63455263-b9f4-3cb1-5653-9541ee3d6830"
    },
    "identity/": {
      "accessor": "identity_89badc2d",
      "config": {
        "allowed_response_headers": [
          "Location"
        ],
        "default_lease_ttl": 0,
        "force_no_cache": false,
        "max_lease_ttl": 0,
        "passthrough_request_headers": [
          "Authorization"
        ]
      },
      "description": "identity store",
      "external_entropy_access": false,
      "local": false,
      "options": null,
      "plugin_version": "",
      "running_plugin_version": "v2.0.3+builtin.vault",
      "running_sha256": "",
      "seal_wrap": false,
      "type": "identity",
      "uuid": "7c1df2ef-4b80-9e94-4f40-d0b54ec195f8"
    },
    "sys/": {
      "accessor": "system_f4737e2b",
      "config": {
        "default_lease_ttl": 0,
        "force_no_cache": false,
        "max_lease_ttl": 0,
        "passthrough_request_headers": [
          "Accept"
        ]
      },
      "description": "system endpoints used for control, policy and debugging",
      "external_entropy_access": false,
      "local": false,
      "options": null,
      "plugin_version": "",
      "running_plugin_version": "v2.0.3+builtin.vault",
      "running_sha256": "",
      "seal_wrap": true,
      "type": "system",
      "uuid": "d7f0ba4b-bd32-7497-5832-c987114b642a"
    }
  },
  "wrap_info": null,
  "warnings": null,
  "auth": null,
  "mount_type": "system"
}
```

Enable KV v2 at secret/

```shell
curl -s \
  -X POST \
  -H "X-Vault-Token: $VAULT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"type":"kv","options":{"version":"2"}}' \
  http://127.0.0.1:8200/v1/sys/mounts/secret
```

create MLflow secret

```shell
curl -s \
  -X POST \
  -H "X-Vault-Token: $VAULT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"data":{"admin_password":"MLflowDevAdmin_2026!"}}' \
  http://127.0.0.1:8200/v1/secret/data/mlflow
```

Verify secret is created and stored

```shell
curl -s \
  -H "X-Vault-Token: $VAULT_TOKEN" \
  http://127.0.0.1:8200/v1/secret/data/mlflow | jq
```

Output

```shell
{
  "request_id": "9994b4a3-fed4-3cb1-abf7-5d2c732cb661",
  "lease_id": "",
  "renewable": false,
  "lease_duration": 0,
  "data": {
    "data": {
      "admin_password": "MLflowDevAdmin_2026!"
    },
    "metadata": {
      "created_time": "2026-09-08T09:07:37.953785249Z",
      "custom_metadata": null,
      "deletion_time": "",
      "destroyed": false,
      "version": 1
    }
  },
  "wrap_info": null,
  "warnings": null,
  "auth": null,
  "mount_type": "kv"
}
```


---


Sign in to Vault UI using provided Token

![Vault Sign-in](<../screenshots/Screenshot Day 44 Vault UI signin.png>)

Verify secret is created and carries a non-empty `admin_password`

![MLflow Secret](<../screenshots/Screenshot Day 44 MLflow secret.png>)