# GSoC 2026 Evaluation: OmniFold Publication Tools

### Name: Harsh Chauhan

This is the evaluation task submission repo for the OmniFold publication tools project (CERN-HSF / GSoC 2026).

Task description: [gsoc2026_evaluation_task.md](https://github.com/wamorkart/omnifold-hepdata/blob/main/gsoc2026_evaluation_task.md)

Data source: [Zenodo 10.5281/zenodo.11507450](https://zenodo.org/records/11507450) (`files/pseudodata/`)

## Repository contents

**Part 1 — Exploration and Gap Analysis**
- `gap_analysis.md`: Column inventory across all three HDF5 files, missing information for reuse, and standardization challenges

**Part 2 — Metadata Schema Design**
- `metadata.yaml`: YAML schema accompanying the nominal weight file; fiducial cuts and normalization verified against the data
- `schema_design.md`: Design justification and references

**Part 3 — Coding Exercise**
- `weighted_histogram.py`: Weighted histogram function with plotting and eight pytest-compatible tests

## Quick start

```bash
# Run tests
python3 weighted_histogram.py          # standalone
python3 -m pytest weighted_histogram.py -v  # with pytest

# Use with OmniFold data
import pandas as pd
from weighted_histogram import weighted_histogram

df = pd.read_hdf("multifold.h5", key="df")
result = weighted_histogram(df["pT_ll"].values, df["weights_nominal"].values,
                            bins=50, xlabel="pT_ll [GeV]")
# result["integral"] should be ~1809 fb (published: 1808 +/- 42 fb)
```

## Key findings

- Fiducial cuts verified from data: muon pT > 25 GeV, |eta| < 2.4, m_ll in [81, 101] GeV, pT_ll > 200 GeV
- Normalization: `sum(weights_nominal) = 1809.5 fb`, matching the published total fiducial cross section
- Per-bin uncertainties use `sqrt(sum(w_i^2))`, the standard HEP prescription for weighted samples
