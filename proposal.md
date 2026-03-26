# GSoC 2026 Proposal: Publication of OmniFold Weights

## Basic Information

| Field            | Details                                                                          |
|------------------|----------------------------------------------------------------------------------|
| **Name**         | Harsh Chauhan                                                                    |
| **Institute**    | Indian Institute of Technology Dharwad (IIT Dharwad)                            |
| **Degree**       | B.Tech Engineering Physics, Junior Year                                          |
| **Email**        | harsh2005.hc@gmail.com                                                           |
| **GitHub**       | [harz05](https://github.com/harz05)                                              |
| **LinkedIn**     | [harsh-chauhan-912ba2280](https://www.linkedin.com/in/harsh-chauhan-912ba2280/)  |
| **Timezone**     | Indian Standard Time (UTC +5:30)                                                 |
| **Project Size** | 175 hours                                                                        |
| **Mentors**      | Tanvi Wamorkar, Benjamin Nachman                                                 |

---

## Project Overview

Modern particle physics experiments are increasingly relying on machine learning for
unfolding, the process of correcting detector-level measurements back to particle-level
distributions. OmniFold, introduced by Andreassen et al. (2020), replaces the traditional
binned histogram approach with per-event reweighting through iterative classifier training.
A single published set of per-event weights lets users compute any observable at particle
level without re-running the analysis. ATLAS demonstrated this at scale in 2024, publishing
the first 24-dimensional unbinned differential cross section measurement of Z+jets
observables ([arXiv:2405.20041](https://arxiv.org/abs/2405.20041)).

However, when that result was released, the per-event weights were published as raw HDF5
arrays with no embedded metadata: no fiducial definition, no normalization convention,
no documentation of what each weight column represents. A user downloading those files
cannot correctly apply the weights without reading the full analysis paper. There is no
standard format, no schema, and no reinterpretation tooling. This project addresses that
gap by producing a Python package with a formal schema, standardized I/O, an analysis
API for applying and propagating weights, and reference examples covering the full
workflow from unfolding output through to HEPData submission where time permits.

---

## Motivation and Problem Statement

1. **Per-event weights are context-dependent**

   Traditional unfolding results are fixed: a binned cross section with uncertainties fits
   cleanly into a HEPData table and is self-contained. Per-event weights are not. They are
   only meaningful relative to a specific event selection, a normalization convention, and
   the MC generator used as a prior. Publishing them without documenting these choices produces
   a result that is technically open but practically unusable for reinterpretation.

2. **The ATLAS Z+jets measurement is the concrete evidence**

   The most complete OmniFold result published to date ([arXiv:2405.20041](https://arxiv.org/abs/2405.20041))
   shows what this looks like in practice. The HDF5 TITLE attribute is empty across all three
   files. Generator identity is only recoverable from the filename. The fiducial selection,
   normalization convention, and weight semantics are absent from the files entirely.

3. **The missing fiducial definition is the most dangerous gap**

   OmniFold weights are only valid inside the phase space used to derive them. Applying them
   outside that region produces wrong results without any warning. In standard ATLAS and CMS
   unfolding publications, the fiducial definition is the first thing documented precisely
   for this reason.

4. **Undocumented weight semantics block uncertainty estimation**

   The nominal file contains 178 weight columns across ensembles, bootstraps, and systematics.
   Nothing in the files documents what each type measures, which to use for statistical
   uncertainties, or why coverage differs across the three files. A user has no path to a
   correct uncertainty band without the paper.

5. **The normalization convention is undocumented**

   Analyzing the files from the [Zenodo record](https://zenodo.org/records/11507450) directly:
   `sum(weights_nominal)` in the nominal file is 1808.3 fb, matching the published total
   fiducial cross section of 1808 ± 42 fb. The weights are absolute cross sections in
   femtobarns. None of this is written anywhere in the files. A user has no way to know the
   unit or verify the normalization without reading the paper. The mean weight in the Sherpa
   file (~0.0056) is slightly higher than in the nominal file (~0.0043), but only because
   Sherpa has fewer events (326k vs 418k) at the same total cross section. That too is
   undocumented and without knowing the convention, the difference looks arbitrary.

6. **No community standard exists**

   Every collaboration that runs OmniFold currently defines its own output format, naming
   scheme, and documentation level. A 2025 review of unbinned unfolding tools
   ([arXiv:2503.09720](https://arxiv.org/abs/2503.09720)) notes that "there are currently
   no standard tools for doing the measurements themselves," and separately that standard
   tools for presenting the results of ML-based measurements remain an open problem. This
   project addresses the second gap.

7. **HEPData cannot host the primary output of the method**

   Designed around binned tables, the platform has a 100 MB per-file limit and no native
   data model for per-event arrays. The ATLAS record ends up with 26 binned summary tables
   on HEPData and the actual unbinned result on Zenodo connected by a text link. The primary
   output of the method lives outside the primary data repository.

---

## Deliverables

### Core Deliverables

- **Formal schema v1.0 with validation** : versioned YAML/JSON schema covering metadata,
  observable definitions, weight conventions, model and training details, dataset provenance,
  and normalization; validated with Pydantic models and a JSON Schema spec defining required
  vs optional fields

- **Standardized weight container** : plain HDF5 layout specification and Parquet format
  support via an `OmniFoldResult` class with `save()` and `load()`; covers nominal weights,
  ensemble and bootstrap weights, and systematic variations with consistent naming conventions
  and indexing

- **Format converter** : utility to read existing PyTables-based OmniFold files (such as
  the public ATLAS Z+jets dataset) and write them into the new standardized format; makes
  the package immediately testable against real published data from the first week

- **Analysis and reinterpretation API** : user-facing Python API to load published weights,
  apply fiducial cuts, compute arbitrary observables, propagate statistical and systematic
  uncertainties via ensemble and bootstrap methods, and produce publication-quality plots
  with mplhep styling

- **Validation suite** : standardized procedures for closure tests, normalization checks
  against known cross sections, iteration stability, and cross-file consistency; each check
  returns structured pass/fail output with diagnostic information

- **Reference Jupyter notebooks** : complete worked examples using the public ATLAS Z+jets
  dataset demonstrating the full workflow: publishing OmniFold outputs, loading and applying
  weights, reproducing published observables, and computing new observables post-publication

### Stretch Goals

- **HEPData integration layer** : mapping OmniFold results to HEPData records using
  hepdata-lib, submission templates, Zenodo DOI linking for external file references, and
  metadata conventions for unbinned results

- **Sphinx documentation site** : auto-generated API reference hosted on ReadTheDocs,
  covering all public classes and functions with usage examples

---

## Plan of Action



### 1. Schema v1.0  *(Weeks 1-2 | May 25 - Jun 7)*

**Objective:** Establish a formal versioned schema that every other component of the package depends on for metadata embedding, file validation, and normalization checks.

**Deliverables:**
- Pydantic `BaseModel` hierarchy covering dataset, fiducial definition, observables, weight groups, unfolding provenance, optional model info, and file format
- Generated JSON Schema file for programmatic validation
- pytest-tested Pydantic models with the ATLAS Z+jets dataset as a reference instance against the spec

The schema is the foundation everything else builds on. The weight container needs it to
embed metadata, the API needs it to validate loaded files, and the validation suite needs
it to check normalization conventions. I will extend the `metadata.yaml` v0.1.0 from the
evaluation task into a formal versioned spec, adding the model and training provenance
section that was left as TODO, formalizing required vs optional fields, and generating a
JSON Schema from Pydantic `BaseModel` definitions for programmatic validation.

The top-level Pydantic model capturing the full schema hierarchy is as follows:

```python
class OmniFoldMetadata(BaseModel):
    schema_version: str
    dataset: DatasetInfo           # process, experiment, energy, references
    fiducial_definition: FiducialDef   # structured cuts, not free text
    observables: list[Observable]  # name, latex, unit, dtype
    weights: list[WeightGroup]     # category, semantics, present_in, index_range
    unfolding: UnfoldingProvenance # iterations, architecture, features, convergence
    model: Optional[ModelInfo] = None # checkpoints, hyperparams, preprocessing
    file_format: FileFormatInfo    # reading instructions, format, layout
```

### 2. Standardized Weight Container and Format Converter  *(Weeks 3-4 | Jun 8 - Jun 21)*

**Objective:** Build `OmniFoldResult`, the central I/O class, and a format converter that makes the package immediately testable against the most complete published OmniFold dataset available.

**Deliverables:**
- `OmniFoldResult` class with `save()` and `load()` for plain HDF5 (h5py) and Parquet (pyarrow), schema embedded as file metadata in both formats
- Documented HDF5 group layout specification with consistent naming for nominal, statistical, and systematic weight groups
- Format converter reading existing PyTables-based OmniFold files and writing to the standardized layout
- pytest tests for the container, layout spec, and converter against the public ATLAS Z+jets files

I will implement `OmniFoldResult` with a plain h5py HDF5 layout, making the files directly readable by ROOT, C++, and Julia without any pandas dependency. Parquet support via pyarrow will be added alongside, with the schema embedded as key-value metadata in the file header. Both formats support the full weight structure from the gap analysis: nominal weights, ensemble and bootstrap weights, and systematic variations under consistent named groups.

Alongside the container I will build a format converter that reads existing PyTables-based OmniFold files, maps the known column structure onto the new layout, validates against the schema, and writes out in the standardized format. The converter makes the package immediately useful against the most complete published OmniFold dataset available.

The proposed HDF5 group layout is:

```
/metadata        ← JSON-serialized OmniFoldMetadata (schema v1.0)
/observables/    ← one dataset per observable (pT_ll, y_ll, ...)
/weights/
    nominal/     ← weights_nominal
    statistical/ ← weights_ensemble_{i}, weights_bootstrap_mc_{i}, weights_bootstrap_data_{i}
    systematic/  ← weights_pileup, weights_muon_eff, weights_theory, ...
```

The `OmniFoldResult` interface covering save, load, and conversion looks like this:

```python
# save to either format based on file extension
result.save("output.h5")
result.save("output.parquet")

# load back with schema validation
result = OmniFoldResult.load("output.h5")

# convert existing PyTables file to standardized format
from omnifold_pub import convert
convert("multifold.h5", "multifold_standard.h5", metadata="metadata.yaml")
```

### 3. Analysis and Reinterpretation API  *(Weeks 5-8 | Jun 22 - Jul 17)*

**Objective:** Implement the user-facing analysis layer that takes a loaded weight file and produces correctly uncertainty-propagated, publication-quality results.

**Deliverables:**
- `apply_fiducial_cut`: reads structured cuts from the loaded schema and applies numpy boolean masks on event arrays
- `histogram`: wraps the `weighted_histogram` function from the evaluation task, adds observable lookup by name and automatic axis labelling from the schema
- `uncertainty_band`: propagates ensemble spread, bootstrap variance, and systematic shifts as three distinct uncertainty types
- `plot`: publication-ready output with mplhep ATLAS styling, step histograms, error bars, and optional theory overlay panel

`apply_fiducial_cut` reads the structured cuts from the loaded schema and applies them as
numpy boolean masks on the event arrays. The `histogram` method wraps the
`weighted_histogram` function developed during the evaluation task, adding observable
lookup by name and automatic axis labelling from the schema. The `uncertainty_band` method
handles the three uncertainty types the ATLAS files carry: ensemble spread across the 100
independently trained networks, bootstrap variance across the 25 MC and 25 data resamples,
and systematic shifts computed as the per-bin difference from nominal. The `plot` method
produces publication-ready output using mplhep ATLAS styling with step histograms, error
bars, and an optional theory overlay panel.

The core methods (`load`, `apply_fiducial_cut`, `histogram`) will be complete and
tested by the midterm on July 10. The uncertainty propagation and plotting methods
will follow in the two weeks after, completing this phase by July 17.

### 4. Validation Suite  *(Weeks 7-9 | Jul 11 - Aug 3)*

**Objective:** Extend the five existing checks in `validate.py` with four new checks covering closure, normalization against published cross sections, cross-file consistency, and full iteration stability.

**Deliverables:**
- Closure test: runs OmniFold on MC pseudo-data and verifies output weights converge to unity, confirming algorithm recovery when data and MC agree
- Normalization check: compares `sum(weights_nominal)` against a user-supplied expected cross section within configurable tolerance
- Cross-file consistency check: verifies observable columns match across nominal, generator systematic, and sample composition files
- Iteration stability check: tracks the full convergence curve across all iterations, not just the last two
- All checks follow the existing `ValidationReport` pattern returning structured pass/fail output with diagnostic values; pytest-tested with documented thresholds

The reference repository already has five numerical weight checks in `validate.py`:
finite values, extreme weight ratios, effective sample size, convergence between
iterations, and normalization. I will extend this foundation rather than replace it,
adding the four checks the current code does not cover. All new checks follow the existing
`ValidationReport` pattern, returning structured pass/fail output with diagnostic values
so results are machine-readable and easy to act on.

### 5. Reference Notebooks  *(Weeks 10-11 | Aug 3 - Aug 14)*

**Objective:** Produce three end-to-end Jupyter notebooks using the public ATLAS Z+jets dataset that demonstrate the complete workflow from publishing to post-publication reinterpretation.

**Deliverables:**
- **Publishing workflow:** load the standardized weight file, inspect the embedded schema,
  and walk through the complete output structure a physicist would submit to Zenodo alongside
  a paper
- **Reproducing a published observable:** apply fiducial cuts, compute the pT_ll differential
  cross section, produce an uncertainty band using ensemble and bootstrap weights, and
  cross-check the integral against the published 1808 ± 42 fb value
  ([arXiv:2405.20041](https://arxiv.org/abs/2405.20041))
- **Computing a new observable:** use the same weights to histogram an observable not in
  the original paper, demonstrating that the unbinned result enables post-publication
  reinterpretation without re-running the analysis

All three notebooks will run cleanly end-to-end against the public dataset and serve as
the primary reference documentation for the package.

### 6. Stretch Goals  *(Week 12 | Aug 14 - Aug 17, if time permits)*

**Objective:** If the five core phases finish ahead of schedule, extend the package with
HEPData submission tooling and a hosted documentation site.

HEPData integration is stretch because mapping unbinned results onto a platform built
for binned tables involves open design decisions that depend on mentor and community
feedback during the project. Sphinx documentation is straightforward to build but only
becomes useful once the public API is fully stable, which happens at the end of the
project rather than midway through.

**Deliverables (time permitting):**
- **HEPData integration layer:** `to_hepdata()` method on `OmniFoldResult` using
  hepdata-lib to generate a submission with Zenodo DOI linking for the external weight
  files, binned summary tables derived from the nominal weights for the HEPData record,
  and metadata conventions for marking a result as unbinned
- **Sphinx documentation site:** auto-generated API reference for all public classes and
  functions, hosted on ReadTheDocs, with usage examples pulled from the reference notebooks

---

## Timeline

| Dates | Activities |
|---|---|
| **Community Bonding**<br>May 1 - May 24 | • Study hep-lbdl/OmniFold and ViniciusMikuni/omnifold codebases; review ATLAS Z+jets GitLab code<br>• Align with mentors on schema field priorities and API design<br>• Set up package skeleton and development environment |
| **Weeks 1-2**<br>May 25 - Jun 7 | • Extend metadata.yaml to full Pydantic BaseModel hierarchy<br>• Generate JSON Schema from Pydantic models<br>• Write pytest tests; validate schema against ATLAS Z+jets dataset<br>• **Deliverable:** Schema v1.0 with Pydantic validation and JSON Schema output |
| **Weeks 3-4**<br>Jun 8 - Jun 21 | • Implement OmniFoldResult with plain HDF5 (h5py) and Parquet (pyarrow)<br>• Build format converter for existing PyTables-based OmniFold files<br>• Write pytest tests against public ATLAS Z+jets files<br>• **Deliverable:** Standardized weight container and format converter |
| **Weeks 5-6**<br>Jun 22 - Jul 5 | • Implement apply_fiducial_cut and histogram (core API methods)<br>• Write tests for core methods against ATLAS Z+jets dataset |
| **Midterm Evaluation**<br>Jul 6 - Jul 10 | • Core API (load, apply_fiducial_cut, histogram) complete and tested against ATLAS Z+jets data<br>• Schema, container, and format converter passing all tests |
| **Weeks 7-9**<br>Jul 11 - Aug 3 | • Implement uncertainty_band (ensemble, bootstrap, systematic)<br>• Implement plot with mplhep ATLAS styling<br>• Implement closure test, normalization check, cross-file consistency, and iteration stability checks<br>• Write pytest tests with documented pass/fail thresholds<br>• **Deliverable:** Full analysis API and validation suite with 9 total checks |
| **Weeks 10-11**<br>Aug 3 - Aug 14 | • Write publishing workflow notebook<br>• Write reproducing published observable notebook<br>• Write computing new observable notebook<br>• **Deliverable:** Three end-to-end notebooks running against public ATLAS Z+jets data |
| **Week 12**<br>Aug 14 - Aug 17 | • HEPData integration layer via hepdata-lib (if time permits)<br>• Sphinx documentation site on ReadTheDocs (if time permits)<br>• **Deliverable (stretch):** HEPData submission tooling and hosted API docs |
| **Final Evaluation**<br>Aug 17 - Aug 24 | • All core deliverables complete, tested, and documented |

---

## About Me

I am Harsh Chauhan, a third year undergraduate in Engineering Physics at IIT Dharwad with
a CGPA of 8.63. My major sits at the intersection of physics and computation and most of
my project work over the past two years has followed that same line. I have taken courses
in quantum mechanics, statistical physics, electrodynamics and numerical methods alongside
data structures and deep learning.

CERN-HSF is the only GSoC organization I am applying to. The reason is that
software written here is load-bearing for real physics results. An improvement to a parser,
a data format or an analysis tool has direct downstream consequences for measurements at
ATLAS or CMS, not for a library that may or may not see use. That connection between
software and experiment is what I want to work on and it exists at CERN-HSF.


What draws me to this project specifically is the open data problem it addresses. The
ATLAS Z+jets measurement published in 2024 is the most complete OmniFold result published
to date, yet a physicist downloading those files cannot correctly apply the weights
without reading the full paper. For the evaluation task I audited those three files,
identified seven categories of missing metadata and designed a schema to address them.
The GSoC project is asking me to build what the evaluation task was diagnosing.

My primary languages for scientific work are Python and C++. Some relevant projects are as follows:

- My [physics-aware diffusion model](https://github.com/harz05/PA_Diffusion) (48M
  parameters) for underwater image enhancement used a Mamba-based backbone and
  incorporated physical light propagation constraints into the architecture. This
  gave me direct experience translating physics intuition into ML design decisions.
  My main contribution was the Mamba backbone and a physics-informed loss function.
- At Inter-IIT Tech Meet 2024 I worked on solving the [FedEx 3D bin packing problem](https://github.com/harz05/FedEx-InterIITTech13)
  (strongly NP-hard) under time constraints. Our team used spatial data structures for free-space
  management. My main contribution was the greedy and genetic algorithm approach. It was a good project to enhance my algorithmic thinking under pressure.

## Prior Contributions

**hep-lbdl/OmniFold** (the reference repository for this project):

- Open [PR #16](https://github.com/hep-lbdl/OmniFold/pull/16) — Added `validate.py` with five
  diagnostic checks for weight quality: finite values, extreme weight ratios, effective sample size,
  convergence between iterations, and normalization. Also fixed `reweight()` to handle saturated
  classifier outputs. Addresses [Issue #15](https://github.com/hep-lbdl/OmniFold/issues/15).
- [Issue #17](https://github.com/hep-lbdl/OmniFold/issues/17) — Identified that `omnifold()`
  initializes per-event weights as `np.ones()`, which silently produces wrong results when MC
  generators like MadGraph5 or Sherpa produce non-uniform prior weights.
- Open [PR #14](https://github.com/hep-lbdl/OmniFold/pull/14) — Cleanup: remove stale PDF from
  the img directory.

**hep-lbdl/CaloGAN**:

- Open [PR #18](https://github.com/hep-lbdl/CaloGAN/pull/18) — PyTorch port of CaloGAN,
  porting the original Keras codebase while keeping it separate under `models/pytorch/`.
  Includes custom layers, a three-stream LAGAN generator, discriminator, and full training pipeline.

**Evaluation task** ([github.com/harz05/gsoc-omnifold-evaluationTask](https://github.com/harz05/gsoc-omnifold-evaluationTask)):

Three-part submission on the public ATLAS Z+jets OmniFold dataset: gap analysis of the three
published HDF5 files identifying seven categories of missing metadata; a versioned YAML metadata
schema with structured fiducial cuts, weight semantics, and normalization documentation; and
`weighted_histogram.py`, a weighted histogram module with eight tests covering negative weights,
empty input, and variable binning.

**root-project/ROOT**:

- Merged [PR #21683](https://github.com/root-project/root/pull/21683) — Fixed an infinite loop
  in `ROperator_Reduce.hxx` in SOFIE's ONNX inference engine, reported via
  [Issue #21682](https://github.com/root-project/root/issues/21682).

## Availability and Communication

My college break runs from May 7 to July 30 with no other commitments, during which I can
dedicate 35 to 40 hours per week. Once college resumes I will be in my final year with a
lighter credit load and can commit 20 to 25 hours per week, comfortably covering the
175-hour project scope. My mid-sem exams run from September 21 to 26 and I will flag this
in advance. I may travel briefly during the summer break and will responsibly keep my
mentors updated on any such plans or emergencies.

I am available over email, Discord, Gitter and LinkedIn. My timezone is IST (UTC+5:30) and
I am flexible with working hours, comfortable any time between 10 AM to 3 AM on weekdays
and 8 PM to 4 AM on weekends.

## Post GSoC

The 175-hour scope covers the core package. HEPData integration is the natural next step
and I plan to continue that work after the programme ends. More broadly, I want to stay
involved in standardizing how unbinned unfolding results are published. The gap this project
addresses exists across multiple experiments, not just the one ATLAS measurement that
motivated it.
