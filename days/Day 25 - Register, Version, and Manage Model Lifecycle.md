Prompt

The xFusionCorp Industries ML platform team needs two trained candidates promoted through the **MLflow Model Registry** so the ops side can track which model version is serving production traffic. Both runs already exist in the `fraud-detection` experiment. Your task is to register both as versions of a new `fraud-detector`model, add a model-level description, and assign `challenger` and `champion` aliases—all through the MLflow UI.

  

1. The MLflow tracking server is already running on port `5000` and two runs are pre-populated in the `fraud-detection` experiment: a `baseline` run (`n_estimators=100`, `max_depth=5`, `f1_score=0.80`) and an `improved` run (`n_estimators=200`, `max_depth=10`, `f1_score=0.89`). Both runs can be opened via the **MLflow UI** button → `fraud-detection`experiment.
    
2. Using the MLflow UI, reach the end state below. The order (baseline first, improved second) matters because MLflow assigns version numbers sequentially within a registered model.
    
    - A registered model named **`fraud-detector`**exists in the Model Registry.
    - The registered model carries a non-empty description that references the word `fraud` (any phrasing; for example `Fraud detection model for xFusionCorp transactions`).
    - **Version 1** of `fraud-detector` is the baseline run and carries the alias **`challenger`**.
    - **Version 2** of `fraud-detector` is the improved run and carries the alias **`champion`**.

> The result can be confirmed by opening **Model registry** → **fraud-detector** in the MLflow UI. Two versions are listed, the description is shown at the top of the model page, and the alias column (or the Aliases field on each version) indicates `challenger` on v1 and `champion` on v2.

---

Solution

### Step 1 — Register the baseline run as Version 1

1. Open the MLflow UI (port 5000) and click the **fraud-detection** experiment.
2. Click fraud-detection from **Recent Experiments** to open its detail page.
3. Scroll down to the **Training runs** section on the left and click the model link for baseline run.
4. Click the **Register Model** button that appears on the right.
5. In the dialog, choose **Create New Model**, type `fraud-detector`, then click **Register**.

MLflow creates the `fraud-detector` registered model and assigns this run **Version 1**.

![Screenshot 1](<../screenshots/Screenshot Day 25 Step 1.png>)

---

### Step 2 — Register the improved run as Version 2

1. Use the breadcrumb or back button to return to the **fraud-detection** experiment list.
2. Click the **improved** run.
3. Scroll to **Artifacts**, click the model folder, then click **Register Model**.
4. This time, choose **Use Existing Model** and select `fraud-detector` from the dropdown.
5. Click **Register**.

MLflow assigns this run **Version 2** (sequential, so order matters — baseline must be registered first).

![Screenshot 2](<../screenshots/Screenshot Day 25 Step 2.png>)

---

### Step 3 — Add the model-level description

1. In the top navigation click **Models** (the Model Registry).
2. Click **fraud-detector** to open the model page.
3. Click the **Edit** (pencil) icon next to the Description field at the top.
4. Type a description that contains the word _fraud_, e.g.:
    
    > `Fraud detection model for xFusionCorp transactions`
    
5. Click **Save**.

![Screenshot 3](<../screenshots/Screenshot Day 25 Step 3.png>)

---

### Step 4 — Assign the `challenger` alias to Version 1

1. Still on the `fraud-detector` model page, click **Version 1** in the versions table.
2. Find the **Aliases** field and click **Add** (or the edit/pencil icon).
3. Type `challenger` and confirm/save.

![Screenshot 4](<../screenshots/Screenshot Day 25 Step 4.png>)

---

### Step 5 — Assign the `champion` alias to Version 2

1. Click the back arrow to return to the `fraud-detector` model page.
2. Click **Version 2**.
3. Find the **Aliases** field and click **Add**.
4. Type `champion` and confirm/save.

![Screenshot 5](<../screenshots/Screenshot Day 25 Step 5.png>)

---

### Verification

Navigate to **Models → fraud-detector**. You should see:

|Version|Source Run|Aliases|
|---|---|---|
|1|baseline|`challenger`|
|2|improved|`champion`|

The description at the top of the page should read your fraud-referencing text. That's the complete end state the ops team needs to track which model is serving production.

![Screenshot Verify](<../screenshots/Screenshot Day 25 Verify.png>)

---

**Key things to get right:**

- **Registration order is critical** — baseline before improved, so the version numbers are assigned correctly (1 = challenger, 2 = champion).
- Aliases are set **per-version** on the individual version detail page, not on the model overview page.
- The description is set at the **model level** (the overview page), not per-version.