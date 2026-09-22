"""Sample business-loan source content (Q2 input).

This simulates the assessment's "mixed business content": web sections,
policy/qualification rules, FAQs, objections, tables, plus intentional
duplicates, inconsistent terminology (WC loan, ROI, turnover), and one record
containing PII — so the cleaning pipeline has real work to do.

In production, `raw_sources` would come from a scraper/parser. Here they are
inline HTML/text blobs to keep the KB reproducible offline.
"""
from __future__ import annotations

# Each source: (source_ref, category, subcategory, title, raw_html_or_text)
RAW_SOURCES: list[tuple[str, str, str, str, str]] = [
    (
        "website:/loans/products",
        "product", "term_loan", "Business Term Loan",
        """<nav>Home About Us Contact Login</nav>
        <h1>Business Term Loan</h1>
        <p>Our business term loan offers 5 lakh to 50 lakh in funding with fixed
        EMIs over 12 to 48 months. Funds can be used for expansion, hiring, or
        inventory. Disbursal typically happens within 3 business days of approval.</p>
        <footer>All rights reserved. Privacy Policy</footer>""",
    ),
    (
        "website:/loans/working-capital",
        "product", "working_capital", "Working Capital Loan",
        """<h1>WC loan</h1><p>A working capital loan (WC loan) helps cover
        day-to-day operating expenses. Limits range from 2 lakh to 25 lakh with
        flexible repayment. The ROI starts at 14% per annum depending on profile.</p>""",
    ),
    (
        "website:/loans/line-of-credit",
        "product", "line_of_credit", "Business Line of Credit",
        """<p>A business line of credit gives you a revolving limit you can draw
        from as needed. You pay interest rate only on the amount used. Ideal for
        seasonal businesses with variable cash flow.</p>""",
    ),
    (
        "policy:/eligibility",
        "qualification", "revenue_rules", "Eligibility: Revenue and Vintage",
        """<h2>Eligibility Rules</h2><p>To qualify, the business must have a
        minimum annual revenue of 20 lakh, be operational for at least 24 months
        (business vintage), and the applicant must be 21 to 65 years old.
        turnover below 20 lakh is not eligible for the term loan.</p>""",
    ),
    (
        "policy:/eligibility",
        "qualification", "credit_score_rules", "Eligibility: Credit Score",
        """<p>A minimum credit score of 700 is required for standard pricing.
        Applicants between 650 and 699 may still qualify at a higher interest rate.
        Below 650 the application is typically declined.</p>""",
    ),
    (
        "policy:/documentation",
        "policy", "documentation", "Documents Required to Apply",
        """<p>To apply you need these documents: PAN and Aadhaar of the applicant,
        last 6 months bank statements, last 2 years financial statements or ITR,
        and GST registration where applicable.</p>""",
    ),
    (
        "policy:/interest-and-fees",
        "policy", "interest_and_fees", "Interest Rates and Fees",
        """<p>Interest rate ranges from 14% to 24% per annum on a reducing balance.
        A one-time processing fee of up to 2% of the loan amount applies.
        There are no hidden charges.</p>""",
    ),
    (
        "policy:/repayment",
        "policy", "repayment", "Repayment and Prepayment",
        """<p>Repayment is via monthly EMIs through auto-debit. pre-payment is
        allowed after 6 EMIs with a prepayment fee of 3% on the outstanding
        principal. Part-prepayment is permitted once per year.</p>""",
    ),
    (
        "faq:/application",
        "faq", "application_process", "How do I apply?",
        """<p>You can apply over this call or online. We collect basic business
        details, run a soft eligibility check, and a relationship manager follows
        up. No branch visit is required for the initial application.</p>""",
    ),
    (
        "faq:/disbursal",
        "faq", "disbursal", "How long until I get the money?",
        """<p>After approval and document verification, disbursal to your business
        bank account typically takes 3 business days.</p>""",
    ),
    (
        "objection:/rate",
        "objection", "rate_too_high", "Objection: The interest rate is too high",
        """<p>Rates are risk-based and depend on credit score, revenue, and vintage.
        Applicants with a score above 750 and strong revenue get our lowest rates.
        We can share the exact rate after a soft check with no impact on credit score.</p>""",
    ),
    (
        "objection:/paperwork",
        "objection", "too_much_paperwork", "Objection: Too much paperwork",
        """<p>Most documents are digital. Bank statements can be fetched securely
        with your consent, and the initial eligibility check needs only a few
        business details.</p>""",
    ),
    (
        "objection:/security",
        "objection", "trust_security", "Objection: Is my data safe?",
        """<p>Your data is encrypted in transit and at rest, used only for loan
        assessment, and never sold. You can request deletion at any time.</p>""",
    ),
    (
        "website:/partners/branch",
        "partnership_benefits", "branch", "Branch Partnership Benefits",
        """<p>Operational, marketing, and technology support is provided to branch
        partners, including lead sharing and co-branded campaigns.</p>""",
    ),
    # --- Intentional NEAR-DUPLICATE of the term loan product (should be dropped) ---
    (
        "website:/loans/products-copy",
        "product", "term_loan", "Business Term Loan (mirror page)",
        """<p>Our business term loan offers 5 lakh to 50 lakh in funding with fixed
        EMIs over 12 to 48 months. Funds can be used for expansion, hiring, or
        inventory. Disbursal typically happens within 3 business days of approval.</p>""",
    ),
    # --- Intentional PII-containing record (should be flagged + redacted) ---
    (
        "crm-export:/sample-lead",
        "faq", "general", "Sample lead note (contains PII)",
        """<p>Lead Ramesh Kumar, phone 98765 43210, email ramesh.k@example.com,
        requested a 10 lakh working capital loan. Follow up next week.</p>""",
    ),
    # --- Intentional broken extraction (should be flagged) ---
    (
        "website:/loans/broken",
        "faq", "general", "Broken page",
        """<h1>404 Not Found</h1><p>undefined</p>""",
    ),
]
