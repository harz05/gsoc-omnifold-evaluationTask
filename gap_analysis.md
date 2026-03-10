# Gap Analysis: OmniFold HDF5 Weight Files

## 1. Column Inventory

All three files share the same 22 physics observables but diverge significantly in which weights they include.

### Observables

These are per-event kinematic quantities at particle level, present in all three files.

The dilepton system (the Z boson proxy) is described by `pT_ll` and `y_ll`. Each lepton has its own kinematics: `pT_l1`, `pT_l2`, `eta_l1`, `eta_l2`, `phi_l1`, `phi_l2`. The two track jets each carry four kinematic variables (`pT`, `y`, `phi`, `m`), three N-subjettiness variables (`tau1`, `tau2`, `tau3`), and a track multiplicity count (`Ntracks`). All of these represent truth-level quantities that the unfolding is trying to recover.

### Weights

`weight_mc` is the raw Monte Carlo generator weight before any unfolding, present in all three files. `weights_nominal` is the main OmniFold output — the per-event weight that corrects for detector effects — also present in all three files.

Beyond that, the files diverge. The nominal file (`multifold.h5`) contains 100 ensemble members (`weights_ensemble_0` through `weights_ensemble_99`), 25 MC bootstraps, 25 data bootstraps, a data-driven reweighting pair (`weights_dd`, `target_dd`), and a full set of experimental systematic weights covering pileup, muon efficiency and calibration, track reconstruction, theory modelling, and luminosity — 22 systematic weight columns in total. The Sherpa file has the nominal weight and 25 MC bootstraps but nothing else. The nonDY file has only `weight_mc` and `weights_nominal`, with no uncertainty quantification at all.

### Summary table

| File | Events | Columns | Generator | Purpose |
|------|--------|---------|-----------|---------|
| `multifold.h5` | 418,014 | 200 | MadGraph5 | Nominal result |
| `multifold_sherpa.h5` | 326,430 | 51 | Sherpa | Generator systematic |
| `multifold_nonDY.h5` | 433,397 | 26 | MadGraph5 | Sample composition systematic |

---

## 2. Missing Information for Reuse

The core problem is that all three files are raw arrays with no context attached. Someone who did not run the original analysis has no way to correctly interpret or apply these weights.

**No file-level metadata.** The HDF5 `TITLE` attribute is empty in all three files. Nothing inside the files records what physics process this is, what experiment produced it, what center-of-mass energy was used, or what the analysis corresponds to. The generator names MadGraph5 and Sherpa are only inferrable from the filenames — they are not written anywhere inside the files themselves. If someone renames the files or downloads them without context, this information is gone.

**No phase space definition.** There is no documentation of what event selection was applied: lepton pT thresholds, eta acceptance, jet pT cuts, overlap removal criteria, or how the dilepton mass window was chosen. This is arguably the most critical missing piece. OmniFold weights are only valid within the fiducial region used to derive them. Applying `weights_nominal` to events outside that selection will produce incorrect results without any warning. In traditional ATLAS or CMS unfolding publications, the particle-level fiducial definition is always the first thing documented, precisely because the corrected cross sections are meaningless without it.

**No normalization convention.** It is not stated whether `weights_nominal` represents an absolute cross section in some unit (fb, pb), a weight normalized so the sum equals 1, or a relative correction to the MC prior. Looking at the numbers, the mean of `weights_nominal` in the Sherpa file is around 0.14, while the bootstrap weights in the nominal file have a mean of around 0.004. These are on completely different scales with no explanation provided.

**No description of what the different weight types mean.** The distinction between `weights_ensemble`, `weights_bootstrap_mc`, and `weights_bootstrap_data` is not documented anywhere. A user cannot determine from the files alone which set of weights to use for statistical uncertainty bands, or whether the ensemble spread and bootstrap spread are measuring the same thing or different things.

**No OmniFold training provenance.** The number of iterations, the input observables fed to the classifier, the ML architecture used, and the convergence criterion are all absent. These matter because OmniFold results depend on the prior (the MC generator) and regularize via early stopping — both of which affect how the weights should be interpreted and how much prior dependence remains.

**Inconsistent weight availability across files.** The systematic files are missing most of the uncertainty quantification that the nominal file has. The nonDY file has no bootstraps at all. There is no documentation explaining whether this is intentional (i.e., those uncertainty sources are assumed negligible for generator comparisons) or simply incomplete. A user has no way to know.

**No units on observable columns.** It is conventional in HEP to report pT and mass in GeV, but this is not written anywhere in the files. A user from a different experiment or field cannot assume this.

---

## 3. Challenges in Standardization

**Naming conventions differ across experiments.** ATLAS, CMS, and LHCb use different column naming schemes for the same physics quantities. Even within one experiment, different analyses use different conventions for systematic weight naming. A standard schema either needs a controlled vocabulary that everyone agrees to adopt, or a mapping layer that translates between conventions — neither of which is easy to establish across collaborations.

**Weight semantics are analysis-dependent.** Whether `weights_nominal` sums to a fiducial cross section, is normalized to unity, or is relative to the MC prior is a choice that differs across analyses. Enforcing a single normalization convention would break compatibility with existing workflows. The standard would need to mandate documentation of the convention without mandating the convention itself.

**HEPData has a 100MB per-file upload limit.** The nominal file here is roughly 200-300MB, and the systematic files are around 150MB each. None of them can be directly submitted to HEPData as-is. The practical solution — hosting on Zenodo and linking from HEPData — is already what this dataset does, but it means the per-event weights live outside the primary data repository, which fragments the record. A standard needs to specify how this split between HEPData metadata and external weight storage should be handled.

**Unbinned outputs do not fit the HEPData data model.** HEPData was designed around binned tables: a set of bin edges, central values, and uncertainties. Per-event weight arrays have no natural representation in that model. Mapping OmniFold outputs into HEPData requires either defining a new resource type or reducing the unbinned result to some binned summary for the primary record, both of which require community agreement.

**The PyTables/pandas HDF5 format is ecosystem-specific.** These files can only be read straightforwardly with pandas `read_hdf`, which assumes a specific internal group structure that is not part of the HDF5 standard. A reader from a C++ or Julia environment would need to reverse-engineer the layout. A format standard should either move to plain HDF5 groups with documented structure, or to a format like Parquet that has broader multi-language support.
