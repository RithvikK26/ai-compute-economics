"""Forms collect inputs; stable schemas and engine validate and calculate."""

import streamlit as st
from pydantic import ValidationError

from compute_economics.ui.presentation import B300_LIMITATION
from compute_economics.ui.presentation import label as human_label
from compute_economics.ui.service import PRESETS, candidate, compute_bytes, compute_preset


def error_message(exc):
    if isinstance(exc, ValidationError):
        return "\n".join(
            f"{' → '.join(human_label(str(v)) for v in e['loc']) or 'Input combination'}: {e['msg']}"
            for e in exc.errors()
        )
    return str(exc)


def publish(bundle):
    st.session_state["completed"] = bundle
    st.session_state["revision"] = st.session_state.get("revision", 0) + 1
    st.session_state.pop("input_error", None)


def submit(payload):
    try:
        with st.spinner("Evaluating fixed policies, frontiers and evidence…"):
            result = compute_bytes(payload)
        publish(result)
        return True
    except (ValueError, ArithmeticError, OSError) as exc:
        st.session_state["input_error"] = error_message(exc)
        return False


def number(field, label, base, updates, optional=False):
    value = getattr(base, field)
    key = f"input:{st.session_state.get('revision', 0)}:{field}"
    if optional:
        text = st.text_input(
            label,
            value="" if value is None else str(value),
            key=key,
            help="Blank means unavailable (or no cash constraint for upfront limit); zero is an explicit value.",
        )
        try:
            updates[field] = float(text) if text.strip() else None
        except ValueError:
            updates[field] = text
    else:
        updates[field] = st.number_input(
            label,
            value=value,
            key=key,
            step=1 if type(value) is int else 0.01,
            format=None if type(value) is int else "%0.4f",
        )


def sidebar(bundle):
    base = bundle.run
    updates = {}
    with st.sidebar:
        st.markdown("### Scenario workspace")
        preset = st.selectbox("Scenario preset", list(PRESETS), key="preset")
        if st.button("Load preset", key="load_preset", width="stretch"):
            with st.spinner("Loading and evaluating preset…"):
                publish(compute_preset(preset))
            st.rerun()
        st.caption("Loading a preset resets the controls. Results update after you submit changes.")
        with st.form("scenario_controls"):
            rev = st.session_state.get("revision", 0)
            config = st.selectbox(
                "Configuration",
                ["cw-b200-8", "cw-b300-8"],
                index=["cw-b200-8", "cw-b300-8"].index(base.configuration_id),
                format_func=lambda v: (
                    "CoreWeave " + ("B200" if "b200" in v else "B300") + " · 8 GPUs"
                ),
                key=f"configuration:{rev}",
            )
            model = st.selectbox(
                "Workload",
                ["gpt-oss-120b", "llama2-70b-99.9"],
                index=["gpt-oss-120b", "llama2-70b-99.9"].index(base.workload.model),
                key=f"workload:{rev}",
                help="MLPerf v6.1 Offline only. Changing hardware never rescales synthetic demand.",
            )
            number("horizon_months", "Horizon (calendar months)", base, updates)
            number("demand_multiplier", "Demand multiplier (×)", base, updates)
            number("max_od_nodes", "Maximum rental nodes", base, updates, optional=True)
            if (
                updates.get("max_od_nodes") is not None
                and isinstance(updates["max_od_nodes"], float)
                and updates["max_od_nodes"].is_integer()
            ):
                updates["max_od_nodes"] = int(updates["max_od_nodes"])
            number("max_fleet_nodes", "Fleet search bound (nodes)", base, updates)
            number(
                "upfront_cash_limit_usd",
                "Upfront cash limit (USD; blank = no constraint)",
                base,
                updates,
                optional=True,
            )
            with st.expander("Performance and service assumptions"):
                for f, label in [
                    ("transfer_fraction", "Baseline throughput transfer (0–1)"),
                    ("od_transfer_fraction", "Rental throughput transfer (0–1)"),
                    ("availability_fraction", "Baseline productive availability (0–1)"),
                    ("od_availability_fraction", "Rental productive availability (0–1)"),
                    ("delay_months", "Owned commissioning delay (months)"),
                    ("spare_nodes", "Owned spare nodes"),
                    ("billing_quantum_hours", "Rental billing quantum (hours)"),
                    ("startup_hours", "Paid startup (hours/node/block)"),
                ]:
                    number(f, label, base, updates)
            with st.expander("B300 price assumption"):
                st.caption(
                    B300_LIMITATION + " Enter a price and rationale to test an explicit assumption."
                )
                price = st.text_input(
                    "Assumed B300 price (USD/node-hour)",
                    value=str(base.od_price_usd)
                    if base.configuration_id == "cw-b300-8" and base.od_price_usd is not None
                    else "",
                    key=f"b300price:{rev}",
                )
                reason = st.text_input("Price assumption rationale", key=f"b300reason:{rev}")
            apply = st.form_submit_button("Run scenario", type="primary", width="stretch")
        if apply:
            try:
                if config == "cw-b300-8":
                    updates["od_price_usd"] = float(price) if price.strip() else None
                elif base.configuration_id != "cw-b200-8":
                    updates["od_price_usd"] = next(
                        e.value for e in base.evidence if e.input_id == "od_price_usd"
                    )
                if submit(candidate(base, updates, config, model, reason)):
                    st.rerun()
            except (ValueError, ArithmeticError) as exc:
                st.session_state["input_error"] = error_message(exc)
        with st.expander("Import a saved scenario"):
            uploaded = st.file_uploader(
                "Versioned JSON · maximum 1 MB",
                type=["json"],
                key="scenario_upload",
                max_upload_size=1,
            )
            if st.button("Import and run", key="import_run"):
                if uploaded is None:
                    st.session_state["input_error"] = "Select a scenario JSON file first."
                elif submit(uploaded.getvalue()):
                    st.rerun()
            st.caption(
                "Imports are validated by the existing schema, provenance and hash checks. Files are processed privately and temporary files are removed."
            )
        st.divider()
        st.caption(
            "Batch inference · whole nodes · USD\n\nHistorical public snapshot + explicit assumptions. No live inventory or production capacity guarantee."
        )


def economics_form(bundle):
    base = bundle.run
    updates = {}
    with st.expander("Edit itemized economic assumptions"):
        st.caption(
            "Inputs are assumptions unless linked to a published observation. Submit to update all four views; editing alone does not change results."
        )
        with st.form("economics_controls"):
            cols = st.columns(3)
            groups = [
                (
                    "Prices and contract",
                    [
                        ("od_price_usd", "Rental (USD/node-hour)", True),
                        ("future_price_multiplier", "Rental price from month 13 (×)", False),
                        ("commit_price_usd", "Commitment (USD/node-hour)", True),
                        ("commit_term_months", "Contract term (months; must match horizon)", False),
                        ("commit_setup_usd", "Setup (USD/committed node)", False),
                        ("prepaid_fraction", "Prepaid fraction (0–1)", False),
                        ("commit_fee_monthly_usd", "Commitment fees (USD/month)", False),
                    ],
                ),
                (
                    "Ownership and cash",
                    [
                        ("node_acquisition_usd", "Complete owned node (USD)", True),
                        ("install_usd", "Installation (USD)", False),
                        ("network_usd", "Incremental network (USD)", False),
                        ("storage_usd", "Incremental storage (USD)", False),
                        ("fixed_operations_annual_usd", "Fixed operations (USD/year)", False),
                        (
                            "per_node_operations_annual_usd",
                            "Per-node operations (USD/node/year)",
                            False,
                        ),
                        ("usable_life_months", "Usable life (months)", False),
                        ("residual_usd", "Gross terminal proceeds (USD)", False),
                        ("exit_usd", "Exit cost (USD)", False),
                        ("discount_rate_fraction", "Annual discount rate (fraction)", False),
                    ],
                ),
                (
                    "Power and hosting",
                    [
                        ("idle_kw", "Whole-node idle power (kW)", False),
                        ("load_kw", "Whole-node load power (kW)", False),
                        ("auxiliary_kw", "Shared auxiliary IT power (kW)", False),
                        ("pue", "Facility PUE (ratio)", False),
                        ("electricity_usd_kwh", "Electricity (USD/kWh)", False),
                        ("all_in_colo_monthly_usd", "All-in colocation (USD/month)", False),
                        ("contracted_kw", "Contracted power (kW)", False),
                        ("demand_charge_usd_kw_month", "Demand charge (USD/kW/month)", False),
                        ("space_monthly_usd", "Space (USD/month)", False),
                        ("other_site_monthly_usd", "Other site fees (USD/month)", False),
                        ("precommission_monthly_usd", "Precommissioning (USD/month)", False),
                    ],
                ),
            ]
            for col, (title, fields) in zip(cols, groups):
                with col:
                    st.markdown("**" + title + "**")
                    for field, label, optional in fields:
                        number(field, label, base, updates, optional)
            updates["hosting_mode"] = st.selectbox(
                "Hosting mode",
                ["metered_energy", "all_in_colo"],
                index=["metered_energy", "all_in_colo"].index(base.hosting_mode),
                format_func=human_label,
                key=f"hosting:{st.session_state.get('revision', 0)}",
            )
            st.caption(
                "All-in colocation requires separate electricity, demand and space charges to be zero. Contract term must equal horizon. The engine excludes incompatible policies and rejects double charging."
            )
            reason = st.text_input(
                "B300 price rationale (when applicable)", key="economic_b300_reason"
            )
            apply = st.form_submit_button("Apply economic assumptions", type="primary")
        if apply:
            try:
                if submit(
                    candidate(base, updates, base.configuration_id, base.workload.model, reason)
                ):
                    st.rerun()
            except (ValueError, ArithmeticError) as exc:
                st.session_state["input_error"] = error_message(exc)
    with st.expander("Advanced saved-input editor"):
        st.caption(
            "For monthly/block demand, ancillary costs, included capital components, start date and other validated settings. Preserve original evidence. This is the existing RunInput schema, not executable code."
        )
        rev = st.session_state.get("revision", 0)
        with st.form("advanced_input_form"):
            text = st.text_area(
                "Complete scenario input JSON",
                value=base.model_dump_json(indent=2),
                height=300,
                key=f"advanced:{rev}",
            )
            apply_json = st.form_submit_button("Validate and run JSON")
        if apply_json and submit(text.encode()):
            st.rerun()
