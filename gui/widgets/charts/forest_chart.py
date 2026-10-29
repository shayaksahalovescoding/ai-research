"""Bootstrap Confidence Interval & Effect Size Forest Plot Canvas."""

from __future__ import annotations

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PySide6.QtWidgets import QVBoxLayout, QWidget


class ForestCIChartCanvas(QWidget):
    """Interactive dark-themed Matplotlib canvas for Bootstrap 95% CI Forest Plot."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.figure = Figure(figsize=(5, 3.2), dpi=100, facecolor="#080d16")
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setStyleSheet("background: transparent;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)

        self.draw_empty_state()

    def draw_empty_state(self) -> None:
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.set_facecolor("#080d16")

        ax.text(
            0.5,
            0.5,
            "Bootstrap 95% CI Forest Plot\n(Run research workflow to compute bootstrap confidence intervals)",
            color="#64748b",
            ha="center",
            va="center",
            fontsize=11,
            fontweight="bold",
            transform=ax.transAxes,
        )
        ax.axis("off")
        self.canvas.draw()

    def update_data(
        self,
        ci: list[float] | None,
        delta: float | None,
        effect_size: float | None = None,
    ) -> None:
        if delta is None or not ci or len(ci) != 2:
            self.draw_empty_state()
            return

        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.set_facecolor("#080d16")

        y_labels = ["Mean Difference (Δ)"]
        y_pos = [0]
        point_estimates = [delta]
        ci_lowers = [ci[0]]
        ci_uppers = [ci[1]]
        colors = ["#34d399" if ci[0] > 0 else "#38bdf8"]

        if effect_size is not None:
            y_labels.insert(0, "Standardized Effect (d / 10)")
            y_pos = [0, 1]
            scaled_effect = effect_size / 10.0
            point_estimates.insert(0, scaled_effect)
            # Approximate CI for effect size
            margin = (ci[1] - ci[0]) / 2.0
            ci_lowers.insert(0, max(0.0, scaled_effect - margin))
            ci_uppers.insert(0, scaled_effect + margin)
            colors.insert(0, "#a78bfa")

        # Zero reference line (Null effect threshold)
        ax.axvline(0, color="#fbbf24", linestyle="--", linewidth=1.5, alpha=0.8, label="Null Threshold ($H_0 = 0$)")

        # Plot Error Bars and Diamond Markers
        for y, pt, low, up, col in zip(y_pos, point_estimates, ci_lowers, ci_uppers, colors, strict=False):
            # Horizontal CI line
            ax.plot([low, up], [y, y], color=col, linewidth=2.8, solid_capstyle="round")
            # End cap whiskers
            ax.plot([low, low], [y - 0.1, y + 0.1], color=col, linewidth=2.0)
            ax.plot([up, up], [y - 0.1, y + 0.1], color=col, linewidth=2.0)
            # Center diamond marker
            ax.scatter([pt], [y], color="#ffffff", edgecolor=col, s=120, marker="D", linewidth=1.8, zorder=5)

            # Label value annotation
            ax.text(
                up + 0.015,
                y,
                f"{pt:+.4f} [{low:.4f}, {up:.4f}]",
                color=col,
                va="center",
                fontsize=9,
                fontweight="bold",
            )

        # Formatting
        ax.set_yticks(y_pos)
        ax.set_yticklabels(y_labels, color="#cbd5e1", fontsize=9, fontweight="bold")
        ax.set_ylim(-0.6, len(y_pos) - 0.4)

        # X bounds
        min_x = min(min(ci_lowers) - 0.05, -0.05)
        max_x = max(max(ci_uppers) + 0.15, 0.20)
        ax.set_xlim(min_x, max_x)

        ax.set_title("Bootstrap 95% Confidence Interval (B=1000 Resamples)", color="#f8fafc", fontsize=11, fontweight="bold", pad=10)
        ax.set_xlabel("Effect Estimate & Confidence Interval", color="#94a3b8", fontsize=9, fontweight="bold")

        ax.tick_params(colors="#64748b", labelsize=8)
        for spine in ax.spines.values():
            spine.set_color("#172033")

        ax.grid(True, linestyle=":", alpha=0.25, color="#334155")
        ax.legend(facecolor="#0e1626", edgecolor="#1c2a42", labelcolor="#cbd5e1", fontsize=8, loc="upper left")

        self.figure.tight_layout()
        self.canvas.draw()
