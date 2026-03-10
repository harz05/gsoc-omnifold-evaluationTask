# Schema Design Justification

## Why this structure

The schema is organized around the question a downstream user would actually ask when encountering these weight files for the first time: *What is this data, where is it valid, and how do I use it?* Every top-level section maps to one of those questions.

**`dataset`** answers *what is this?* — the physics process, collision energy, experiment, and links to the reference paper and data record. This is the information that was completely absent from the HDF5 files and only recoverable from the Zenodo landing page or the filename convention.

**`fiducial_definition`** answers *where is it valid?* — the particle-level event selection that defines the region in which the unfolded weights are meaningful. This is structured as a set of object definitions (leptons, dilepton system, jets) with explicit cut values rather than a free-text description, because cut values are what a user needs to actually apply a selection programmatically. Several of the cut values were verified directly from the data files: the subleading muon pT floor at 25 GeV, |η| < 2.4, a dilepton mass window of 81–101 GeV (mZ ± 10 GeV), and the hard pT_ll > 200 GeV threshold. The distinction between the reported fiducial cut (pT_ll > 200 GeV) and the internal unfolding boundary (190 GeV) is recorded because it matters for anyone trying to reproduce the measurement or understand edge effects near the phase space boundary.

**`observables`** answers *what are the columns?* — each observable gets a column name (matching the HDF5 key), a LaTeX-style physics name, a human description, and a unit. The `dtype` field is included only where it matters (integer track multiplicity), defaulting to float64 otherwise.

**`weights`** answers *how do I use the weights?* — this is the most detailed section because it addresses the largest gap identified in Part 1. Every weight column is assigned a `category` (nominal, statistical_uncertainty, experimental_systematic, theory_systematic, etc.) and a `description` that tells the user what the weight represents and what to do with it. Indexed weights (ensembles, bootstraps) use a template notation (`weights_ensemble_{i}`) with an explicit `index_range` and `count`, rather than listing all 100 entries individually. The `present_in` field records which files contain each weight, directly addressing the inconsistency across files flagged in the gap analysis. The `normalization_convention` field was verified empirically: `sum(weights_nominal)` over the nominal file yields 1809.5 fb, matching the published fiducial cross section of 1808 ± 42 fb, confirming the weights are absolute cross sections in femtobarns.

**`files`** answers *what are the different files and how do they relate?* — each file gets a `role` (nominal, generator_systematic, sample_composition_systematic) and generator provenance. This solves the problem that the generator identity was only inferrable from filenames.

**`unfolding`** records the OmniFold training provenance — iterations, architecture, input features, ensemble strategy. These are marked as TODOs because they require information from the analysis code or internal documentation, but the schema defines *what* should be recorded.

**`file_format`** documents the practical reading instructions and known limitations (PyTables lock-in, HEPData size limit). This is metadata about the format itself, not the physics, but it is critical for a user from outside the pandas ecosystem.

## What I chose to leave out

**Trained model checkpoints and architecture files.** These are important for full reproducibility but are a separate artifact with different storage and versioning requirements. The schema records *what* was used (architecture, hyperparameters) but does not try to embed the models. A future extension could add a `models` section with paths or DOIs to stored checkpoints.

**Binning definitions.** The entire point of OmniFold is that the result is unbinned. Prescribing bins in the metadata would undermine this. The schema documents observables and their units, which is sufficient for a user to define their own binning.

**Detector-level information.** The weight files contain only particle-level quantities. Detector-level features, reconstruction details, and trigger information are part of the analysis chain but not part of the published result. Including them would conflate the measurement output with the measurement procedure.

**A formal JSON Schema or validation spec.** For this evaluation task, a human-readable YAML with clear field names and descriptions is more useful than a machine-enforceable schema. In a production implementation, the YAML structure shown here could be straightforwardly translated into a JSON Schema or Pydantic model for programmatic validation.

## How a new user would interact with this file

A physicist who downloads the weight files from Zenodo or HEPData would read the metadata YAML to answer three questions before writing any analysis code:

1. **Can I use this for my purpose?** The `fiducial_definition` tells them exactly which phase space the weights cover. If their theory prediction or comparison measurement uses different cuts, they know immediately whether the weights are applicable or whether they need to restrict their comparison to the overlapping region.

2. **Which file and which weight column do I need?** The `files` section tells them to start with `multifold.h5` for the nominal result. The `weights` section tells them to histogram their observable using `weights_nominal`, and then to compute uncertainty bands by repeating with the ensemble, bootstrap, and systematic weight columns. The `category` and `group` fields let them construct a grouped uncertainty breakdown without reverse-engineering the naming convention.

3. **How do I actually load the data?** The `file_format` section gives them the one-liner (`pd.read_hdf(filename, key='df')`) and warns them about the PyTables-specific layout if they are not using Python.

The TODO markers are intentional — they flag fields where the schema designer could not determine the correct value from the files alone, which is itself a demonstration of the gaps identified in Part 1.

## References

1. ATLAS Collaboration, "A simultaneous unbinned differential cross section measurement of twenty-four Z+jets kinematic observables with the ATLAS detector," Phys. Rev. Lett. 133, 261803 (2024), arXiv:2405.20041 [hep-ex]. This is the measurement paper that produced the weight files. The fiducial definition, MC sample descriptions, and uncertainty methodology are documented here. Cut values in the YAML were cross-checked against the data files and are consistent with this paper.

2. A. Andreassen, P. T. Komiske, E. M. Metodiev, B. Nachman, J. Thaler, "OmniFold: A Method to Simultaneously Unfold All Observables," Phys. Rev. Lett. 124, 182001 (2020), arXiv:1911.09107 [hep-ph]. The original OmniFold method paper. Provides the algorithmic context for understanding what the per-event weights represent (iterative reweighting to the maximum likelihood particle-level distribution).

3. ATLAS Collaboration, "ATLAS OmniFold 24-Dimensional Z+jets Open Data," Zenodo, doi:10.5281/zenodo.11507450 (2024). The data record hosting the HDF5 files. Documentation and example notebooks are linked from https://gitlab.cern.ch/atlas-physics/public/sm-z-jets-omnifold-2024.

4. B. Nachman et al., "A Practical Guide to Unbinned Unfolding," arXiv:2507.09582 [hep-ph]. Documents practical considerations for publishing unbinned unfolding results, including the 190 GeV unfolding boundary used in the ATLAS Z+jets measurement to mitigate migration effects at the 200 GeV fiducial threshold.
