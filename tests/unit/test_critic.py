from app.critique.service import ScientificCritic
from app.statistics.service import StatisticalSummary


def test_critic_rejects_interval_that_includes_no_improvement() -> None:
    report = ScientificCritic().evaluate(
        StatisticalSummary(
            effect_size=0.1,
            confidence_interval=[-0.02, 0.04],
            p_value=0.12,
            sample_count=12,
            variance=0.01,
            mean_difference=0.01,
            statistical_power=None,
        ),
        "EXPLORATORY",
    )

    assert report.outcome == "REJECT"
    assert any(finding.code == "INTERVAL_INCLUDES_NO_IMPROVEMENT" for finding in report.findings)

