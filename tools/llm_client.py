import os
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Iterator

from dotenv import load_dotenv

load_dotenv()

_session_tokens: ContextVar[object | None] = ContextVar(
    "chatgpt_session_tokens",
    default=None,
)


@contextmanager
def use_session_tokens(tokens: object | None) -> Iterator[None]:
    """Make tokens available to LLM calls in the current pipeline context."""
    context_token = _session_tokens.set(tokens)
    try:
        yield
    finally:
        _session_tokens.reset(context_token)


def _is_test_mode() -> bool:
    return os.getenv("TEST_MODE", "false").lower() in ("true", "1", "yes")


def _mock_response(prompt: str) -> str:
    if "produce a JSON object with the following exact keys" in prompt:
        return """
{
  "name": "VentureValuator",
  "problem": ["Early-stage founders struggle to validate business ideas quickly.", "Investors waste time manually analyzing inconsistent, poorly structured pitch decks."],
  "solution": ["VentureValuator automated analysis system.", "Unified dashboard presenting score, market metrics, and financial models."],
  "target_customer": ["Early-stage startup founders", "Angel investors and venture capital firms"],
  "business_model": ["SaaS subscription model for VC teams", "Pay-per-report model for founders"],
  "pricing": ["$19 per deck analysis or $299/mo for VC teams"],
  "gtm_strategy": ["Direct outreach to startup incubators and accelerators", "Content marketing targeting venture capital platforms"],
  "cost_structure": ["Cloud hosting and API processing costs", "Marketing and direct sales staff"],
  "competition": ["Standard VC analyst teams", "Pitch deck design agencies", "Self-made templates"],
  "notable_metrics": {
    "revenue_last_month": "12000",
    "mau": "1500",
    "mom_growth": "15%",
    "nps": "65",
    "repeat_rate": "80%",
    "marketing_cost_monthly": "4000",
    "tech_cost_monthly": "2000"
  },
  "assumptions": ["Startup pitch deck contains basic metrics.", "Founders are willing to pay for fast verification."]
}
"""

    if "create a **12-slide YC-style pitch deck**" in prompt:
        return """
{
  "slides": [
    {"title": "Problem", "bullets": ["Founders waste weeks validating market size and unit economics.", "Investors sift through 100+ messy, unstandardized pitch decks weekly."]},
    {"title": "Target User", "bullets": ["Solo founders looking for rapid valuation checks.", "Busy investors wanting consistent, parsed memos."]},
    {"title": "Current Behavior", "bullets": ["Founders hire expensive consulting analysts.", "Manual spreadsheet calculations that are error-prone."]},
    {"title": "Solution", "bullets": ["VentureValuator: An automated multi-agent analysis system.", "Upload a PDF pitch deck and receive structured evaluation in 2 minutes."]},
    {"title": "Why Now", "bullets": ["Massive surge in early-stage tech startups worldwide.", "Generative AI can now parse and structure messy PDF data accurately."]},
    {"title": "Market Size", "bullets": ["$15B TAM for global venture intelligence and builder tools.", "Focusing initially on early-stage accelerators ($2.5B SAM)."]},
    {"title": "Competition", "bullets": ["Manual analyst reviews (slow & expensive).", "Database giants like PitchBook (expensive, not automated for validation)."]},
    {"title": "Unique Advantage", "bullets": ["Proprietary multi-agent orchestration for extracting, researching, and modeling in minutes.", "Deterministic financial forecasting combined with generative feedback."]},
    {"title": "Business Model", "bullets": ["$19 per individual deck report for founders.", "B2B SaaS subscription starting at $299/mo for VC/Accelerator teams."]},
    {"title": "Traction", "bullets": ["1,500 Monthly Active Users within the first 30 days of launch.", "$12,000 in monthly recurring revenue (MRR) growing at 15% MoM."]},
    {"title": "Financial Projection Summary", "bullets": ["Forecasted to reach $1.2M ARR in Year 2.", "Gross margins stable at 75% due to optimized LLM token consumption."]},
    {"title": "The Ask (Fundraising)", "bullets": ["Raising $500k to expand database integrations.", "Looking to scale sales team targeting global incubators."]}
  ]
}
"""

    if "world-class startup market analyst" in prompt:
        return """
{
  "market_category": "AI Productivity Software / Venture Intelligence",
  "tam": "$15 Billion",
  "sam": "$2.5 Billion",
  "som": "$350 Million",
  "market_growth_rate": "22% CAGR",
  "key_trends": [
    "Increase in AI-driven investment analysis tools.",
    "Founders demanding self-serve valuation platforms.",
    "VC firms automating top-of-funnel screening."
  ],
  "customer_segments": [
    "Angel Investors",
    "Pre-seed/Seed Founders",
    "VC Associates"
  ],
  "competitive_landscape": {
    "direct_competitors": ["PitchBook", "Crunchbase", "Tracxn"],
    "indirect_competitors": ["Manual Excel models", "Slidebean"],
    "competitive_advantages": ["Automated multi-agent workflow", "Instant deterministic financial model creation"],
    "competitive_risks": ["Data privacy concerns sharing draft decks", "Rapid evolution of LLM capabilities"]
  },
  "regional_factors": "Strong tech hub presence in India and North America.",
  "industry_benchmarks": {
    "average_gross_margin": "75%",
    "typical_cac_range": "$50 - $150",
    "ltv_range": "$1200 - $3500",
    "unit_economics_notes": "SaaS margins apply. Customer acquisition cost is offset rapidly within 6 months of usage."
  },
  "opportunities": [
    "Integrating pitch deck generation tools directly into accelerators.",
    "Partnering with corporate innovation hubs."
  ],
  "risks": [
    "High churn among single-report founder users."
  ],
  "summary_insights": "The market is ripe for automated venture intelligence as the volume of global startup pitches increases.",
  "sources": [
    {"title": "Venture Capital Tech Market Report 2025", "url": "https://example.com/vc-tech-market", "snippet": "Global venture intelligence software market estimated at $15B TAM."},
    {"title": "AI in Private Markets - Gartner", "url": "https://example.com/gartner-ai-pm", "snippet": "22% CAGR in AI-powered investment tools through 2028."}
  ]
}
"""

    if "skeptical Series A partner" in prompt:
        return """
{
  "red_flags": [
    "TAM of $15B appears top-down without bottom-up validation from customer segments.",
    "$12K MRR with 1,500 MAU implies ~$8 ARPU — unit economics need clearer path to $50+ ACV for VC SaaS.",
    "Competition includes well-funded incumbents (PitchBook, Crunchbase) with established data moats."
  ],
  "missing_data": [
    "No churn or retention metrics provided.",
    "No CAC or payback period disclosed in the deck.",
    "Team backgrounds and prior exits not mentioned."
  ],
  "challenged_claims": [
    "15% MoM growth claim needs 3+ months of verified data to assess sustainability.",
    "75% gross margin projection assumes LLM costs stay flat as usage scales — unlikely without optimization proof."
  ],
  "partner_questions": [
    "What's your net revenue retention after the first 90 days?",
    "Why won't PitchBook just add an AI screening feature and crush you?",
    "What's the sales cycle length for $299/mo VC teams vs $19 founder reports?",
    "How do you handle confidential deck data — SOC 2, encryption, data retention?"
  ],
  "diligence_next_steps": [
    "Verify MRR and user counts with Stripe/billing export.",
    "Run 5 customer reference calls with VC associates using the product.",
    "Map competitive feature matrix vs PitchBook and Tracxn AI offerings."
  ],
  "skeptic_summary": "Interesting wedge in a large market, but traction is early and competitive moat is unproven. Worth a second meeting if retention data holds up."
}
"""

    if "VC analyst writing the evaluation section" in prompt:
        return """
{
  "strengths": [
    "Clear problem-solution fit targeting both founders and investors in the pitch deck workflow.",
    "$12K MRR and 1,500 MAU demonstrate early product-market signal with 15% MoM growth.",
    "Multi-agent architecture differentiates from single-prompt deck summarizers.",
    "Web-grounded market research adds credibility vs pure LLM hallucination.",
    "Dual revenue model ($19/report + $299/mo SaaS) captures both sides of the market."
  ],
  "risks": [
    "Competitive landscape includes well-capitalized incumbents with proprietary data assets.",
    "Low implied ARPU (~$8) may not support sustainable VC SaaS unit economics without upsell.",
    "Missing churn, CAC, and team credentials weaken diligence readiness.",
    "Data privacy concerns may slow adoption among institutional VC firms."
  ]
}
"""

    return """
# Investment Memo — VentureValuator

Company Overview:
VentureValuator builds AI-powered multi-agent systems to analyze startup pitch decks.

Market Opportunity:
Highly attractive niche in the VC tech stack space.

Recommendation:
Highly recommended for proceeding with due diligence.
"""


def _make_client_from_session_token(model: str):
    """
    Build a client from tokens captured by the Streamlit script thread and
    passed into the current pipeline context.
    """
    tokens = _session_tokens.get()
    if tokens is None:
        raise ValueError("No session token set")

    from login_with_chatgpt.auth.store import MemoryTokenStore
    from login_with_chatgpt._client import ChatGPTAccount

    store = MemoryTokenStore()
    store.save("default", tokens)
    account = ChatGPTAccount(store=store)
    return account.openai()


def _make_client_from_env_token(model: str):
    """
    Cloud-deployment path: if CHATGPT_TOKEN_JSON is set as a secret env var,
    bootstrap the library with MemoryTokenStore so the OS keyring is never touched.
    Returns an openai.OpenAI client or raises if the env var is absent/invalid.
    """
    token_json = os.getenv("CHATGPT_TOKEN_JSON", "").strip()
    if not token_json:
        raise ValueError("CHATGPT_TOKEN_JSON not set")

    import json as _json
    from login_with_chatgpt.auth.store import MemoryTokenStore
    from login_with_chatgpt.auth.models import TokenSet
    from login_with_chatgpt._client import ChatGPTAccount

    payload = _json.loads(token_json)
    tokens = TokenSet(
        access_token=payload["access_token"],
        refresh_token=payload.get("refresh_token"),
        id_token=payload.get("id_token"),
        account_id=payload.get("account_id"),
        expires_at=payload.get("expires_at"),
    )
    store = MemoryTokenStore()
    store.save("default", tokens)
    account = ChatGPTAccount(store=store)
    return account.openai()


def call_llm(prompt: str, model: str | None = None) -> str:
    if _is_test_mode():
        return _mock_response(prompt)

    model = model or os.getenv("CHATGPT_MODEL", "gpt-5.6-sol")

    # 1. Highest priority: User session token (web-based login for visitors)
    try:
        client = _make_client_from_session_token(model)
        resp = client.responses.create(model=model, input=prompt)
        return resp.output_text
    except ValueError:
        pass  # No session token — check fallback paths
    except Exception as session_err:
        print(f"[llm_client] Session token auth failed: {session_err}")

    # 2. Cloud path: token injected via CHATGPT_TOKEN_JSON secret env var
    try:
        client = _make_client_from_env_token(model)
        resp = client.responses.create(model=model, input=prompt)
        return resp.output_text
    except ValueError:
        pass  # env var not set — fall through to local auth
    except Exception as cloud_err:
        print(f"[llm_client] Cloud token auth failed: {cloud_err}")

    # 2. Local keyring (login-with-chatgpt CLI)
    try:
        from login_with_chatgpt import OpenAI

        client = OpenAI()
        try:
            resp = client.responses.create(model=model, input=prompt)
            return resp.output_text
        finally:
            client.close()
    except Exception as keyring_err:
        pass

    # 3. Local proxy fallback
    proxy_url = os.getenv("OPENAI_OAUTH_PROXY_URL", "http://127.0.0.1:10531/v1")
    try:
        from openai import OpenAI as StdOpenAI

        client = StdOpenAI(base_url=proxy_url, api_key="openai-oauth")
        resp = client.responses.create(model=model, input=prompt)
        return resp.output_text
    except Exception as proxy_err:
        raise RuntimeError(
            "ChatGPT auth failed. Options:\n"
            "  Cloud: set CHATGPT_TOKEN_JSON secret\n"
            "  Local: run `uvx login-with-chatgpt login`\n"
            f"  Proxy error: {proxy_err}"
        ) from proxy_err
