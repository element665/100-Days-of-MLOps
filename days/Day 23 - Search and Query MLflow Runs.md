Prompt

A xFusionCorp Industries data scientist has accumulated ten runs in the `fraud-detection` MLflow experiment. Your task is to triage those runs via the **MLflow UI**: mark the single best-performing candidate as the shortlisted model, and flag every clearly under-performing run for removal.

1. The MLflow tracking server is already running on port `5000`, and the `fraud-detection` experiment has been pre-populated with ten runs. The runs can be viewed via the **MLflow UI** button → `fraud-detection`experiment.
    
2. Using the MLflow UI, complete the triage below. The end state is what is tested—the path taken through the UI is not.
    
    - **Shortlist the best candidate.** Among all runs where `metrics.f1_score > 0.85`, the single run with the highest `f1_score` must carry a run-level tag: key `review-status`, value `shortlisted`.
        
    - **Reject the under-performers.** Every run where `metrics.f1_score < 0.75` must carry a run-level tag: key `review-status`, value `rejected`.
        
3. The other runs (those in the 0.75 ≤ f1 ≤ 0.85 band, and the second-best shortlisting candidate) must carry no `review-status` tag at all.

---

Solution

- Click MLflow UI button

![Start](<../screenshots/Screenshot Day 23 Start.png>)

- Select fraud-detection experiment

![Dash](<../screenshots/Screenshot Day 23 MLflow dash.png>)

- Navigate to Evaluation runs

![Evaluation runs](<../screenshots/Screenshot Day 23 evaluation runs.png>)

- Filter best candidates

![Filter top](<../screenshots/Screenshot Day 23 filter top.png>)

- Tag best f1_score

![Tag shortlist](<../screenshots/Screenshot Day 23 tag shortlist.png>)

![Tag top](<../screenshots/Screenshot Day 23 top performer.png>)

- Filter under-performers

![Filter under](<../screenshots/Screenshot Day 23 filter under.png>)

- Tag rejected runs

![Tag under 1](<../screenshots/Screenshot Day 23 tag rejected 1.png>)

![Tag under 2](<../screenshots/Screenshot Day 23 tag rejected 2.png>)

- Verify task is completed by adding review-status column

![Verify](<../screenshots/Screenshot Day 23 verify task.png>)