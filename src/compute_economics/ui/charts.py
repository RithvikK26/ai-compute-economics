"""Charts reshape emitted values only; calculations remain in the engine."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

COLORS = {"own": "#087F72", "commit": "#D59635", "on_demand": "#566BC4", "unavailable": "#D7DDE3"}


def policy_label(value):
    if not value:
        return "Unavailable"
    family, nodes = value.split(":")
    return (
        "All on-demand"
        if family == "on_demand"
        else f"{'Own' if family == 'own' else 'Commit'} {nodes} nodes + overflow"
    )


def finish(fig, title, x, y, height=400):
    fig.update_layout(
        title=dict(text=title, font_size=17),
        xaxis_title=x,
        yaxis_title=y,
        height=height,
        margin=dict(l=10, r=15, t=50, b=25),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Arial", color="#162A3A", size=12),
        legend=dict(orientation="h", y=-0.2),
        hovermode="closest",
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#E4E9EF", zerolinecolor="#ABB8C4")
    return fig


def surface_chart(analysis):
    rows = analysis["surface"]
    if not rows:
        return None
    df = pd.DataFrame(rows)
    xs = sorted(df.demand_multiplier.unique())
    ys = sorted(df.acquisition_multiplier.unique())
    codes = {"on_demand": 0, "commit": 1, "own": 2, "unavailable": 3}
    cells = {(r["demand_multiplier"], r["acquisition_multiplier"]): r for r in rows}
    z = []
    hover = []
    for y in ys:
        zr = []
        hr = []
        for x in xs:
            r = cells[x, y]
            family = r["winner"].split(":")[0] if r["winner"] else "unavailable"
            zr.append(codes[family])
            hr.append(
                [
                    policy_label(r["winner"]),
                    r["lowest_pv_usd"],
                    r["node_acquisition_usd"],
                    ", ".join(policy_label(p) for p in r["tie_set"]),
                ]
            )
        z.append(zr)
        hover.append(hr)
    palette = [COLORS[k] for k in codes]
    scale = []
    for i, color in enumerate(palette):
        scale.extend([(i / 4, color), ((i + 1) / 4, color)])
    fig = go.Figure(
        go.Heatmap(
            x=xs,
            y=ys,
            z=z,
            zmin=-0.5,
            zmax=3.5,
            colorscale=scale,
            customdata=hover,
            colorbar=dict(
                tickvals=[0, 1, 2, 3],
                ticktext=["On-demand", "Commit", "Own", "Unavailable"],
                thickness=12,
                len=0.7,
            ),
            hovertemplate="Demand: %{x:.2f}×<br>Acquisition: %{y:.2f}× (%{customdata[2]:$,.0f}/node)<br>%{customdata[0]}<br>Lowest PV: %{customdata[1]:$,.0f}<br>Tie set: %{customdata[3]}<extra></extra>",
        )
    )
    # Mark borders between adjacent tested cells with different winning fleets.
    # These are grid-cell boundaries, not interpolated economic thresholds.
    xe = (
        [xs[0] - (xs[1] - xs[0]) / 2]
        + [(a + b) / 2 for a, b in zip(xs, xs[1:])]
        + [xs[-1] + (xs[-1] - xs[-2]) / 2]
    )
    ye = (
        [ys[0] - (ys[1] - ys[0]) / 2]
        + [(a + b) / 2 for a, b in zip(ys, ys[1:])]
        + [ys[-1] + (ys[-1] - ys[-2]) / 2]
    )
    bx, by = [], []
    for j, y in enumerate(ys):
        for i, x in enumerate(xs):
            winner = cells[x, y]["winner"]
            if i + 1 < len(xs) and winner != cells[xs[i + 1], y]["winner"]:
                bx.extend([xe[i + 1], xe[i + 1], None])
                by.extend([ye[j], ye[j + 1], None])
            if j + 1 < len(ys) and winner != cells[x, ys[j + 1]]["winner"]:
                bx.extend([xe[i], xe[i + 1], None])
                by.extend([ye[j + 1], ye[j + 1], None])
    fig.add_trace(
        go.Scatter(
            x=bx,
            y=by,
            mode="lines",
            line=dict(color="white", width=1.5),
            name="Tested fleet boundaries",
            hoverinfo="skip",
            showlegend=False,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[1.0],
            y=[1.0],
            mode="markers",
            name="Current assumptions",
            marker=dict(
                size=13, color="white", line=dict(color="#162A3A", width=2), symbol="diamond"
            ),
            hovertemplate="Current assumptions: 1× demand / 1× acquisition<extra></extra>",
        )
    )
    return finish(
        fig,
        "Sourcing decision surface",
        "Demand multiplier · relative to current scenario",
        "Acquisition-cost multiplier",
        410,
    )


def frontier_chart(analysis, axis):
    points = analysis["frontier"][axis]["points"]
    if not points:
        return None
    fig = go.Figure()
    for family in ["on_demand", "commit", "own"]:
        # Minimum over emitted feasible policy costs is presentation of the family envelope.
        values = []
        for p in points:
            costs = [
                v for k, v in p["costs"].items() if k.startswith(family + ":") and v is not None
            ]
            values.append(min(costs) if costs else None)
        fig.add_trace(
            go.Scatter(
                x=[p["value"] for p in points],
                y=values,
                name={
                    "own": "Owned baseline + overflow",
                    "commit": "Committed baseline + overflow",
                    "on_demand": "All on-demand",
                }[family],
                mode="lines+markers",
                line=dict(color=COLORS[family], width=2, shape="linear"),
                marker_size=4,
                connectgaps=False,
                hovertemplate="%{x:.3g}<br>PV cost: %{y:$,.0f}<extra>%{fullData.name}</extra>",
            )
        )
    xlabel = {
        "demand": "Demand multiplier",
        "acquisition_cost_multiplier": "Acquisition-cost multiplier",
        "commitment_price_usd_node_hour": "Commitment price · USD/node-hour",
    }[axis]
    return finish(fig, "Feasible cost at tested points", xlabel, "Present-value cost · USD", 350)


def cash_chart(frame):
    fig = go.Figure(
        go.Bar(
            x=frame["period"],
            y=frame["cash_usd"],
            marker_color=["#AA5151" if v < 0 else "#087F72" for v in frame["cash_usd"]],
            hovertemplate="Month %{x}<br>%{y:$,.0f}<extra></extra>",
        )
    )
    return finish(fig, "Monthly cash requirements", "Month · 0 is upfront", "Cash flow · USD")


def capacity_chart(frame):
    monthly = frame.groupby("period")[
        ["demand_tokens", "baseline_tokens", "overflow_tokens", "unmet_tokens"]
    ].sum()
    fig = go.Figure()
    for field, label, color in [
        ("baseline_tokens", "Baseline served", "#087F72"),
        ("overflow_tokens", "Overflow served", "#8799D0"),
    ]:
        fig.add_trace(go.Bar(x=monthly.index, y=monthly[field], name=label, marker_color=color))
    fig.add_trace(
        go.Scatter(
            x=monthly.index,
            y=monthly["demand_tokens"],
            name="Demand",
            line=dict(color="#162A3A", width=2),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=monthly.index,
            y=monthly["unmet_tokens"],
            name="Unmet demand",
            line=dict(color="#C04444", width=3, dash="dot"),
        )
    )
    fig.update_layout(barmode="stack")
    return finish(fig, "Delivered work and visible service gaps", "Month", "Output tokens")


def cost_chart(policies):
    rows = [
        dict(policy=policy_label(p["policy_id"]), category=k.replace("_", " ").title(), pv=v)
        for p in policies
        for k, v in p["category_pv_usd"].items()
    ]
    if not rows:
        return None
    fig = px.bar(pd.DataFrame(rows), x="policy", y="pv", color="category", barmode="relative")
    return finish(fig, "Present-value cost composition", "Policy", "Present-value cost · USD")
