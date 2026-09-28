"""Strict, finite, versioned contracts. Unknowns are not zeros."""

from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Nonnegative = Annotated[float, Field(ge=0)]
Positive = Annotated[float, Field(gt=0)]
Fraction = Annotated[float, Field(gt=0, le=1)]
Share = Annotated[float, Field(ge=0, le=1)]
Nodes = Annotated[int, Field(ge=0, le=128)]
Unit = Literal[
    "USD",
    "USD/node-hour",
    "USD/GPU-hour",
    "USD/month",
    "USD/year",
    "USD/kWh",
    "USD/kW-month",
    "USD/million-output-tokens",
    "USD/GB",
    "USD/GB-month",
    "tokens/s/node",
    "output_tokens",
    "hours",
    "months",
    "nodes",
    "GPUs",
    "kW",
    "kWh",
    "bytes",
    "GB",
    "fraction",
    "ratio",
    "text",
]


class StrictModel(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", allow_inf_nan=False, frozen=True)


class Evidence(StrictModel):
    input_id: str
    value: float | str | list[float] | None
    unit: Unit
    source_id: str | None
    source_url: str | None
    source_locator: str | None
    observed_at_utc: datetime | None
    effective_at: date | None = None
    published_at: date | None = None
    region: str | None
    currency: Literal["USD"] | None
    configuration_id: str | None
    evidence_class: Literal[
        "observed", "derived", "analyst_assumption", "user_assumption", "unavailable"
    ]
    measurement_kind: Literal[
        "list_price",
        "vendor_spec",
        "benchmark_measurement",
        "financial_disclosure",
        "survey_reference",
        "user_measurement",
        "hypothetical",
    ]
    user_adjustable: bool
    confidence_note: str
    limitations: str
    raw_artifact_sha256: str | None
    parser_version: str
    review_status: Literal["reviewed", "pending"]
    formula_id: str | None = None
    parent_input_ids: list[str] = []
    rationale: str | None = None
    low: float | None = None
    base: float | None = None
    high: float | None = None
    null_reason: str | None = None
    zero_assertion: str | None = None

    @model_validator(mode="after")
    def integrity(self):
        if self.value is None and not self.null_reason:
            raise ValueError("null requires a reason")
        if self.evidence_class == "unavailable" and self.value is not None:
            raise ValueError("unavailable must be null")
        if self.value == 0 and not self.zero_assertion:
            raise ValueError("zero requires an assertion")
        if self.evidence_class == "observed" and not all(
            [
                self.source_id,
                self.source_url,
                self.source_locator,
                self.observed_at_utc,
                self.raw_artifact_sha256,
            ]
        ):
            raise ValueError("observation requires traceable artifact")
        if self.evidence_class == "derived" and not (self.formula_id and self.parent_input_ids):
            raise ValueError("derived inputs require formula and parents")
        if self.evidence_class.endswith("assumption") and not self.rationale:
            raise ValueError("assumptions require rationale")
        if self.evidence_class == "user_assumption" and not self.parent_input_ids:
            raise ValueError("override must preserve original input")
        if self.low is not None and self.high is not None and self.low > self.high:
            raise ValueError("inverted assumption bounds")
        return self


class Workload(StrictModel):
    workload_id: str
    model: Literal["gpt-oss-120b", "llama2-70b-99.9"]
    revision: str
    release: Literal["v6.1"] = "v6.1"
    scenario: Literal["Offline"] = "Offline"
    quality: str
    dataset: str
    precision: str
    runtime: str
    topology: str
    benchmark_id: str
    performance_tokens_s: Positive | None
    measurement_kind: Literal["benchmark_measurement", "user_measurement", "hypothetical"] = (
        "benchmark_measurement"
    )
    transfer_differences: str = Field(min_length=1)


class Ancillary(StrictModel):
    item_id: str
    mode: Literal["fixed_monthly", "per_billed_node_hour", "egress_GB", "storage_GB_month"]
    scope: Literal["shared", "on_demand", "commit", "own"]
    rate_usd: Nonnegative
    quantity: Nonnegative = 1.0
    included_in_base: bool = False
    rationale: str = Field(min_length=1)


class RunInput(StrictModel):
    schema_version: Literal["1.0"] = "1.0"
    model_version: Literal["0.1.0"] = "0.1.0"
    analysis_as_of: date = date(2026, 9, 27)
    data_snapshot_id: str
    source_checksums: dict[str, str]
    evidence: list[Evidence]
    override_history: list[Evidence] = []
    scenario_id: str
    configuration_id: str
    gpu_count: Annotated[int, Field(gt=0)] = 8
    region: Literal["North America"] = "North America"
    currency: Literal["USD"] = "USD"
    workload: Workload
    benchmark_references: list[Workload] = []
    start_date: date = date(2026, 10, 1)
    horizon_months: Annotated[int, Field(ge=1, le=120)] = 36
    demand_scale_tokens_s: Positive = 71892.1
    demand_base_nodes: list[Nonnegative] = [4.0, 8.0]
    block_fractions: list[Positive] = [0.8, 0.2]
    demand_growth_fraction: Annotated[float, Field(gt=-1, le=1)] = 0.005
    demand_multiplier: Nonnegative = 1.0
    demand_disappointment: bool = False
    custom_demand_tokens: list[list[Nonnegative]] | None = None
    transfer_fraction: Fraction = 0.7
    od_transfer_fraction: Fraction = 0.7
    availability_fraction: Fraction = 0.98
    od_availability_fraction: Fraction = 0.98
    max_od_nodes: Nodes | None = 32
    assumed_max_od_nodes: Nodes | None = None
    capacity_acknowledged: bool = True
    max_fleet_nodes: Annotated[int, Field(ge=1, le=128)] = 32
    spare_nodes: Nodes = 0
    delay_months: Annotated[int, Field(ge=0)] = 0
    usable_life_months: Annotated[int, Field(ge=1)] = 36
    billing_quantum_hours: Positive = 1.0
    startup_hours: Nonnegative = 0.0
    od_price_usd: Nonnegative | None = 68.8
    future_price_multiplier: Nonnegative = 1.0
    commit_price_usd: Nonnegative | None = 40.0
    commit_term_months: Annotated[int, Field(ge=1)] = 36
    commit_setup_usd: Nonnegative = 0.0
    prepaid_fraction: Share = 0.0
    commit_fee_monthly_usd: Nonnegative = 0.0
    node_acquisition_usd: Nonnegative | None = 400000.0
    acquisition_includes: list[Literal["installation", "network", "storage"]] = []
    install_usd: Nonnegative = 50000.0
    network_usd: Nonnegative = 0.0
    storage_usd: Nonnegative = 0.0
    fixed_operations_annual_usd: Nonnegative = 24000.0
    per_node_operations_annual_usd: Nonnegative = 4000.0
    precommission_monthly_usd: Nonnegative = 0.0
    idle_kw: Nonnegative = 2.0
    load_kw: Nonnegative = 10.0
    auxiliary_kw: Nonnegative = 0.0
    pue: Annotated[float, Field(ge=1)] = 1.25
    electricity_usd_kwh: Nonnegative = 0.1
    hosting_mode: Literal["metered_energy", "all_in_colo"] = "metered_energy"
    all_in_colo_monthly_usd: Nonnegative = 0.0
    contracted_kw: Nonnegative = 0.0
    demand_charge_usd_kw_month: Nonnegative = 0.0
    space_monthly_usd: Nonnegative = 0.0
    other_site_monthly_usd: Nonnegative = 0.0
    discount_rate_fraction: Nonnegative = 0.1
    residual_usd: Nonnegative = 0.0
    exit_usd: Nonnegative = 0.0
    upfront_cash_limit_usd: Nonnegative | None = None
    variable_usd_million_tokens: Nonnegative = 0.0
    ancillary: list[Ancillary] = []
    historical_snapshot: bool = True
    stale_acknowledged: bool = False
    comparison_filters: dict[str, str] = {}

    @model_validator(mode="after")
    def constraints(self):
        for component, cost in [
            ("installation", self.install_usd),
            ("network", self.network_usd),
            ("storage", self.storage_usd),
        ]:
            if component in self.acquisition_includes and cost != 0:
                raise ValueError("Acquisition quote includes separately charged " + component)
        if self.start_date.day != 1:
            raise ValueError("calendar must start at month boundary")
        if not self.block_fractions or len(self.block_fractions) != len(self.demand_base_nodes):
            raise ValueError("nonempty matching demand blocks required")
        if abs(sum(self.block_fractions) - 1) > 1e-12:
            raise ValueError("blocks must partition month")
        if self.delay_months > self.horizon_months:
            raise ValueError("delay exceeds horizon")
        if self.idle_kw > self.load_kw:
            raise ValueError("idle exceeds load power")
        if self.hosting_mode == "all_in_colo" and (
            self.electricity_usd_kwh or self.demand_charge_usd_kw_month or self.space_monthly_usd
        ):
            raise ValueError("all-in hosting forbids duplicate energy/space/demand charges")
        if self.custom_demand_tokens is not None and (
            len(self.custom_demand_tokens) != self.horizon_months
            or any(len(x) != len(self.block_fractions) for x in self.custom_demand_tokens)
        ):
            raise ValueError("custom demand dimensions must match calendar blocks")
        for items in [self.evidence, self.override_history]:
            if len({e.input_id for e in items}) != len(items):
                raise ValueError("duplicate provenance keys")
        if len({a.item_id for a in self.ancillary}) != len(self.ancillary):
            raise ValueError("duplicate ancillary service")
        return self


class Policy(StrictModel):
    family: Literal["on_demand", "commit", "own"]
    nodes: Nodes

    @model_validator(mode="after")
    def nodes_match(self):
        if (self.family == "on_demand") != (self.nodes == 0):
            raise ValueError("only all-on-demand has zero baseline nodes")
        return self

    @property
    def policy_id(self):
        return f"{self.family}:{self.nodes}"


class ValidationReport(StrictModel):
    errors: list[str] = []
    warnings: list[str] = []
    policy_exclusions: dict[str, str] = {}
    source_freshness: dict[str, str] = {}


class PolicyResult(StrictModel):
    policy_id: str
    family: Literal["on_demand", "commit", "own"]
    nodes: Nodes
    configuration_id: str
    status: Literal["conditional", "ineligible", "unavailable"]
    pv_cost_usd: float | None = None
    tco_usd: float | None = None
    upfront_usd: Nonnegative | None = None
    obligation_usd: Nonnegative | None = None
    delivered_tokens: Nonnegative = 0.0
    unmet_tokens: Nonnegative = 0.0
    service_fraction: Share | None = None
    execution_utilization: Share | None = None
    available_utilization: Share | None = None
    unused_paid_share: Share | None = None
    unused_commitment_usd: Nonnegative | None = None
    levelized_usd_million_tokens: float | None = None
    undiscounted_usd_million_tokens: float | None = None
    effective_gpu_hours: Nonnegative = 0.0
    billed_rental_gpu_hours: Nonnegative = 0.0
    owned_calendar_gpu_hours: Nonnegative = 0.0
    effective_gpu_hour_cost_usd: float | None = None
    monthly_ledger: list[dict] = []
    block_ledger: list[dict] = []
    cost_ledger: list[dict] = []
    category_pv_usd: dict[str, float] = {}
    warnings: list[str] = []
    source_dependencies: list[str] = []
