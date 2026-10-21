Prompt

The xFusionCorp Industries ML platform team practices canary rollouts using a pure-Python simulator before integrating the same traffic-split strategy into Argo Rollouts. The `canary_deploy.py` scaffold located at `/root/code/serving/` is responsible for monitoring the v2 error rate and steering the rollout. However, the canary policy, including the phase-weight ramp and rollback threshold, has not yet been implemented. Your task is to develop the canary policy in `canary_deploy.py` to ensure that the simulator effectively ramps traffic from 95/5 to 70/30 and finally to 0/100, concluding with the outcome `OUTCOME: PROMOTED` under healthy v2 conditions.

  

The project layout under `/root/code/serving/`:

- `canary_deploy.py` – Defines `CanaryDeployer` with `promote()`, `rollback()`, and `send_requests()`, plus a `main()` that runs three phases and rolls back if the v2 error rate exceeds `ROLLBACK_THRESHOLD`. `send_requests()`, `rollback()`, and `main()` are wired; `promote()`'s phase-weight ramp and the `ROLLBACK_THRESHOLD` value are left as `TODO`s. No network or model is used; the v2 error rate is simulated at 2 % per request via a seeded `random.Random(seed=42)`.

The end state must include:

- `ROLLBACK_THRESHOLD` is set to a value that keeps the healthy v2 rollout (simulated at a 2 % error rate) above the bar so it promotes rather than rolls back.
- `promote()` ramps the weights across the three phases: phase 1 → 95/5; phase 2 → 70/30; phase 3 → 0/100.
- Running the script prints three `Phase N:` lines, a `Total requests: 300` line, and ends with `OUTCOME: PROMOTED`.
- The phase-2 log line shows `v1_requests` > `v2_requests`.

> Managed canary controllers such as Argo Rollouts, Flagger, and Linkerd ship with a small default rollback threshold—set high enough it lets a broken v2 do meaningful damage before the rollout halts, too low and a healthy rollout is aborted on noise.

---

Solution

canary_deploy.py (Original)

```python
"""Canary-deployment simulator for the fraud-detection model.

Runs a three-phase traffic-split rollout from the stable v1 to the
candidate v2:

  Phase 1 — 95 % v1 / 5 % v2   (initial canary wedge)
  Phase 2 — 70 % v1 / 30 % v2  (confidence ramp)
  Phase 3 — 0  % v1 / 100 % v2 (full promotion)

Each phase fires `REQUESTS_PER_PHASE` requests, routes them per the
current weights, and measures the v2 error rate. If the error rate
exceeds `ROLLBACK_THRESHOLD`, the deployer rolls back to 100 % v1
and the simulation reports `ROLLED_BACK`; otherwise it advances to
the next phase. A clean three-phase run reports `PROMOTED`.

Released canary tooling (Argo Rollouts, Flagger, Linkerd) uses 5 %
as the standard rollback threshold — anything higher lets a bad
v2 do meaningful damage before the rollout halts.
"""
import random

# TODO: set the canary rollback bar. Released canary tooling (Argo
#       Rollouts, Flagger, Linkerd) halts a rollout once the candidate's
#       error rate exceeds ~5% — set ROLLBACK_THRESHOLD to 0.05.
ROLLBACK_THRESHOLD = 1.0
REQUESTS_PER_PHASE = 100

# Simulated per-request error probability of the v2 candidate.
# Stays well below a 5 % rollback threshold under healthy conditions.
V2_ERROR_RATE = 0.02


class CanaryDeployer:
    def __init__(self, seed: int = 42) -> None:
        self._rng = random.Random(seed)
        self.v1_weight = 1.0
        self.v2_weight = 0.0
        self.phase = 0

    def promote(self) -> tuple[float, float]:
        """Advance to the next phase's traffic weights."""
        self.phase += 1
        # TODO: author the canary ramp — set self.v1_weight and
        #   self.v2_weight for each phase (self.phase is 1, 2, or 3).
        #   Keep v1 the majority until v2 has proven itself, then hand
        #   v2 all traffic:
        #     phase 1 -> v1=0.95, v2=0.05   (initial 5% canary wedge)
        #     phase 2 -> v1=0.70, v2=0.30   (confidence ramp)
        #     phase 3 -> v1=0.00, v2=1.00   (full promotion)
        return self.v1_weight, self.v2_weight

    def rollback(self) -> None:
        self.v1_weight = 1.0
        self.v2_weight = 0.0

    def send_requests(self, n: int = REQUESTS_PER_PHASE) -> dict:
        v1_hits = 0
        v2_hits = 0
        v2_errors = 0
        for _ in range(n):
            if self._rng.random() < self.v1_weight:
                v1_hits += 1
            else:
                v2_hits += 1
                if self._rng.random() < V2_ERROR_RATE:
                    v2_errors += 1
        v2_error_rate = v2_errors / v2_hits if v2_hits else 0.0
        return {
            "v1_requests": v1_hits,
            "v2_requests": v2_hits,
            "v2_errors": v2_errors,
            "v2_error_rate": v2_error_rate,
        }


def main() -> None:
    deployer = CanaryDeployer(seed=42)
    total_requests = 0

    for phase_num in range(1, 4):
        v1_w, v2_w = deployer.promote()
        print(f"Phase {phase_num}: v1={v1_w:.0%} v2={v2_w:.0%}")
        stats = deployer.send_requests()
        total_requests += stats["v1_requests"] + stats["v2_requests"]
        print(
            f"  v1_requests={stats['v1_requests']} "
            f"v2_requests={stats['v2_requests']} "
            f"v2_error_rate={stats['v2_error_rate']:.2%}"
        )

        if stats["v2_error_rate"] > ROLLBACK_THRESHOLD:
            print(
                f"  ROLLBACK — v2 error rate {stats['v2_error_rate']:.2%} "
                f"> threshold {ROLLBACK_THRESHOLD:.0%}"
            )
            deployer.rollback()
            print(f"OUTCOME: ROLLED_BACK after {phase_num} phase(s)")
            print(f"Total requests: {total_requests}")
            return

    print("OUTCOME: PROMOTED")
    print(f"Total requests: {total_requests}")


if __name__ == "__main__":
    main()
```

(Updated)

```python
"""Canary-deployment simulator for the fraud-detection model.

Runs a three-phase traffic-split rollout from the stable v1 to the
candidate v2:

  Phase 1 — 95 % v1 / 5 % v2   (initial canary wedge)
  Phase 2 — 70 % v1 / 30 % v2  (confidence ramp)
  Phase 3 — 0  % v1 / 100 % v2 (full promotion)

Each phase fires `REQUESTS_PER_PHASE` requests, routes them per the
current weights, and measures the v2 error rate. If the error rate
exceeds `ROLLBACK_THRESHOLD`, the deployer rolls back to 100 % v1
and the simulation reports `ROLLED_BACK`; otherwise it advances to
the next phase. A clean three-phase run reports `PROMOTED`.

Released canary tooling (Argo Rollouts, Flagger, Linkerd) uses 5 %
as the standard rollback threshold — anything higher lets a bad
v2 do meaningful damage before the rollout halts.
"""
import random

# TODO: set the canary rollback bar. Released canary tooling (Argo
#       Rollouts, Flagger, Linkerd) halts a rollout once the candidate's
#       error rate exceeds ~5% — set ROLLBACK_THRESHOLD to 0.05.
ROLLBACK_THRESHOLD = 0.05
REQUESTS_PER_PHASE = 100

# Simulated per-request error probability of the v2 candidate.
# Stays well below a 5 % rollback threshold under healthy conditions.
V2_ERROR_RATE = 0.02


class CanaryDeployer:
    def __init__(self, seed: int = 42) -> None:
        self._rng = random.Random(seed)
        self.v1_weight = 1.0
        self.v2_weight = 0.0
        self.phase = 0

    def promote(self) -> tuple[float, float]:
        """Advance to the next phase's traffic weights."""
        self.phase += 1
        if self.phase == 1:
            self.v1_weight = 0.95
            self.v2_weight = 0.05
        elif self.phase == 2:
            self.v1_weight = 0.70
            self.v2_weight = 0.30
        elif self.phase == 3:
            self.v1_weight = 0.00
            self.v2_weight = 1.00
        return self.v1_weight, self.v2_weight

    def rollback(self) -> None:
        self.v1_weight = 1.0
        self.v2_weight = 0.0

    def send_requests(self, n: int = REQUESTS_PER_PHASE) -> dict:
        v1_hits = 0
        v2_hits = 0
        v2_errors = 0
        for _ in range(n):
            if self._rng.random() < self.v1_weight:
                v1_hits += 1
            else:
                v2_hits += 1
                if self._rng.random() < V2_ERROR_RATE:
                    v2_errors += 1
        v2_error_rate = v2_errors / v2_hits if v2_hits else 0.0
        return {
            "v1_requests": v1_hits,
            "v2_requests": v2_hits,
            "v2_errors": v2_errors,
            "v2_error_rate": v2_error_rate,
        }


def main() -> None:
    deployer = CanaryDeployer(seed=42)
    total_requests = 0

    for phase_num in range(1, 4):
        v1_w, v2_w = deployer.promote()
        print(f"Phase {phase_num}: v1={v1_w:.0%} v2={v2_w:.0%}")
        stats = deployer.send_requests()
        total_requests += stats["v1_requests"] + stats["v2_requests"]
        print(
            f"  v1_requests={stats['v1_requests']} "
            f"v2_requests={stats['v2_requests']} "
            f"v2_error_rate={stats['v2_error_rate']:.2%}"
        )

        if stats["v2_error_rate"] > ROLLBACK_THRESHOLD:
            print(
                f"  ROLLBACK — v2 error rate {stats['v2_error_rate']:.2%} "
                f"> threshold {ROLLBACK_THRESHOLD:.0%}"
            )
            deployer.rollback()
            print(f"OUTCOME: ROLLED_BACK after {phase_num} phase(s)")
            print(f"Total requests: {total_requests}")
            return

    print("OUTCOME: PROMOTED")
    print(f"Total requests: {total_requests}")


if __name__ == "__main__":
    main()
```

Navigate to working directory

```shell
cd /root/code/serving
```

Run script

```shell
python3 canary_deploy.py
```

Output

```shell
Phase 1: v1=95% v2=5%
  v1_requests=94 v2_requests=6 v2_error_rate=0.00%
Phase 2: v1=70% v2=30%
  v1_requests=70 v2_requests=30 v2_error_rate=0.00%
Phase 3: v1=0% v2=100%
  v1_requests=0 v2_requests=100 v2_error_rate=3.00%
OUTCOME: PROMOTED
Total requests: 300
```



```shell

```



```shell

```



```shell

```



```shell

```



```shell

```
