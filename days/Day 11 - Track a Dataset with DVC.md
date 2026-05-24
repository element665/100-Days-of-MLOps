Prompt

A teammate has added the transactions dataset to the xFusionCorp Industries fraud-detection repository, but it was committed directly to Git instead of being tracked with DVC. Bring the repository in line with the team standard—every dataset under `data/` must be tracked by DVC, not by Git.


1. A project exists at `/root/code/fraud-detection/` with DVC already initialised. The dataset `data/raw/transactions.csv` is currently tracked by Git, and the team standard requires DVC to own it instead.
    
2. Stop Git from tracking the dataset without deleting it from disk.
    
3. Track the same dataset with DVC so a `.dvc` pointer file is produced and `data/raw/.gitignore` excludes the dataset itself.
    
4. Stage the new `.dvc` pointer and the new `.gitignore`, then record a Git commit with the message `Track transactions dataset with DVC`.
    

> Once tracking is moved to DVC, the **DVC TRACKED**section in the EXPLORER panel will list the dataset, confirming the extension recognises it as a DVC-managed file.

---

Solution

Navigate to repo

```shell
cd /root/code/fraud-detection/
```

Check if dataset is owned by git

```shell
git ls-files data/raw/transactions.csv
```

Remove dataset from git tracking

```shell
git rm --cached data/raw/transactions.csv
```

Start tracking with DVC

```shell
dvc add data/raw/transactions.csv
```

Verify repo status

```shell
git status
```

Stage changes (including dataset removal)

```shell
git add data/raw/transactions.csv.dvc
git add data/raw/.gitignore
git add -u
```

Commit changes (Use required message)

```shell
git commit -m "Track transactions dataset with DVC"
```

Verify Git and DVC

```shell
git status
dvc status
```

---

## Notes

### Why `git rm --cached` matters

Without `--cached`, Git would delete the file from disk.

With `--cached`:

- Git stops tracking it
- the file remains physically present
- DVC can immediately take over ownership


### What changed architecturally

Before:

```
Git ---> tracked raw CSV directly
```

After:

```
Git ---> tracks lightweight .dvc metadataDVC ---> tracks actual dataset contents
```

That separation is the core idea behind DVC:

- Git handles code + metadata
- DVC handles large datasets/models

This avoids:

- giant Git repos
- slow clones
- corrupted histories
- binary diff nightmares