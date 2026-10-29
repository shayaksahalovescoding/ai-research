"""Citation & Cryptographic Lineage DAG Network Graph Canvas."""

from __future__ import annotations

from typing import Any
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import networkx as nx
from PySide6.QtWidgets import QVBoxLayout, QWidget

NODE_COLORS = {
    "Source": "#10b981",
    "Paper": "#059669",
    "Evidence": "#0284c7",
    "Hypothesis": "#6366f1",
    "Experiment": "#8b5cf6",
    "ExperimentRun": "#a855f7",
    "Metric": "#f59e0b",
    "Result": "#d97706",
    "Critique": "#f43f5e",
    "Artifact": "#64748b",
}


class ProvenanceDAGCanvas(QWidget):
    """Interactive dark-themed NetworkX & Matplotlib canvas for Lineage DAG Graph."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.figure = Figure(figsize=(6, 3.8), dpi=100, facecolor="#080d16")
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
            "Cryptographic Lineage DAG Network\n(Run research workflow to generate verifiable provenance graph)",
            color="#64748b",
            ha="center",
            va="center",
            fontsize=11,
            fontweight="bold",
            transform=ax.transAxes,
        )
        ax.axis("off")
        self.canvas.draw()

    def update_data(self, knowledge_payload: dict[str, Any] | None) -> None:
        if not knowledge_payload or not knowledge_payload.get("nodes"):
            self.draw_empty_state()
            return

        raw_nodes = knowledge_payload.get("nodes", [])
        raw_edges = knowledge_payload.get("edges", [])

        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.set_facecolor("#080d16")

        G = nx.DiGraph()

        # Add Nodes with Type attributes
        layer_order = ["Source", "Paper", "Evidence", "Hypothesis", "Experiment", "ExperimentRun", "Metric", "Result", "Critique", "Artifact"]
        for node in raw_nodes:
            nid = str(node.get("id", ""))
            ntype = str(node.get("type", "Entity"))
            short_id = nid[:6] if len(nid) > 6 else nid
            label = f"{ntype}\n({short_id})"
            layer = layer_order.index(ntype) if ntype in layer_order else 5
            G.add_node(nid, label=label, ntype=ntype, layer=layer)

        # Add Edges
        for edge in raw_edges:
            src = str(edge.get("source", ""))
            tgt = str(edge.get("target", ""))
            if src in G and tgt in G:
                G.add_edge(src, tgt, rel=edge.get("type", "LINK"))

        if len(G.nodes) == 0:
            self.draw_empty_state()
            return

        # Compute Layout positions
        try:
            pos = nx.spring_layout(G, k=1.8, seed=42, iterations=60)
        except Exception:
            pos = nx.shell_layout(G)

        # Node colors
        node_colors = [NODE_COLORS.get(G.nodes[n].get("ntype", "Entity"), "#3b82f6") for n in G.nodes]

        # Draw Edges with curved arrows
        nx.draw_networkx_edges(
            G,
            pos,
            ax=ax,
            edge_color="#334155",
            width=1.8,
            arrowsize=14,
            arrowstyle="-|>",
            connectionstyle="arc3,rad=0.1",
            alpha=0.8,
        )

        # Draw Nodes with glowing halo effect
        nx.draw_networkx_nodes(
            G,
            pos,
            ax=ax,
            node_color=node_colors,
            node_size=800,
            alpha=0.9,
            edgecolors="#ffffff",
            linewidths=1.2,
        )

        # Draw Node Labels
        labels = {n: G.nodes[n].get("label", n[:6]) for n in G.nodes}
        nx.draw_networkx_labels(
            G,
            pos,
            labels=labels,
            ax=ax,
            font_size=7,
            font_color="#ffffff",
            font_family="sans-serif",
            font_weight="bold",
        )

        ax.set_title("Cryptographic Lineage DAG: Verifiable Entity Provenance Chain", color="#f8fafc", fontsize=11, fontweight="bold", pad=12)
        ax.axis("off")

        self.figure.tight_layout()
        self.canvas.draw()
