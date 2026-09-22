"""Preliminary eligibility logic for business-loan qualification (Q1 action).

Rules mirror the KB eligibility records so the agent's computed verdict stays
consistent with what the knowledge base says. This is a *preliminary* check,
explicitly not a final credit decision.
"""
from __future__ import annotations

from dataclasses import dataclass

MIN_REVENUE_LAKH = 20.0
MIN_VINTAGE_MONTHS = 24
MIN_AGE = 21
MAX_AGE = 65
STANDARD_SCORE = 700
MARGINAL_SCORE = 650


@dataclass
class EligibilityResult:
    verdict: str          # "likely_eligible" | "marginal" | "not_eligible"
    reasons: list[str]
    suggested_products: list[str]
    disclaimer: str


def check_eligibility(
    *,
    annual_revenue_lakh: float | None = None,
    vintage_months: int | None = None,
    credit_score: int | None = None,
    applicant_age: int | None = None,
) -> EligibilityResult:
    reasons: list[str] = []
    hard_fail = False
    marginal = False

    if annual_revenue_lakh is not None:
        if annual_revenue_lakh < MIN_REVENUE_LAKH:
            reasons.append(
                f"Annual revenue {annual_revenue_lakh} lakh is below the {MIN_REVENUE_LAKH} lakh minimum."
            )
            hard_fail = True
        else:
            reasons.append(f"Revenue {annual_revenue_lakh} lakh meets the minimum.")

    if vintage_months is not None:
        if vintage_months < MIN_VINTAGE_MONTHS:
            reasons.append(
                f"Business vintage {vintage_months} months is below the {MIN_VINTAGE_MONTHS}-month minimum."
            )
            hard_fail = True
        else:
            reasons.append(f"Vintage {vintage_months} months meets the minimum.")

    if applicant_age is not None and not (MIN_AGE <= applicant_age <= MAX_AGE):
        reasons.append(f"Applicant age {applicant_age} is outside the {MIN_AGE}-{MAX_AGE} range.")
        hard_fail = True

    if credit_score is not None:
        if credit_score < MARGINAL_SCORE:
            reasons.append(f"Credit score {credit_score} is below {MARGINAL_SCORE}; typically declined.")
            hard_fail = True
        elif credit_score < STANDARD_SCORE:
            reasons.append(
                f"Credit score {credit_score} qualifies at a higher rate ({MARGINAL_SCORE}-{STANDARD_SCORE-1} band)."
            )
            marginal = True
        else:
            reasons.append(f"Credit score {credit_score} qualifies for standard pricing.")

    if hard_fail:
        verdict = "not_eligible"
        products: list[str] = []
    elif marginal:
        verdict = "marginal"
        products = ["working_capital", "line_of_credit"]
    else:
        verdict = "likely_eligible"
        products = ["term_loan", "working_capital", "line_of_credit"]

    return EligibilityResult(
        verdict=verdict,
        reasons=reasons,
        suggested_products=products,
        disclaimer="Preliminary only. Final approval depends on document verification and credit review.",
    )
