"""
ui/styles.py - Custom dark control-room theme and responsive styling for CityPulse V2
"""

def get_custom_css() -> str:
    """Returns CSS injection string for Streamlit app."""
    return """
<style>
    /* Google Fonts import */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

    /* Global Typography & Deep Dark Background */
    html, body, [class*="css"], .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        background-color: #0B0F19 !important;
        color: #F8FAFC !important;
    }
    
    [data-testid="stAppViewContainer"] {
        background-color: #0B0F19 !important;
    }

    [data-testid="stHeader"] {
        background-color: rgba(11, 15, 25, 0.85) !important;
        backdrop-filter: blur(10px) !important;
    }

    [data-testid="stSidebar"] {
        background-color: #0E1322 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
    }
    
    code, pre, .mono-font {
        font-family: 'JetBrains Mono', monospace !important;
    }

    /* Radar Pulsing Indicator */
    @keyframes live-pulse-green {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
        70% { transform: scale(1.08); box-shadow: 0 0 0 9px rgba(16, 185, 129, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
    }
    @keyframes live-pulse-amber {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(245, 158, 11, 0.7); }
        70% { transform: scale(1.08); box-shadow: 0 0 0 9px rgba(245, 158, 11, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(245, 158, 11, 0); }
    }
    @keyframes live-pulse-red {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); }
        70% { transform: scale(1.08); box-shadow: 0 0 0 9px rgba(239, 68, 68, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
    }

    .pulse-dot-green {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background-color: #10B981;
        animation: live-pulse-green 2s infinite ease-in-out;
        margin-right: 6px;
        vertical-align: middle;
    }
    .pulse-dot-amber {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background-color: #F59E0B;
        animation: live-pulse-amber 2s infinite ease-in-out;
        margin-right: 6px;
        vertical-align: middle;
    }
    .pulse-dot-red {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background-color: #EF4444;
        animation: live-pulse-red 2s infinite ease-in-out;
        margin-right: 6px;
        vertical-align: middle;
    }

    /* Demo Notice Banner */
    .demo-notice-banner {
        background: rgba(245, 158, 11, 0.12);
        border: 1px solid rgba(245, 158, 11, 0.35);
        border-left: 5px solid #F59E0B;
        border-radius: 8px;
        padding: 11px 16px;
        margin-bottom: 20px;
        color: #FDE68A;
        font-size: 13px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 8px;
    }

    /* Status Badges */
    .pulse-badge-CRITICAL {
        background: rgba(239, 68, 68, 0.18) !important;
        color: #F87171 !important;
        border: 1px solid rgba(239, 68, 68, 0.5) !important;
        padding: 5px 14px;
        border-radius: 8px;
        font-weight: 700;
        font-size: 13px;
        letter-spacing: 0.04em;
        display: inline-flex;
        align-items: center;
        box-shadow: 0 0 14px rgba(239, 68, 68, 0.25);
    }
    .pulse-badge-ELEVATED {
        background: rgba(249, 115, 22, 0.18) !important;
        color: #FB923C !important;
        border: 1px solid rgba(249, 115, 22, 0.5) !important;
        padding: 5px 14px;
        border-radius: 8px;
        font-weight: 700;
        font-size: 13px;
        letter-spacing: 0.04em;
        display: inline-flex;
        align-items: center;
        box-shadow: 0 0 14px rgba(249, 115, 22, 0.25);
    }
    .pulse-badge-ATTENTION {
        background: rgba(245, 158, 11, 0.18) !important;
        color: #FBBF24 !important;
        border: 1px solid rgba(245, 158, 11, 0.5) !important;
        padding: 5px 14px;
        border-radius: 8px;
        font-weight: 700;
        font-size: 13px;
        letter-spacing: 0.04em;
        display: inline-flex;
        align-items: center;
        box-shadow: 0 0 14px rgba(245, 158, 11, 0.25);
    }
    .pulse-badge-NORMAL {
        background: rgba(16, 185, 129, 0.18) !important;
        color: #34D399 !important;
        border: 1px solid rgba(16, 185, 129, 0.5) !important;
        padding: 5px 14px;
        border-radius: 8px;
        font-weight: 700;
        font-size: 13px;
        letter-spacing: 0.04em;
        display: inline-flex;
        align-items: center;
        box-shadow: 0 0 14px rgba(16, 185, 129, 0.25);
    }

    /* Control Room Card Containers */
    .civic-card {
        background: #111827 !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 12px;
        padding: 18px 22px;
        margin-bottom: 18px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.35);
        transition: border-color 0.2s ease, transform 0.2s ease;
    }
    .civic-card:hover {
        border-color: rgba(255, 255, 255, 0.18) !important;
    }

    .hero-pulse-card {
        background: linear-gradient(135deg, #111827 0%, #1e293b 100%) !important;
        border: 1px solid rgba(255, 255, 255, 0.14) !important;
        border-radius: 14px;
        padding: 24px 28px;
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.45);
        position: relative;
        overflow: hidden;
        margin-bottom: 22px;
    }

    /* KPI Modern Cards */
    .kpi-card {
        background: #131B2E !important;
        border: 1px solid rgba(255, 255, 255, 0.09) !important;
        border-radius: 12px;
        padding: 16px 18px;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        box-shadow: 0 4px 16px rgba(0,0,0,0.25);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .kpi-card:hover {
        border-color: rgba(59, 130, 246, 0.45) !important;
        transform: translateY(-2px);
    }
    .kpi-title {
        font-size: 12px;
        font-weight: 600;
        color: #94A3B8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .kpi-value {
        font-size: 28px;
        font-weight: 800;
        color: #F8FAFC;
        line-height: 1.1;
        margin-bottom: 6px;
    }
    .kpi-delta {
        font-size: 11.5px;
        font-weight: 500;
        color: #CBD5E1;
        display: flex;
        align-items: center;
        gap: 4px;
    }
    .kpi-badge-alert {
        background: rgba(239, 68, 68, 0.22);
        color: #F87171;
        border: 1px solid rgba(239, 68, 68, 0.4);
        padding: 2px 8px;
        border-radius: 4px;
        font-weight: 700;
        font-size: 11px;
    }
    .kpi-badge-normal {
        background: rgba(16, 185, 129, 0.22);
        color: #34D399;
        border: 1px solid rgba(16, 185, 129, 0.4);
        padding: 2px 8px;
        border-radius: 4px;
        font-weight: 700;
        font-size: 11px;
    }

    /* Evidence Flow Chain */
    .evidence-chain-container {
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: 10px;
        background: rgba(15, 23, 42, 0.7);
        border: 1px dashed rgba(255, 255, 255, 0.15);
        border-radius: 10px;
        padding: 14px 16px;
        margin: 12px 0;
    }
    .evidence-step {
        background: #1E293B;
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 8px;
        padding: 8px 12px;
        font-size: 12.5px;
        color: #F1F5F9;
        display: flex;
        align-items: center;
        gap: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    }
    .evidence-arrow {
        color: #38BDF8;
        font-size: 15px;
        font-weight: bold;
    }

    /* Grounded Civic Narrative Box */
    .narrative-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.9) 0%, rgba(15, 23, 42, 0.95) 100%) !important;
        border: 1px solid rgba(59, 130, 246, 0.4) !important;
        border-left: 6px solid #3B82F6 !important;
        border-radius: 12px;
        padding: 20px 24px;
        margin-bottom: 22px;
        box-shadow: 0 6px 24px rgba(15, 23, 42, 0.6);
    }

    /* Active Anomaly Item Card */
    .anomaly-row-card {
        background: #111827;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 10px;
        transition: border-color 0.15s ease;
    }
    .anomaly-row-card:hover {
        border-color: rgba(255, 255, 255, 0.2);
    }

    /* Zone Grid Cards */
    .zone-cell-card {
        background: #111827 !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 10px;
        padding: 14px 16px;
        text-align: center;
        transition: transform 0.15s ease, border-color 0.15s ease;
        height: 100%;
    }
    .zone-cell-card:hover {
        transform: translateY(-2px);
        border-color: rgba(255, 255, 255, 0.22) !important;
    }

    /* Scientific Disclaimer Box */
    .disclaimer-box {
        background: rgba(30, 41, 59, 0.6);
        border-left: 3px solid #64748B;
        border-radius: 6px;
        padding: 10px 14px;
        font-size: 12px;
        color: #94A3B8;
        font-style: italic;
        margin-top: 10px;
    }

    /* Custom Scrollbars */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    ::-webkit-scrollbar-track {
        background: #0B0F19;
    }
    ::-webkit-scrollbar-thumb {
        background: #1E293B;
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #334155;
    }

    /* Streamlit components dark overrides */
    div[data-testid="stMetricValue"] {
        font-size: 1.85rem !important;
        font-weight: 800 !important;
        color: #F8FAFC !important;
    }
    div[data-testid="stMetricLabel"] {
        color: #94A3B8 !important;
        font-size: 0.85rem !important;
        font-weight: 600 !important;
    }
    
    div[data-testid="stExpander"] {
        border: 1px solid rgba(255, 255, 255, 0.09) !important;
        background: #111827 !important;
        border-radius: 10px !important;
    }
    div[data-testid="stExpander"] summary {
        color: #E2E8F0 !important;
        font-weight: 600 !important;
    }

    /* Streamlit Folium map wrapper */
    .stFolium iframe {
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.12);
        box-shadow: 0 6px 20px rgba(0,0,0,0.4);
    }
</style>
"""
