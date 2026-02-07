"""Generate an HTML evaluation report with summary and charts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from .models import EvalSummary, RunResult


def _escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def write_html_report(
    summary: EvalSummary,
    output_path: str | Path,
    *,
    title: str = "Lookfor Chat Evaluation Report",
) -> None:
    """Write a single HTML file with summary stats, by-agent breakdown, and charts."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    total = summary.total
    escalated = summary.escalated
    errors = summary.errors
    success = total - escalated - errors
    if total:
        esc_pct = 100.0 * summary.escalation_rate
        err_pct = 100.0 * summary.error_rate
    else:
        esc_pct = err_pct = 0.0

    routing_acc = summary.routing_accuracy
    routing_str = f"{100.0 * routing_acc:.1f}%" if routing_acc is not None else "N/A (no ground truth)"
    intent_acc = summary.intent_accuracy
    intent_str = f"{100.0 * intent_acc:.1f}%" if intent_acc is not None else "N/A (no ground truth)"

    # By-agent data for chart
    agents = list(summary.by_agent.keys())
    counts = [summary.by_agent.get(a, {}).get("count", 0) for a in agents]
    escalated_by_agent = [summary.by_agent.get(a, {}).get("escalated", 0) for a in agents]

    # Confusion-style: expected vs actual (only when we have ground truth)
    routing_results = [(r.ticket.expected_agent, r.agent) for r in summary.results if r.ticket.expected_agent]
    confusion_pairs = []
    for exp, act in routing_results:
        exp = (exp or "").strip().lower()
        act = (act or "").strip().lower()
        if exp and act:
            confusion_pairs.append({"expected": exp, "actual": act})

    # Failures table: escalated or wrong route
    failures = [
        r
        for r in summary.results
        if r.is_escalated or r.error or (r.routing_correct is False)
    ][:200]  # cap for report size

    # Latency stats
    latencies = summary.latency_ms or []
    lat_p50 = _percentile(latencies, 50) if latencies else None
    lat_p95 = _percentile(latencies, 95) if latencies else None
    lat_avg = sum(latencies) / len(latencies) if latencies else None

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{_escape(title)}</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
  <style>
    :root {{ --bg: #0f1419; --card: #1a2332; --text: #e6edf3; --muted: #8b949e; --accent: #58a6ff; --success: #3fb950; --warning: #d29922; --danger: #f85149; }}
    * {{ box-sizing: border-box; }}
    body {{ font-family: 'Segoe UI', system-ui, sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 1.5rem; line-height: 1.5; }}
    h1 {{ font-size: 1.75rem; margin: 0 0 1rem; }}
    h2 {{ font-size: 1.15rem; margin: 1.5rem 0 0.5rem; color: var(--muted); }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 0.75rem; margin-bottom: 1rem; }}
    .card {{ background: var(--card); border-radius: 8px; padding: 1rem; border: 1px solid rgba(255,255,255,0.06); }}
    .card .value {{ font-size: 1.5rem; font-weight: 600; color: var(--accent); }}
    .card .label {{ font-size: 0.8rem; color: var(--muted); margin-top: 0.25rem; }}
    .card.success .value {{ color: var(--success); }}
    .card.warning .value {{ color: var(--warning); }}
    .card.danger .value {{ color: var(--danger); }}
    .charts {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 1rem; margin: 1rem 0; }}
    .chart-wrap {{ background: var(--card); border-radius: 8px; padding: 1rem; border: 1px solid rgba(255,255,255,0.06); height: 280px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; }}
    th, td {{ text-align: left; padding: 0.5rem 0.75rem; border-bottom: 1px solid rgba(255,255,255,0.06); }}
    th {{ color: var(--muted); font-weight: 500; }}
    .mono {{ font-family: ui-monospace, monospace; font-size: 0.85em; }}
    .snippet {{ max-width: 280px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
    .badge {{ display: inline-block; padding: 0.2em 0.5em; border-radius: 4px; font-size: 0.75rem; }}
    .badge.escalated {{ background: rgba(248,81,73,0.2); color: var(--danger); }}
    .badge.error {{ background: rgba(210,153,34,0.2); color: var(--warning); }}
    .badge.wrong {{ background: rgba(88,166,255,0.2); color: var(--accent); }}
  </style>
</head>
<body>
  <h1>{_escape(title)}</h1>
  <p style="color: var(--muted); margin: 0 0 1rem;">Total tickets: {total} · Success (auto-handled): {success} · Escalated: {escalated} · Errors: {errors}</p>

  <div class="grid">
    <div class="card">
      <div class="value">{total}</div>
      <div class="label">Total tickets</div>
    </div>
    <div class="card success">
      <div class="value">{success}</div>
      <div class="label">Auto-handled</div>
    </div>
    <div class="card warning">
      <div class="value">{escalated}</div>
      <div class="label">Escalated ({esc_pct:.1f}%)</div>
    </div>
    <div class="card danger">
      <div class="value">{errors}</div>
      <div class="label">Errors ({err_pct:.1f}%)</div>
    </div>
    <div class="card">
      <div class="value">{routing_str}</div>
      <div class="label">Routing accuracy</div>
    </div>
    <div class="card">
      <div class="value">{intent_str}</div>
      <div class="label">Intent accuracy</div>
    </div>
    <div class="card">
      <div class="value">{f"{lat_avg:.0f} ms" if lat_avg is not None else "—"}</div>
      <div class="label">Avg latency</div>
    </div>
    <div class="card">
      <div class="value">{f"p95 {lat_p95:.0f} ms" if lat_p95 is not None else "—"}</div>
      <div class="label">Latency p95</div>
    </div>
  </div>

  <h2>By agent</h2>
  <div class="chart-wrap">
    <canvas id="chartByAgent" height="220"></canvas>
  </div>

  <h2>Outcome distribution</h2>
  <div class="chart-wrap">
    <canvas id="chartOutcome" height="220"></canvas>
  </div>

  <h2>Agent breakdown (table)</h2>
  <table>
    <thead><tr><th>Agent</th><th>Count</th><th>Escalated</th><th>Esc %</th><th>Errors</th></tr></thead>
    <tbody>
"""
    for a in sorted(summary.by_agent.keys(), key=lambda x: -summary.by_agent[x].get("count", 0)):
        row = summary.by_agent[a]
        c = row.get("count", 0)
        e = row.get("escalated", 0)
        err = row.get("errors", 0)
        esc_p = (100.0 * e / c) if c else 0
        html += f"      <tr><td class=\"mono\">{_escape(a)}</td><td>{c}</td><td>{e}</td><td>{esc_p:.1f}%</td><td>{err}</td></tr>\n"
    html += """    </tbody>
  </table>
"""

    if failures:
        html += """
  <h2>Sample failures (escalated / wrong route / error)</h2>
  <table>
    <thead><tr><th>Conversation ID</th><th>Expected</th><th>Actual</th><th>Status</th><th>Message snippet</th></tr></thead>
    <tbody>
"""
        for r in failures[:100]:
            snippet = ""
            if r.ticket.message:
                snippet = (r.ticket.message[:80] + "…") if len(r.ticket.message) > 80 else r.ticket.message
            elif r.ticket.messages:
                for m in r.ticket.messages:
                    if isinstance(m, dict) and m.get("role") == "user":
                        c = m.get("content", "")
                        snippet = (c[:80] + "…") if len(c) > 80 else c
                        break
            status = []
            if r.is_escalated:
                status.append('<span class="badge escalated">escalated</span>')
            if r.error:
                status.append('<span class="badge error">error</span>')
            if r.routing_correct is False:
                status.append('<span class="badge wrong">wrong route</span>')
            status_str = " ".join(status) or "—"
            exp = (r.ticket.expected_agent or "—")
            act = (r.agent or "—")
            html += f"      <tr><td class=\"mono snippet\">{_escape(r.ticket.conversation_id)}</td><td class=\"mono\">{_escape(exp)}</td><td class=\"mono\">{_escape(act)}</td><td>{status_str}</td><td class=\"snippet\" title=\"{_escape(snippet)}\">{_escape(snippet)}</td></tr>\n"
        html += """    </tbody>
  </table>
"""

    # Chart.js config (dark theme)
    agents_js = json.dumps(agents)
    counts_js = json.dumps(counts)
    escalated_js = json.dumps(escalated_by_agent)
    html += f"""
  <script>
    Chart.defaults.color = '#8b949e';
    Chart.defaults.borderColor = 'rgba(255,255,255,0.06)';
    const agents = {agents_js};
    const counts = {counts_js};
    const escalatedByAgent = {escalated_js};
    new Chart(document.getElementById('chartByAgent'), {{
      type: 'bar',
      data: {{
        labels: agents,
        datasets: [
          {{ label: 'Total', data: counts, backgroundColor: 'rgba(88,166,255,0.5)' }},
          {{ label: 'Escalated', data: escalatedByAgent, backgroundColor: 'rgba(248,81,73,0.5)' }}
        ]
      }},
      options: {{
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: {{ legend: {{ position: 'top' }} }},
        scales: {{ x: {{ stacked: false, beginAtZero: true }} }}
      }}
    }});
    new Chart(document.getElementById('chartOutcome'), {{
      type: 'doughnut',
      data: {{
        labels: ['Auto-handled', 'Escalated', 'Errors'],
        datasets: [{{
          data: [{success}, {escalated}, {errors}],
          backgroundColor: ['#3fb950', '#d29922', '#f85149']
        }}]
      }},
      options: {{
        responsive: true,
        maintainAspectRatio: false,
        plugins: {{ legend: {{ position: 'right' }} }}
      }}
    }});
  </script>
</body>
</html>
"""
    path.write_text(html, encoding="utf-8")


def _percentile(sorted_list: List[float], p: float) -> float:
    if not sorted_list:
        return 0.0
    s = sorted(sorted_list)
    k = (len(s) - 1) * (p / 100.0)
    f = int(k)
    c = f + 1 if f + 1 < len(s) else f
    return s[f] + (k - f) * (s[c] - s[f]) if f != c else s[f]
