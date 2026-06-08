Prompt

The xFusionCorp Industries ML platform team is onboarding two new ML projects and needs each one organised under its own MLflow experiment rather than sharing the `Default` experiment. Your task is to register both experiments through the **MLflow UI** and tag them with the owning team.


1. The MLflow tracking server is already running on port `5000`. The **MLflow UI** button at the top of the lab can be opened to view the dashboard. One seeded experiment (`legacy-models`) is listed alongside the platform-created `Default`—both act as reference material and must not be modified.
    
2. Using the MLflow UI, register two new experiments with the experiment-level metadata below. The task is complete when both records satisfy every bullet.
    
    - **`fraud-detection`**
        
        - Experiment-level description is a non-empty string describing the project (any phrasing).
        - Experiment-level tag: key `team`, value `ml-platform`.
    - **`churn-prediction`**
        
        - Experiment-level tag: key `team`, value `analytics`.

> The result can be confirmed in the **MLflow UI**: both new experiments appear in the left-hand list, with the description and tags visible on each experiment's page.

---

Solution

**Create `fraud-detection`**

1. Open the MLflow UI → click **"Create Experiment"** (top-right or sidebar button).

![Dashboard](<../screenshots/Screenshot Day 22 MLflow dash.png>)

2. Enter name: `fraud-detection` → click **Create**.

![Create fraud-detection](<../screenshots/Screenshot Day 22 create fraud.png>)

3. You land on the experiment's page. Click the **pencil/edit icon** next to the description area and type any non-empty description (e.g. _"Fraud Detection Model"_). Save.

![Create description](<../screenshots/Screenshot Day 22 add desc fraud.png>)

4. Scroll to the **Tags** section → click **Add Tag** → key: `team`, value: `ml-platform` → Save.

![Tag ml-platform](<../screenshots/Screenshot Day 22 tag ml-platform.png>)

**Create `churn-prediction`**

1. Repeat steps 1–2 with name: `churn-prediction`.

![Create churn-prediction](<../screenshots/Screenshot Day 22 create churn.png>)

2. In the Tags section → key: `team`, value: `analytics` → Save.

![Tag analytics](<../screenshots/Screenshot Day 22 tag analytics.png>)

3. A description isn't strictly required for this experiment, but you can add one optionally. (e.g. _"Churn Prediction Model"_)



Verify all steps are completed

![Verification](<../screenshots/Screenshot Day 22 verification.png>)