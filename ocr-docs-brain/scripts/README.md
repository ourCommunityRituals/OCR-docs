# Brain enforcement scripts

This directory ships the Python scripts that **enforce** the contracts
declared by the YAML files in `ocr-docs-brain/` (registry, taxonomy,
flags, invariants, etc.). They live next to the Brain content so a
single PR can update both a contract shape *and* the code that checks
for drift against it — no cross-repo coordination required.

## Why these scripts live in OCR-docs, not in the workspace root

The OCR-docs repo is the Brain — governance, ADRs, parseable contracts,
enforcement schemas. The workspace root (`ourCommunityRituals`) is for
shared *toolchain*: pnpm-workspace, runner provisioning, build-tool
config. These scripts are not toolchain — they encode the Brain's
shape. Putting them anywhere else fractures the source-of-truth.

If you're adding a new conformance check, add it here. If you're adding
a new Brain YAML, add the matching enforcement here in the same PR.

## Scripts

### `check_brain_contract.py`

Compares a product repo's actual state against what the OCR-docs brain
declares and writes a JSON conformance report.

```
python3 check_brain_contract.py \
  --brain <path-to-ocr-docs-brain> \
  --repo <path-to-product-repo> \
  --product-id <ose|osm|oaw|wkrp|osg|osr|osp> \
  --report-path conformance-report.json
```

Exit codes:
- `0` — conformant (or skipped per `code_present: false`)
- `1` — drift detected (details in `--report-path`)
- `2` — execution error (brain unreachable, product repo malformed,
  unknown `product-id`)

Stub-repo skip: when `product-registry.yaml` marks a product
`code_present: false`, the script writes a single `[SKIP]` PASS report
and exits 0. The propagator still updates docs/standards into the stub
repo; only the code-presence checks are suspended until the repo
onboards real application code.

Depends on `pyyaml` and `packaging` only (`pip install pyyaml packaging`).

### `open_drift_ticket.py`

Wraps `check_brain_contract.py`'s JSON report and opens a Linear ticket
when drift is detected on a PR. Posts a summary back to the PR.

Inputs (env vars):
- `LINEAR_API_KEY` — secret
- `GITHUB_TOKEN` — secret
- `PR_URL`, `PR_NUMBER`, `PR_AUTHOR`, `COMMIT_SHA`, `REPO_NAME` — pull
  request context

## How consumer repos invoke these scripts

Each product repo's `.github/workflows/brain-contract-check.yml` does
**two** checkouts: its own code, and `ourCommunityRituals/OCR-docs`.
The scripts then run from the OCR-docs checkout path.

Example shape (paste into a new consumer repo's workflow):

```yaml
- name: Checkout OCR-docs brain
  uses: actions/checkout@v4
  with:
    repository: ourCommunityRituals/OCR-docs
    path: ocr-docs
    ref: main
    token: ${{ secrets.OCR_PROPAGATE_TOKEN }}

- name: Run brain conformance
  run: |
    python3 ocr-docs/ocr-docs-brain/scripts/check_brain_contract.py \
      --brain ocr-docs/ocr-docs-brain \
      --repo .  \
      --product-id <product-id> \
      --report-path conformance-report.json
```

Note: pre-2026-05-15 workflows added a *third* checkout of the workspace
root (`ourCommunityRituals/ourCommunityRituals`) because the scripts
used to live at `packages/ocr-ci-scripts/`. That third checkout is no
longer needed — drop it when you next touch your workflow.

## Migration history

- **2026-05-15** — Relocated from `ourCommunityRituals` workspace root
  (`packages/ocr-ci-scripts/`) into OCR-docs alongside the Brain content.
  The script enforces Brain shape; the two evolve together.
  - Same PR added the stub-repo skip: products with `code_present: false`
    in `product-registry.yaml` exit 0 with a single SKIP report instead
    of failing the three code-presence checks. Fixes the noisy CI on OSM
    propagator PRs.
- **2026-04-19** — Originally extracted from 4 app repos that had
  diverged only by app name. Centralized into the workspace root.
  - Same commit hardened `open_drift_ticket.py`:
    - `api_key.strip()` defends against re-pasted secrets with trailing
      whitespace (the 401 failure mode that triggered the centralization).
    - `verify_auth()` preflight fails fast with a rotation-instruction
      `::error::` annotation instead of an opaque `get_team_id` crash.

## When to update what

- **Brain YAML shape changes** → update `check_brain_contract.py` in
  the same PR. Reviewers can see the contract diff and the enforcement
  diff together.
- **New product onboards** → add the entry to `product-registry.yaml`;
  no script change required unless the product introduces a new check
  type.
- **Stub repo onboards real code** → flip `code_present: true` (or
  remove the line) in `product-registry.yaml`; the script picks it up
  automatically.
