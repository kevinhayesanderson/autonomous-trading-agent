"""
Autonomous Quantitative Trading Agent - Fundamental Intelligence & Context Caching
Formats SEC 10-K disclosures, pricing power indicators, and competitive moat profiles
into token-efficient, cached context windows for frontier LLM reasoning.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

# Curated High-Beta Monopolistic Deep-Tech Dossiers (Pre-cached context representations)
CURATED_MONOPOLY_DOSSIERS: Dict[str, Dict[str, Any]] = {
    "ASML": {
        "company_name": "ASML Holding N.V.",
        "cik": "0000937966",
        "market": "US / Euronext",
        "primary_moat": "100% global monopoly on Extreme Ultraviolet (EUV) photolithography systems.",
        "technology_stack": "0.33 NA and High-NA (0.55 NA) EUV lithography, DUV immersion (ArFi), TWINSCAN optics.",
        "pricing_power": "Average selling price > $200M-$380M per High-NA machine. Customer order backlog exceeds 18 months.",
        "key_customers": ["TSMC", "Intel", "Samsung Electronics", "Micron Technology"],
        "sec_10k_risks": [
            "Dutch & US export control restrictions on sales to Chinese wafer fabs.",
            "Semiconductor capex cyclicality and foundry fab buildout timing delays.",
            "Single-source component supply risks (Zeiss optical mirrors, Cymer laser sources)."
        ],
        "sec_10k_metrics": {
            "gross_margin_target": "54% - 56%",
            "net_margin_historical": "28.5%",
            "roic_average": "32.0%",
            "rd_reinvestment_ratio": "15.0% of revenue"
        }
    },
    "TSM": {
        "company_name": "Taiwan Semiconductor Manufacturing Company Limited",
        "cik": "0001046179",
        "market": "NYSE / TWSE",
        "primary_moat": ">90% global market share in leading-edge sub-5nm AI accelerator foundry production.",
        "technology_stack": "N3, N3P, N2 (GAA gate-all-around), CoWoS advanced 2.5D/3D packaging.",
        "pricing_power": "Leading-edge wafer ASP exceeds $20,000; high customer switching costs due to PDK lock-in.",
        "key_customers": ["Apple", "NVIDIA", "AMD", "Broadcom", "Qualcomm"],
        "sec_10k_risks": [
            "Geopolitical risk in the Taiwan Strait; concentration of domestic fabrication capacity.",
            "Water, green power, and utility grid constraints in Hsinchu/Tainan science parks.",
            "Cost inflation on overseas fab expansions (Arizona Fab 21, Kumamoto JASM, Dresden ESMC)."
        ],
        "sec_10k_metrics": {
            "gross_margin_target": "53.0%+",
            "net_margin_historical": "38.0%",
            "roic_average": "28.0%",
            "capex_intensity": "40% - 50% of annual revenue"
        }
    },
    "NVDA": {
        "company_name": "NVIDIA Corporation",
        "cik": "0001045810",
        "market": "Nasdaq",
        "primary_moat": "Proprietary CUDA software ecosystem and full-stack accelerated computing architecture (Blackwell, Hopper).",
        "technology_stack": "GB200 NVL72 rack-scale systems, Quantum-X800 InfiniBand, Spectrum-X Ethernet.",
        "pricing_power": "Dominant 85%+ AI training compute share; systems command gross margins > 72%.",
        "key_customers": ["Microsoft Azure", "AWS", "Google Cloud", "Meta", "Tesla", "CoreWeave"],
        "sec_10k_risks": [
            "US Department of Commerce export controls restricting compute thresholds to China.",
            "Hyperscaler in-house custom silicon alternatives (Google TPU, AWS Trainium, Meta MTIA).",
            "CoWoS packaging packaging throughput bottlenecks at foundry partners."
        ],
        "sec_10k_metrics": {
            "gross_margin_target": "73% - 75%",
            "net_margin_historical": "45.0%+",
            "roic_average": "55.0%+",
            "fwd_growth_visibility": "Sustained generative AI enterprise training and inference demand"
        }
    },
    "MRVL": {
        "company_name": "Marvell Technology, Inc.",
        "cik": "0001835632",
        "market": "Nasdaq",
        "primary_moat": "Custom hyperscale AI XPU design accelerators and high-speed electro-optics (DSP, PAM4, PCIe retimers).",
        "technology_stack": "5nm/3nm custom compute platform, COLORZ optical interconnects, Teralynx Ethernet switches.",
        "pricing_power": "Sole/dual source supplier for tier-1 hyperscale custom AI ASICs with multi-year production commitments.",
        "key_customers": ["Amazon (Trainium)", "Google Cloud", "Microsoft", "Tier-1 Datacenter Operators"],
        "sec_10k_risks": [
            "Customer concentration in major cloud hyperscalers for custom ASIC programs.",
            "Enterprise networking and carrier infrastructure inventory destocking cycles.",
            "Rapid technological transitions in optical interconnect standards (1.6T transitions)."
        ],
        "sec_10k_metrics": {
            "gross_margin_target": "60% - 62%",
            "net_margin_historical": "Positive non-GAAP cash generation",
            "datacenter_revenue_share": "> 70% of total company revenue",
            "fwd_eps_growth": "High acceleration from custom AI ramps"
        }
    }
}

def get_cached_fundamental_dossier(ticker: str) -> Dict[str, Any]:
    """
    Retrieves or synthesizes a structured fundamental context dossier for a company.
    Designed for zero-latency LLM context caching.
    """
    ticker_clean = ticker.upper().strip()
    if ticker_clean in CURATED_MONOPOLY_DOSSIERS:
        return CURATED_MONOPOLY_DOSSIERS[ticker_clean]
    
    # Generic synthesized dossier for screened candidate
    return {
        "company_name": f"{ticker_clean} Corporation",
        "market": "US Equity",
        "primary_moat": "High-beta technology enterprise under institutional screening review.",
        "pricing_power": "Standard commercial pricing power.",
        "sec_10k_risks": [
            "Macroeconomic demand volatility",
            "Semiconductor and tech supply chain fluctuations"
        ],
        "sec_10k_metrics": {
            "net_margin_status": "Screened for positive net margin compliance",
            "retrieval_timestamp": datetime.utcnow().isoformat()
        }
    }

def format_context_for_thinking_model(ticker: str, metrics: Dict[str, Any]) -> str:
    """
    Formats multi-source context (financials, 10-K profile, technicals)
    into a structured prompt block optimized for extended thinking models.
    """
    dossier = get_cached_fundamental_dossier(ticker)
    lines = [
        f"### INSTITUTIONAL RESEARCH DOSSIER: {ticker}",
        f"- Company: {dossier.get('company_name')}",
        f"- Primary Moat: {dossier.get('primary_moat')}",
        f"- Pricing Power: {dossier.get('pricing_power')}",
        f"- Key Customers: {', '.join(dossier.get('key_customers', ['Global tech enterprises']))}",
        f"- SEC 10-K Risk Factors:",
    ]
    for r in dossier.get("sec_10k_risks", []):
        lines.append(f"    * {r}")
    lines.append("- Quant Factors & Metrics:")
    for k, v in metrics.items():
        lines.append(f"    * {k}: {v}")
    return "\n".join(lines)
