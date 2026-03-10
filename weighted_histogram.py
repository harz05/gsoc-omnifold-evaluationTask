"""
weighted_histogram.py

Part-3 GSoC'26 Evaluation task. Self-contained module for computing and plotting weighted histograms of OmniFold observables.

Usage:
    import pandas as pd
    df = pd.read_hdf("multifold.h5", key="df")
    result = weighted_histogram(df["pT_ll"].values, df["weights_nominal"].values)
"""

import numpy as np
import matplotlib.pyplot as plt


def weighted_histogram(
    values,
    weights,
    bins=50,
    range=None,
    xlabel=None,
    ylabel=None,
    title=None,
    plot=True,
    ax=None,
):
    """
    Compute a weighted histogram and optionally plot it.

    The per-bin uncertainty is sqrt(sum(w_i^2)) for all events i
    falling in that bin. This is the standard prescription in HEP
    for weighted event samples: it reduces to sqrt(N) when all
    weights are unity, and correctly propagates the variance of
    non-uniform or negative weights.

    Parameters
    ----------
    values : array_like
        Observable values, one per event.
    weights : array_like
        Per-event weights. Can be negative (common in MC systematics).
    bins : int or array_like
        Number of equal-width bins, or explicit bin edges.
    range : tuple of (float, float) or None
        Range to histogram over. Ignored if bins is an array, if none, numpy infers from data.
    xlabel : str or None
        X-axis label for the plot.
    ylabel : str or None
        Y-axis label. Defaults to "Events" if weights look like counts, or includes unit info if they look like cross sections.
    title : str or None
        Plot title.
    plot : bool
        Whether to produce a matplotlib figure.
    ax : matplotlib Axes or None
        If provided, plot on this axes instead of creating a new figure.

    Returns
    -------
    dict with keys:
        bin_edges   : (n_bins + 1,) array of bin boundaries
        bin_centers : (n_bins,) array of bin midpoints
        bin_widths  : (n_bins,) array of bin widths
        contents    : (n_bins,) weighted bin counts (= sum of weights per bin)
        errors      : (n_bins,) per-bin uncertainty, sqrt(sum(w_i^2))
        integral    : scalar, total sum of weights across all bins
    """
    values = np.asarray(values, dtype=np.float64)
    weights = np.asarray(weights, dtype=np.float64)

    if values.shape != weights.shape:
        raise ValueError(
            f"values and weights must have the same shape, "
            f"got {values.shape} vs {weights.shape}"
        )
    if values.ndim != 1:
        raise ValueError(f"Expected 1D arrays, got ndim={values.ndim}")

    # Handle the degenerate case: empty input.
    # Return a valid but empty histogram structure so downstream code
    # doesn't crash on len-0 data (e.g. when a phase space cut removes
    # all events for a particular systematic).
    if len(values) == 0:
        if isinstance(bins, (int, np.integer)):
            n_bins = int(bins)
            lo = 0.0 if range is None else range[0]
            hi = 1.0 if range is None else range[1]
            bin_edges = np.linspace(lo, hi, n_bins + 1)
        else:
            bin_edges = np.asarray(bins, dtype=np.float64)
        n_bins = len(bin_edges) - 1
        return {
            "bin_edges": bin_edges,
            "bin_centers": 0.5 * (bin_edges[:-1] + bin_edges[1:]),
            "bin_widths": np.diff(bin_edges),
            "contents": np.zeros(n_bins),
            "errors": np.zeros(n_bins),
            "integral": 0.0,
        }

    # Weighted bin counts: sum of w_i per bin.
    contents, bin_edges = np.histogram(values, bins=bins, range=range, weights=weights)

    # Per-bin uncertainty: sqrt(sum(w_i^2)) per bin.
    # This is the variance of a weighted sum when events are independent.
    errors_sq, _ = np.histogram(values, bins=bin_edges, weights=weights**2)
    errors = np.sqrt(errors_sq)

    bin_centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])
    bin_widths = np.diff(bin_edges)
    integral = float(np.sum(contents))

    result = {
        "bin_edges": bin_edges,
        "bin_centers": bin_centers,
        "bin_widths": bin_widths,
        "contents": contents,
        "errors": errors,
        "integral": integral,
    }

    if plot:
        _plot_histogram(result, xlabel=xlabel, ylabel=ylabel, title=title, ax=ax)

    return result


def _plot_histogram(result, xlabel=None, ylabel=None, title=None, ax=None):
    """
    Plot a weighted histogram as a step line with error bars.
    Uses the standard HEP convention: bin contents shown as a
    horizontal step function, uncertainties as vertical error bars
    at bin centers.
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 5))
    else:
        fig = ax.get_figure()

    centers = result["bin_centers"]
    contents = result["contents"]
    errors = result["errors"]
    edges = result["bin_edges"]

    # Step histogram for the central values.
    ax.step(edges, np.append(contents, contents[-1]),
            where="post", color="black", linewidth=1.2)

    # Error bars at bin centers.
    ax.errorbar(centers, contents, yerr=errors,
                fmt="none", ecolor="black", elinewidth=0.8, capsize=2)

    ax.set_xlabel(xlabel or "Observable")
    ax.set_ylabel(ylabel or "Weighted counts")
    if title:
        ax.set_title(title)

    # Keep zero visible for cross-section plots.
    ymin = min(0, ax.get_ylim()[0])
    ax.set_ylim(bottom=ymin)
    ax.margins(x=0)

    fig.tight_layout()
    return fig, ax


# ---------------------------------------------------------------------------
# Tests---->>
# ---------------------------------------------------------------------------
# Run with: pytest weighted_histogram.py -v
# Or standalone: python3 weighted_histogram.py

def test_uniform_weights_match_unweighted():
    """
    If every event has weight 1, the weighted histogram must be
    identical to a plain count histogram. 
    This is the most basic sanity check: the weighting machinery should be a no-op when
    weights are trivial.
    """
    rng = np.random.default_rng(42)
    values = rng.normal(0, 1, size=10_000)
    ones = np.ones_like(values)
    bins = np.linspace(-4, 4, 41)

    result = weighted_histogram(values, ones, bins=bins, plot=False)
    expected, _ = np.histogram(values, bins=bins)

    np.testing.assert_array_equal(result["contents"], expected)
    # Uncertainty should be sqrt(N) per bin for unit weights.
    np.testing.assert_allclose(result["errors"], np.sqrt(expected), atol=1e-10)


def test_integral_equals_weight_sum():
    
    #The histogram integral (sum of bin contents) must equal the sum of all input weights, as long as the range covers all data.
    #This is a normalization consistency check: losing or double-counting events in the binning would show up here.
    
    rng = np.random.default_rng(7)
    values = rng.uniform(0, 10, size=5000)
    weights = rng.exponential(0.5, size=5000)

    result = weighted_histogram(values, weights, bins=30, range=(0, 10), plot=False)
    np.testing.assert_allclose(result["integral"], np.sum(weights), rtol=1e-10)


def test_negative_weights():
    """
    MC systematic variations often produce negative per-event weights.
    The histogram must handle them correctly: bin contents can be
    negative, and the uncertainty calculation (sqrt of sum of w^2)
    must still be non-negative.
    """
    values = np.array([1.0, 2.0, 3.0, 3.5])
    weights = np.array([1.0, -2.0, 1.5, -0.5])
    bins = np.array([0.0, 2.5, 4.0])

    result = weighted_histogram(values, weights, bins=bins, plot=False)

    # Bin 0 [0, 2.5): events at 1.0 (w=1) and 2.0 (w=-2) -> sum = -1.0
    assert result["contents"][0] == -1.0
    # Bin 1 [2.5, 4.0): events at 3.0 (w=1.5) and 3.5 (w=-0.5) -> sum = 1.0
    assert result["contents"][1] == 1.0

    # Errors must always be non-negative regardless of weight signs.
    assert np.all(result["errors"] >= 0)
    # Bin 0 error: sqrt(1^2 + (-2)^2) = sqrt(5)
    np.testing.assert_allclose(result["errors"][0], np.sqrt(5), atol=1e-10)


def test_empty_input():
    """
    After aggressive phase-space cuts, it's possible for zero events
    to survive. The function should return a valid histogram with all
    zeros rather than crashing, so that downstream aggregation code
    (e.g. combining systematic variations) can proceed.
    """
    result = weighted_histogram(
        np.array([]), np.array([]), bins=10, range=(0, 1), plot=False
    )
    assert result["contents"].shape == (10,)
    assert np.all(result["contents"] == 0)
    assert result["integral"] == 0.0


def test_single_event_single_bin():
    
    #Minimal non-trivial case. One event, one bin. 
    #Useful for checkin that indexing logic doesn't have off-by-one issues.
    
    result = weighted_histogram(
        np.array([5.0]), np.array([3.14]), bins=np.array([0.0, 10.0]), plot=False
    )
    assert result["contents"][0] == 3.14
    np.testing.assert_allclose(result["errors"][0], 3.14)


def test_shape_mismatch_raises():
    
    #Mismatched values/weights arrays are a common caller error.
    #Fail early with a clear message rather than silently producing garbage.
    
    try:
        weighted_histogram(np.array([1, 2, 3]), np.array([1, 2]), plot=False)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


def test_events_outside_range_excluded():
    """
    Events outside the specified range must not contribute to any bin.
    This matters for fiducial cross-section calculations i.e. if a user
    requests a restricted range, overflow events shouldn't inflate
    the integral.
    """
    values = np.array([1.0, 5.0, 9.0])
    weights = np.array([10.0, 20.0, 30.0])

    # Only the event at 5.0 falls inside [3, 7).
    result = weighted_histogram(values, weights, bins=1, range=(3, 7), plot=False)
    assert result["contents"][0] == 20.0
    assert result["integral"] == 20.0


def test_bin_edges_returned_correctly():
    """
    Explicit bin edges should pass through unchanged. Users doing
    variable-width binning (common in HEP for log-scale observables)
    rely on this.
    """
    edges = np.array([0, 1, 5, 10, 100])
    values = np.array([0.5, 3.0, 7.0, 50.0])
    weights = np.ones(4)

    result = weighted_histogram(values, weights, bins=edges, plot=False)
    np.testing.assert_array_equal(result["bin_edges"], edges)
    assert len(result["contents"]) == 4  # 4 bins from 5 edges


if __name__ == "__main__":
    # Run all tests when executed directly.
    import sys

    tests = [
        test_uniform_weights_match_unweighted,
        test_integral_equals_weight_sum,
        test_negative_weights,
        test_empty_input,
        test_single_event_single_bin,
        test_shape_mismatch_raises,
        test_events_outside_range_excluded,
        test_bin_edges_returned_correctly,
    ]

    failed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
        except Exception as e:
            print(f"  FAIL  {t.__name__}: {e}")
            failed += 1

    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    if failed:
        sys.exit(1)

    # Demo plot using synthetic data if no HDF5 file is available.
    print("\nGenerating demo plot...")
    rng = np.random.default_rng(0)
    demo_values = rng.exponential(scale=300, size=50_000) + 200
    demo_weights = rng.exponential(scale=0.004, size=50_000)

    result = weighted_histogram(
        demo_values,
        demo_weights,
        bins=np.linspace(200, 2000, 51),
        xlabel=r"$p_T^{\ell\ell}$ [GeV]",
        ylabel=r"$d\sigma / dp_T^{\ell\ell}$ [fb / bin]",
        title="Demo: weighted histogram",
        plot=True,
    )
    plt.savefig("demo_histogram.png", dpi=150)
    print(f"Saved demo_histogram.png (integral = {result['integral']:.2f})")
