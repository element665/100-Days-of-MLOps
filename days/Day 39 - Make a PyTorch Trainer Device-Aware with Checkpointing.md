Prompt

The xFusionCorp Industries ML platform team is tasked with deploying fraud-detection models utilizing a compact PyTorch network. It is essential that the training script operates seamlessly on any available accelerator, whether that be CUDA GPUs in the production cluster or standard CPUs on the lab's nodes. This ensures uniform functionality across all platforms.

Currently, a preliminary version of the trainer is available at `/root/code/fraud-detection/src/models/train_pytorch.py`. However, this script is not device-aware; it assumes the presence of CUDA, resulting in failures upon the first tensor operation on incompatible hardware. Additionally, the device parameter logged to MLflow is hardcoded, leading to inaccuracies in reporting.

Your objective is to enhance the trainer by implementing device awareness, enabling it to accurately reflect the utilized device in the MLflow logs. Furthermore, you are required to incorporate per-epoch checkpointing to facilitate resuming long training sessions.

  

1. The MLflow tracking server is already running on port `5000`. The **MLflow UI** button at the top of the lab can be opened to confirm—the dashboard loads with an empty `pytorch-training` experiment. PyTorch (CPU build) is baked into the lab image; `import torch` works out of the box. The host does not expose a GPU (`torch.cuda.is_available()` returns `False`).
    
2. The project layout under `/root/code/fraud-detection/`:
    
    - `data/train.csv` – The same 200-row synthetic binary-classification dataset the rest of the Training section uses.
    - `src/models/train_pytorch.py` – The trainer scaffold. The two-layer feedforward network, the optimiser, the loss function, the MLflow experiment setup, and the model-persistence call to `models/fraud_model.pt` are already wired; the work is confined to this file (two device corrections plus a per-epoch checkpointing TODO in the training loop).
3. Run the trainer once against the scaffold as-is—`python src/models/train_pytorch.py`—to see it fail on the first tensor operation.
    
4. The end state must include:
    
    - The script completes successfully and writes a PyTorch state-dict to `/root/code/fraud-detection/models/fraud_model.pt`.
    - One run exists in the `pytorch-training`experiment on MLflow, carrying `params.device = "cpu"` and `metrics.final_loss`.
    - No bare `.cuda()` calls remain anywhere in `train_pytorch.py`.
    - At least two resumable checkpoints exist under `/root/code/fraud-detection/checkpoints/`(named `ckpt_epoch_*.pt`), each a dict carrying the model and optimiser state (so training can resume).

---

Solution

train_pytorch.py (Original)

```python
"""Feedforward fraud-detection trainer.

Trains a tiny two-layer network on the synthetic transactions CSV,
logs the run to MLflow with `params.device` + `metrics.final_loss`,
and saves the trained weights to `models/fraud_model.pt`.

Data loading, model definition, optimizer setup, loss function, and
the MLflow experiment are already wired. Two things need work:

  1. The current wiring assumes a CUDA GPU is always present. Make
     the device handling runtime-aware so the script runs on whichever
     accelerator the host exposes, and log the device it actually used.
  2. Long training runs need to be resumable — add per-epoch
     checkpointing (TODO inside the loop) so progress survives an
     interruption.
"""
import os

import mlflow
import numpy as np
import pandas as pd
import torch
import torch.nn as nn

TRACKING_URI = "http://localhost:5000"
EXPERIMENT = "pytorch-training"
TRAIN_CSV = "/root/code/fraud-detection/data/train.csv"
MODEL_PATH = "/root/code/fraud-detection/models/fraud_model.pt"
CHECKPOINT_DIR = "/root/code/fraud-detection/checkpoints"

FEATURES = ["amount", "hour", "num_tx_past_day"]
TARGET = "is_fraud"
EPOCHS = 30
LR = 0.01
SEED = 42


class FraudNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc1 = nn.Linear(len(FEATURES), 8)
        self.fc2 = nn.Linear(8, 2)

    def forward(self, x):
        return self.fc2(torch.relu(self.fc1(x)))


def main():
    torch.manual_seed(SEED)
    np.random.seed(SEED)

    mlflow.set_tracking_uri(TRACKING_URI)
    mlflow.set_experiment(EXPERIMENT)

    df = pd.read_csv(TRAIN_CSV)
    X = df[FEATURES].values.astype(np.float32)
    y = df[TARGET].values.astype(np.int64)

    X_t = torch.from_numpy(X)
    y_t = torch.from_numpy(y)

    model = FraudNet()
    model = model.cuda()

    optimizer = torch.optim.SGD(model.parameters(), lr=LR)
    loss_fn = nn.CrossEntropyLoss()

    os.makedirs(CHECKPOINT_DIR, exist_ok=True)

    with mlflow.start_run(run_name="fraud-mlp"):
        mlflow.log_param("device", "cuda")

        xb = X_t.cuda()
        yb = y_t.cuda()

        final_loss = None
        for epoch in range(EPOCHS):
            logits = model(xb)
            loss = loss_fn(logits, yb)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            final_loss = float(loss.item())
            print(f"epoch {epoch:02d}  loss={final_loss:.4f}")

            # TODO: every 10th epoch (0, 10, 20), write a resumable
            # checkpoint to CHECKPOINT_DIR/ckpt_epoch_{epoch}.pt. Use
            # torch.save({...}, path) with a dict carrying "epoch", the
            # model "model_state_dict", the optimizer
            # "optimizer_state_dict", and the current "loss" — everything
            # needed to resume training from that point.

        mlflow.log_metric("final_loss", final_loss)

        os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
        torch.save(model.state_dict(), MODEL_PATH)
        print(f"Model saved to {MODEL_PATH}")


if __name__ == "__main__":
    main()
```

Run the trainer once as-is per instructions

```shell
cd fraud-detection/
python src/models/train_pytorch.py
```

Output

```shell
Traceback (most recent call last):
  File "/root/code/fraud-detection/src/models/train_pytorch.py", line 101, in <module>
    main()
  File "/root/code/fraud-detection/src/models/train_pytorch.py", line 63, in main
    model = model.cuda()
            ^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/torch/nn/modules/module.py", line 1096, in cuda
    return self._apply(lambda t: t.cuda(device))
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/torch/nn/modules/module.py", line 933, in _apply
    module._apply(fn)
  File "/usr/local/lib/python3.12/dist-packages/torch/nn/modules/module.py", line 964, in _apply
    param_applied = fn(param)
                    ^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/torch/nn/modules/module.py", line 1096, in <lambda>
    return self._apply(lambda t: t.cuda(device))
                                 ^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/torch/cuda/__init__.py", line 484, in _lazy_init
    raise AssertionError("Torch not compiled with CUDA enabled")
AssertionError: Torch not compiled with CUDA enabled
```

- Add device detection
- Move tensors to the device
- Log device
- Add checkpointing

Add device detection

```python
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = FraudNet().to(device)
```

Move tensors to device

```python
xb = X_t.to(device)
yb = y_t.to(device)
```

Log the device

```python
mlflow.log_param("device", str(device))
```

Add checkpointing (TODO section)

```python
if epoch % 10 == 0:
	checkpoint_path = os.path.join(
		CHECKPOINT_DIR, f"ckpt_epoch_{epoch}.pt"
	)
	torch.save(
		{
			"epoch": epoch,
			"model_state_dict": model.state_dict(),
			"optimizer_state_dict": optimizer.state_dict(),
			"loss": final_loss,
		},
		checkpoint_path,
	)
	print(f"Checkpoint saved to {checkpoint_path}")
```

train_pytorch.py (Final)

```python
"""Feedforward fraud-detection trainer.

Trains a tiny two-layer network on the synthetic transactions CSV,
logs the run to MLflow with `params.device` + `metrics.final_loss`,
and saves the trained weights to `models/fraud_model.pt`.

Data loading, model definition, optimizer setup, loss function, and
the MLflow experiment are already wired. Two things need work:

  1. The current wiring assumes a CUDA GPU is always present. Make
     the device handling runtime-aware so the script runs on whichever
     accelerator the host exposes, and log the device it actually used.
  2. Long training runs need to be resumable — add per-epoch
     checkpointing (TODO inside the loop) so progress survives an
     interruption.
"""
import os

import mlflow
import numpy as np
import pandas as pd
import torch
import torch.nn as nn

TRACKING_URI = "http://localhost:5000"
EXPERIMENT = "pytorch-training"
TRAIN_CSV = "/root/code/fraud-detection/data/train.csv"
MODEL_PATH = "/root/code/fraud-detection/models/fraud_model.pt"
CHECKPOINT_DIR = "/root/code/fraud-detection/checkpoints"

FEATURES = ["amount", "hour", "num_tx_past_day"]
TARGET = "is_fraud"
EPOCHS = 30
LR = 0.01
SEED = 42


class FraudNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc1 = nn.Linear(len(FEATURES), 8)
        self.fc2 = nn.Linear(8, 2)

    def forward(self, x):
        return self.fc2(torch.relu(self.fc1(x)))


def main():
    torch.manual_seed(SEED)
    np.random.seed(SEED)

    mlflow.set_tracking_uri(TRACKING_URI)
    mlflow.set_experiment(EXPERIMENT)

    df = pd.read_csv(TRAIN_CSV)
    X = df[FEATURES].values.astype(np.float32)
    y = df[TARGET].values.astype(np.int64)

    X_t = torch.from_numpy(X)
    y_t = torch.from_numpy(y)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = FraudNet().to(device)

    optimizer = torch.optim.SGD(model.parameters(), lr=LR)
    loss_fn = nn.CrossEntropyLoss()

    os.makedirs(CHECKPOINT_DIR, exist_ok=True)

    with mlflow.start_run(run_name="fraud-mlp"):
        mlflow.log_param("device", str(device))

        xb = X_t.to(device)
        yb = y_t.to(device)

        final_loss = None
        for epoch in range(EPOCHS):
            logits = model(xb)
            loss = loss_fn(logits, yb)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            final_loss = float(loss.item())
            print(f"epoch {epoch:02d}  loss={final_loss:.4f}")

            # TODO: every 10th epoch (0, 10, 20), write a resumable
            # checkpoint to CHECKPOINT_DIR/ckpt_epoch_{epoch}.pt. Use
            # torch.save({...}, path) with a dict carrying "epoch", the
            # model "model_state_dict", the optimizer
            # "optimizer_state_dict", and the current "loss" — everything
            # needed to resume training from that point.

            if epoch % 10 == 0:
                checkpoint_path = os.path.join(
                    CHECKPOINT_DIR, f"ckpt_epoch_{epoch}.pt"
                )
                torch.save(
                    {
                        "epoch": epoch,
                        "model_state_dict": model.state_dict(),
                        "optimizer_state_dict": optimizer.state_dict(),
                        "loss": final_loss,
                    },
                    checkpoint_path,
                )
                print(f"Checkpoint saved to {checkpoint_path}")        


        mlflow.log_metric("final_loss", final_loss)

        os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
        torch.save(model.state_dict(), MODEL_PATH)
        print(f"Model saved to {MODEL_PATH}")


if __name__ == "__main__":
    main()
```

Check for bare `.cuda()` calls

```shell
grep -n "\.cuda()" src/models/train_pytorch.py
```

Run updated script

```shell
python src/models/train_pytorch.py
```

Output

```shell
epoch 00  loss=19.1806
Checkpoint saved to /root/code/fraud-detection/checkpoints/ckpt_epoch_0.pt
epoch 01  loss=561.9835
epoch 02  loss=0.6144
epoch 03  loss=0.6141
epoch 04  loss=0.6140
epoch 05  loss=0.6138
epoch 06  loss=0.6137
epoch 07  loss=0.6136
epoch 08  loss=0.6134
epoch 09  loss=0.6133
epoch 10  loss=0.6132
Checkpoint saved to /root/code/fraud-detection/checkpoints/ckpt_epoch_10.pt
epoch 11  loss=0.6131
epoch 12  loss=0.6129
epoch 13  loss=0.6128
epoch 14  loss=0.6127
epoch 15  loss=0.6126
epoch 16  loss=0.6125
epoch 17  loss=0.6123
epoch 18  loss=0.6122
epoch 19  loss=0.6121
epoch 20  loss=0.6120
Checkpoint saved to /root/code/fraud-detection/checkpoints/ckpt_epoch_20.pt
epoch 21  loss=0.6119
epoch 22  loss=0.6118
epoch 23  loss=0.6117
epoch 24  loss=0.6116
epoch 25  loss=0.6114
epoch 26  loss=0.6113
epoch 27  loss=0.6112
epoch 28  loss=0.6111
epoch 29  loss=0.6110
Model saved to /root/code/fraud-detection/models/fraud_model.pt
🏃 View run fraud-mlp at: http://localhost:5000/#/experiments/1/runs/31eacfb232f34da88fe51acb442ab62a
🧪 View experiment at: http://localhost:5000/#/experiments/1
```


Verification

- Screenshot of PyTorch state-dict (/root/code/fraud-detection/models/fraud_model.pt)

![Pytorch](<../screenshots/Screenshot Day 39 PyTorch state-dict.png>)

- Screenshot of one run in MLflow UI

![MLflow UI](<../screenshots/Screenshot Day 39 MLflow UI run.png>)

- Screenshot of run details

![Run Details](<../screenshots/Screenshot Day 39 Run Details.png>)

- Screenshot of no cuda calls

![No CUDA calls](<../screenshots/Screenshot Day 39 No CUDA calls.png>)

- Screenshot of checkpoints

![Checkpoints](<../screenshots/Screenshot Day 39 Checkpoints.png>)

