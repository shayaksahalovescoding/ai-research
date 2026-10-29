from app.statistics.service import StatisticsService


def test_paired_statistics_reports_actual_positive_effect() -> None:
    summary = StatisticsService().analyze_paired(
        [0.50, 0.55, 0.52, 0.54, 0.51, 0.53, 0.50, 0.54, 0.52, 0.53],
        [0.62, 0.67, 0.63, 0.66, 0.64, 0.65, 0.62, 0.66, 0.64, 0.65],
        bootstrap_samples=300,
        permutation_samples=1_000,
    )

    assert summary.sample_count == 10
    assert summary.mean_difference > 0
    assert summary.confidence_interval[0] > 0
    assert summary.p_value < 0.05

