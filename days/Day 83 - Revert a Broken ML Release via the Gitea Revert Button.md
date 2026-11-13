Prompt

The xFusionCorp Industries ML platform team recently shipped a pull request (PR) titled **Add speculative hashing scaffold**; this PR was merged by an admin without prior review to facilitate the upcoming Wednesday release cut. Subsequently, this change has caused a lint regression, resulting in a persistent red status on the `main` branch. According to the team's rollback policy, reverts should not be executed from the command line, and force-pushes are strictly prohibited. Instead, reverts must be processed through a PR, following the same procedure used for the initial breakage. Your task is to utilize Gitea's **Revert** button on the merged PR to remove the change from the `main` branch, thereby restoring the CI status to green.

  

The Gitea UI is on port `3000` (**Gitea** button). Admin credentials: `gitea-admin` / `gitea2026`. The repo is at `http://localhost:3000/gitea-admin/fraud-detector` and a working clone is at `/root/code/fraud-detector` (on `main`). No local git commands are needed — the revert happens entirely in the Gitea UI.

The starting state: the merged PR `Add speculative hashing scaffold` (visible under **Pull Requests → Closed**) landed a regression on `main`, and the latest `CI` run on `main` (on the **Actions** tab) is **red**. The rollback path is Gitea's built-in revert: reverting the merged commit through a new revert branch and a second, reviewable revert PR — with its own `lint` + `test`checks — that merges the reverted state back onto `main`rather than force-pushing or hand-editing.

The end state must include:

- The original **Add speculative hashing scaffold** PR is still merged (reverts do not re-open the original PR).
- A second, separate PR with a title starting with `Revert`exists and is merged.
- `main`'s HEAD commit message contains `Revert`.
- `main`'s HEAD commit SHA reports combined CI status `success`.

> The Revert button is the Gitea (and GitHub) equivalent of the incident-response `pager → hotfix → revert-PR → merge` playbook. It does two things the command line does not: it creates a human-reviewable PR so the rollback is audit-traceable, and it runs the full CI pipeline against the reverted state before the revert lands on main. That is the difference between _fixing production_ and _rolling production back safely_.

---

Solution

Login to Gitea UI

![screenshot](<../screenshots/Screenshot Day 83 Gitea login.png>)

Navigate to 'fraud-detector' repo

![screenshot](<../screenshots/Screenshot Day 83 select repo.png>)

Click on the latest commit '1faf92bcf1'

![screenshot](<../screenshots/Screenshot Day 83 select commit.png>)

Click on the 'Operations' button in the top right

![screenshot](<../screenshots/Screenshot Day 83 commit details.png>)

Select 'Revert' from the drop-down

![screenshot](<../screenshots/Screenshot Day 83 select revert.png>)

Click the 'Revert' button since 'main' is already selected

![screenshot](<../screenshots/Screenshot Day 83 revert popup.png>)

 Edit commit title and select create new branch option; then click 'Propose file change' button

![screenshot](<../screenshots/Screenshot Day 83 propose file change.png>)

Select 'New Pull Request'

![screenshot](<../screenshots/Screenshot Day 83 new PR.png>)

Confirm PR starts with 'Revert' and click 'Create Pull Request'

![screenshot](<../screenshots/Screenshot Day 83 confirm PR.png>)

Click 'Create merge commit' button

![screenshot](<../screenshots/Screenshot Day 83 create merge commit.png>)

Confirm all checks pass and that 'Pull request successfully merged and closed'

![screenshot](<../screenshots/Screenshot Day 83 confirm checks.png>)

---
### Verification

Confirm original PR is still merged

```shell
TOKEN=$(cat /root/.gitea/token)

curl -s -H "Authorization: token $TOKEN" "http://localhost:3000/api/v1/repos/gitea-admin/fraud-detector/pulls" | jq '.[1].title, .[1].body, .[1].state'
```

Output

```shell
"Add speculative hashing scaffold"
"Preparatory hook for a hashing feature we may add later. Reviewed in-band."
"closed"
```

Confirm separate PR with Revert in title

```shell
curl -s -H "Authorization: token $TOKEN" "http://localhost:3000/api/v1/repos/gitea-admin/fraud-detector/pulls" | jq '.[0].title'
```

Output

```shell
"Revert \"feat(train): speculative hashing scaffold\""
```

Confirm main's HEAD commit message contains 'Revert'

```shell
curl -s -H "Authorization: token $TOKEN"   'http://localhost:3000/api/v1/repos/gitea-admin/fraud-detector/branches/main' | jq '.commit.message'
```

Output

```shell
"Merge pull request 'Revert \"feat(train): speculative hashing scaffold\"' (#2) from gitea-admin-patch-1 into main\n\nReviewed-on: https://3000-port-ba5mmlqvqargmq6j.labs.kodekloud.com/gitea-admin/fraud-detector/pulls/2\n"
```

Confirm main's HEAD commit SHA reports combined CI status 'successful'

```shell
COMMIT_SHA=$(curl -s -H "Authorization: token $TOKEN"   'http://localhost:3000/api/v1/repos/gitea-admin/fraud-detector/branches/main' | jq -r '.commit.id')

curl -s -H "Authorization: token $TOKEN" "http://localhost:3000/api/v1/repos/gitea-admin/fraud-detector/commits/$COMMIT_SHA/status" | jq '{"Status": .state}'
```

Output

```shell
{
  "Status": "success"
}
```
