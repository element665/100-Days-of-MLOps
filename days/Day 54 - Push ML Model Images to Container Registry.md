Prompt

The xFusionCorp Industries ML platform team has implemented a fraud-detection image and stored it in a private Docker registry for downstream clusters to access by tag. The registry is currently operational on host port `5555`, and there exists a `push.sh` script located at `/root/code/ml-registry/` that builds the image. However, the script does not yet include the steps necessary for publishing the image to the registry, which is marked as a `TODO`. Your objective is to complete the publishing flow within the script. Specifically, ensure that when you run `./push.sh`, it successfully builds the image labeled `fraud-detector:v1`, tags it appropriately for the local registry, pushes the image, and confirms that the registry's HTTP catalogue responds with `{"repositories":["fraud-detector"]}`.

  

1. The Docker daemon is already running and a `registry:2` container named `local-registry` is already up on host port `5555` (→ container port 5000).
    
2. The project layout under `/root/code/ml-registry/`:
    
    - `train.py` – Fits a tiny RandomForest and writes `/app/model.pkl`. Correct.
    - `Dockerfile` – `python:3.11-slim` base, installs sklearn + numpy + joblib, runs `train.py` at build time so the model is baked into the image. Correct.
    - `push.sh` – Executable shell script that `docker build`s `fraud-detector:v1`; the registry publish flow (naming the image for the registry and pushing it) is left as a `TODO` to author.
3. The end state must include:
    
    - `docker images fraud-detector:v1` lists the locally-built image.
    - `curl http://localhost:5555/v2/_catalog`returns a JSON body with `fraud-detector` in the `repositories` array.
    - `curl http://localhost:5555/v2/fraud-detector/tags/list` returns a JSON body carrying `v1` in the `tags` array.

> `docker tag` only writes local metadata; nothing reaches the registry until `docker push` runs.

---

Solution

[train.py](<../assets/Day 54 - train.py>) (Provided)

[Dockerfile](<../assets/Day 54 - Dockerfile>) (Provided)

push.sh (Original)

```shell
#!/bin/bash
# Build the fraud-detector image and publish it to the local private
# registry so downstream clusters can pull it by tag.
#
# Run from /root/code/ml-registry/.
set -euo pipefail

cd "$(dirname "$0")"

IMAGE="fraud-detector:v1"

docker build -t "$IMAGE" .

# TODO: publish "$IMAGE" to the lab's private registry so downstream
#       clusters can pull it. The registry runs on host port 5555
#       (registry:2 -> container port 5000). Author the publish flow
#       below so that, after ./push.sh runs, the registry catalogue at
#       http://localhost:5555/v2/_catalog lists "fraud-detector" and
#       its tags/list carries "v1". Remember an image only reaches a
#       registry once it is both named for that registry and pushed —
#       naming it alone writes local metadata only.
```

push.sh (Updated)

```sh
#!/bin/bash
# Build the fraud-detector image and publish it to the local private
# registry so downstream clusters can pull it by tag.
#
# Run from /root/code/ml-registry/.
set -euo pipefail

cd "$(dirname "$0")"

IMAGE="fraud-detector:v1"

docker build -t "$IMAGE" .

# TODO: publish "$IMAGE" to the lab's private registry so downstream
#       clusters can pull it. The registry runs on host port 5555
#       (registry:2 -> container port 5000). Author the publish flow
#       below so that, after ./push.sh runs, the registry catalogue at
#       http://localhost:5555/v2/_catalog lists "fraud-detector" and
#       its tags/list carries "v1". Remember an image only reaches a
#       registry once it is both named for that registry and pushed —
#       naming it alone writes local metadata only.

REGISTRY="localhost:5555"

docker tag "$IMAGE" "$REGISTRY/$IMAGE"

docker push "$REGISTRY/$IMAGE"
```

Run push script

```shell
./push.sh
```

Output

```shell
[+] Building 22.3s (10/10) FINISHED                                                        docker:default
 => [internal] load build definition from Dockerfile                                                 0.0s
 => => transferring dockerfile: 304B                                                                 0.0s
 => [internal] load metadata for docker.io/library/python:3.11-slim                                  1.2s
 => [internal] load .dockerignore                                                                    0.0s
 => => transferring context: 2B                                                                      0.0s
 => [1/5] FROM docker.io/library/python:3.11-slim@sha256:e41613d42d4891e4930f79523f93f81bbc7632584e  2.3s
 => => resolve docker.io/library/python:3.11-slim@sha256:e41613d42d4891e4930f79523f93f81bbc7632584e  0.0s
 => => sha256:0526d5e29bf341cb1941d46a6d4ab64fcde4fca3dc3adccfb4dbf5728b88b61e 249B / 249B           0.1s
 => => sha256:58abdd9670ca8c69d03432ce188995dee67f0979357caf83866fe1ef2ec37138 14.45MB / 14.45MB     0.4s
 => => sha256:41e7217c2e506d048f89ca0c5cfef848c05ef990900627c19f99938c4aae57f8 1.29MB / 1.29MB       0.4s
 => => sha256:6b37362b3da78869050b894b799ad4df04f1f3b52774087db0d81151570244c8 29.83MB / 29.83MB     0.6s
 => => extracting sha256:6b37362b3da78869050b894b799ad4df04f1f3b52774087db0d81151570244c8            0.6s
 => => extracting sha256:41e7217c2e506d048f89ca0c5cfef848c05ef990900627c19f99938c4aae57f8            0.3s
 => => extracting sha256:58abdd9670ca8c69d03432ce188995dee67f0979357caf83866fe1ef2ec37138            0.6s
 => => extracting sha256:0526d5e29bf341cb1941d46a6d4ab64fcde4fca3dc3adccfb4dbf5728b88b61e            0.0s
 => [internal] load build context                                                                    0.1s
 => => transferring context: 602B                                                                    0.0s
 => [2/5] WORKDIR /app                                                                               0.0s
 => [3/5] RUN pip install --no-cache-dir scikit-learn numpy joblib                                   8.1s
 => [4/5] COPY train.py /app/train.py                                                                0.1s
 => [5/5] RUN python3 /app/train.py                                                                  1.3s
 => exporting to image                                                                               9.2s
 => => exporting layers                                                                              6.0s
 => => exporting manifest sha256:2d65aee8f6e39e1bac5172fce2c3a0c469b51e96b98e7927562f787f464a74e0    0.0s
 => => exporting config sha256:a50ed7d0b858497daa8c36aaec5a3230a8e9cf5f4ea097b7063a0f8b88c6daef      0.0s
 => => exporting attestation manifest sha256:2463169dc8d1062b06fe7e90a5a666245e13945064908f976fa46f  0.0s
 => => exporting manifest list sha256:be6a03588fe424d61eaa0191d6b9f59581bf8f920d6d7e0127ab7215fb9c2  0.0s
 => => naming to docker.io/library/fraud-detector:v1                                                 0.0s
 => => unpacking to docker.io/library/fraud-detector:v1                                              3.1s
The push refers to repository [localhost:5555/fraud-detector]
3472bdb7e2ce: Pushed 
58abdd9670ca: Pushed 
0526d5e29bf3: Pushed 
6674a1320446: Pushed 
3ef4f8faf1f5: Pushed 
6b37362b3da7: Pushed 
b18733c467de: Pushed 
b7fa7499e7e6: Pushed 
41e7217c2e50: Pushed 
v1: digest: sha256:be6a03588fe424d61eaa0191d6b9f59581bf8f920d6d7e0127ab7215fb9c20b6 size: 856
```

### Verification

Confirm image is listed locally

```shell
docker images fraud-detector:v1
```

Output

```shell
IMAGE               ID             DISK USAGE   CONTENT SIZE   EXTRA
fraud-detector:v1   be6a03588fe4        576MB          133MB
```

Confirm image registry lists 'fraud-detector'

```shell
curl http://localhost:5555/v2/_catalog
```

Output

```JSON
{"repositories":["fraud-detector"]}
```

Confirm image registry has 'fraud-detector' tagged 'v1'

```shell
curl http://localhost:5555/v2/fraud-detector/tags/list
```

Output

```json
{"name":"fraud-detector","tags":["v1"]}
```
