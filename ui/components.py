import streamlit as st


def apply_custom_styles():
    """Applies a clean, modern medical/healthcare-grade UI theme."""
    st.markdown("""
    <style>
        /* Import clean modern font */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        /* Top header accent */
        .main-header {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            color: #ffffff;
            padding: 1.5rem 2rem;
            border-radius: 12px;
            margin-bottom: 1.5rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
            border-left: 6px solid #10b981;
        }

        .main-header h1 {
            color: #ffffff !important;
            font-size: 1.85rem;
            font-weight: 700;
            margin: 0;
            letter-spacing: -0.02em;
        }

        .main-header p {
            color: #94a3b8 !important;
            font-size: 0.95rem;
            margin-top: 0.35rem;
            margin-bottom: 0;
        }

        /* Metric cards */
        .metric-card {
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            padding: 1.1rem 1.25rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            transition: all 0.2s ease;
        }

        .metric-card:hover {
            box-shadow: 0 4px 10px rgba(0,0,0,0.08);
            transform: translateY(-2px);
        }

        .metric-label {
            font-size: 0.8rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #64748b;
            margin-bottom: 0.35rem;
        }

        .metric-value {
            font-size: 1.75rem;
            font-weight: 700;
            color: #0f172a;
            margin: 0;
        }

        .metric-sub {
            font-size: 0.75rem;
            color: #94a3b8;
            margin-top: 0.25rem;
        }

        /* Badges */
        .badge {
            display: inline-block;
            padding: 0.25rem 0.65rem;
            font-size: 0.75rem;
            font-weight: 600;
            border-radius: 9999px;
            text-align: center;
        }

        .badge-critical { background-color: #fee2e2; color: #dc2626; border: 1px solid #fecaca; }
        .badge-high { background-color: #ffedd5; color: #ea580c; border: 1px solid #fed7aa; }
        .badge-medium { background-color: #fef9c3; color: #ca8a04; border: 1px solid #fef08a; }
        .badge-low { background-color: #f0fdf4; color: #16a34a; border: 1px solid #dcfce7; }
        .badge-info { background-color: #e0f2fe; color: #0284c7; border: 1px solid #bae6fd; }

        /* Agent workflow log timeline */
        .agent-log-card {
            background-color: #f8fafc;
            border-left: 4px solid #3b82f6;
            border-radius: 6px;
            padding: 0.75rem 1rem;
            margin-bottom: 0.6rem;
            font-size: 0.9rem;
        }
        .agent-log-success { border-left-color: #10b981; }
        .agent-log-warning { border-left-color: #f59e0b; }
        .agent-log-error { border-left-color: #ef4444; }

        /* Sidebar tweak */
        [data-testid="stSidebar"] {
            background-color: #0f172a;
        }
        [data-testid="stSidebar"] * {
            color: #e2e8f0;
        }
        [data-testid="stSidebar"] .stSelectbox label {
            color: #94a3b8;
        }
    </style>
    """, unsafe_allow_html=True)


def render_header(title: str, subtitle: str):
    st.markdown(f"""
    <div class="main-header">
        <h1>{title}</h1>
        <p>{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)


def render_kpi(label: str, value: str, subtext: str = "", border_color: str = "#3b82f6"):
    st.markdown(f"""
    <div class="metric-card" style="border-top: 4px solid {border_color};">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        {f'<div class="metric-sub">{subtext}</div>' if subtext else ''}
    </div>
    """, unsafe_allow_html=True)


def get_priority_badge(priority: str) -> str:
    p = priority.lower()
    if "critical" in p:
        return f'<span class="badge badge-critical">CRITICAL</span>'
    elif "high" in p:
        return f'<span class="badge badge-high">HIGH</span>'
    elif "med" in p:
        return f'<span class="badge badge-medium">MEDIUM</span>'
    elif "low" in p:
        return f'<span class="badge badge-low">LOW</span>'
    return f'<span class="badge badge-info">{priority.upper()}</span>'


def render_agent_activity_box(log_dict: dict):
    stt = log_dict.get("status", "info")
    css_class = f"agent-log-{stt}"
    icon = "✓" if stt == "success" else ("⚠" if stt == "warning" else ("✕" if stt == "error" else "ℹ"))

    st.markdown(f"""
    <div class="agent-log-card {css_class}">
        <span style="font-weight:700; margin-right:8px;">{icon} {log_dict.get('agent', 'Agent')}</span>
        <span style="color:#64748b; font-size:0.8rem; margin-right:12px;">[{log_dict.get('timestamp', '')}]</span>
        <div style="margin-top:4px; color:#1e293b;">{log_dict.get('action', '')}</div>
    </div>
    """, unsafe_allow_html=True)
