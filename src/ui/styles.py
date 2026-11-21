"""
Custom CSS for SafeSpend AI.
Bold, Modern Indian Fintech Design:
- Dark Navy Canvas (#0A0E1A, #121A2D)
- Vibrant Emerald Green (#00F59B)
- Electric Purple (#8B5CF6)
- Radiant Orange (#F97316)
"""

CUSTOM_CSS = """
<style>
/* Global App Canvas & Background */
.stApp {
    background-color: #0A0E1A;
    color: #F8FAFC;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}

/* Header & Sidebar Styling */
header[data-testid="stHeader"] {
    background-color: rgba(10, 14, 26, 0.85);
    backdrop-filter: blur(12px);
}

section[data-testid="stSidebar"] {
    background-color: #0D1322 !important;
    border-right: 1px solid #1E293B;
}

/* Card Container */
.fintech-card {
    background: linear-gradient(145deg, #121A2D 0%, #0F172A 100%);
    border: 1px solid #1E293B;
    border-radius: 16px;
    padding: 22px;
    margin-bottom: 18px;
    box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.5);
    transition: all 0.25s ease-in-out;
}

.fintech-card:hover {
    border-color: rgba(0, 245, 155, 0.35);
    box-shadow: 0 8px 28px -4px rgba(0, 245, 155, 0.12);
}

/* Hero Safe-to-Spend Card */
.hero-safe-card {
    background: radial-gradient(circle at 100% 0%, rgba(139, 92, 246, 0.18) 0%, transparent 60%),
                radial-gradient(circle at 0% 100%, rgba(0, 245, 155, 0.18) 0%, transparent 60%),
                #121A2D;
    border: 1.5px solid rgba(0, 245, 155, 0.4);
    border-radius: 20px;
    padding: 28px;
    margin-bottom: 24px;
    box-shadow: 0 10px 30px -5px rgba(0, 245, 155, 0.15);
}

/* Survival Mode Warning Card */
.survival-card {
    background: radial-gradient(circle at 50% 50%, rgba(239, 68, 68, 0.2) 0%, #121A2D 100%);
    border: 2px solid #EF4444;
    border-radius: 20px;
    padding: 26px;
    margin-bottom: 24px;
    box-shadow: 0 0 30px rgba(239, 68, 68, 0.3);
    animation: pulse 2s infinite ease-in-out;
}

@keyframes pulse {
    0% { box-shadow: 0 0 15px rgba(239, 68, 68, 0.25); }
    50% { box-shadow: 0 0 35px rgba(239, 68, 68, 0.5); }
    100% { box-shadow: 0 0 15px rgba(239, 68, 68, 0.25); }
}

/* Typography Helpers */
.title-gradient {
    background: linear-gradient(135deg, #00F59B 0%, #38BDF8 50%, #8B5CF6 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 800;
    letter-spacing: -0.5px;
}

.text-muted {
    color: #94A3B8;
    font-size: 0.88rem;
}

.metric-value-huge {
    font-size: 2.8rem;
    font-weight: 800;
    color: #00F59B;
    letter-spacing: -1px;
    line-height: 1.1;
    margin: 8px 0;
}

.metric-value-huge-danger {
    font-size: 2.8rem;
    font-weight: 800;
    color: #EF4444;
    letter-spacing: -1px;
    line-height: 1.1;
    margin: 8px 0;
}

/* Fintech Pills and Badges */
.badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 9999px;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}

.badge-green {
    background: rgba(0, 245, 155, 0.15);
    color: #00F59B;
    border: 1px solid rgba(0, 245, 155, 0.35);
}

.badge-purple {
    background: rgba(139, 92, 246, 0.15);
    color: #C084FC;
    border: 1px solid rgba(139, 92, 246, 0.35);
}

.badge-orange {
    background: rgba(249, 115, 22, 0.15);
    color: #FB923C;
    border: 1px solid rgba(249, 115, 22, 0.35);
}

.badge-red {
    background: rgba(239, 68, 68, 0.2);
    color: #F87171;
    border: 1px solid rgba(239, 68, 68, 0.4);
}

/* Coach Card */
.coach-box {
    background: #141E34;
    border-left: 4px solid #8B5CF6;
    border-radius: 12px;
    padding: 16px 18px;
    margin-bottom: 14px;
}

.coach-box-danger {
    background: #1A1522;
    border-left: 4px solid #EF4444;
    border-radius: 12px;
    padding: 16px 18px;
    margin-bottom: 14px;
}

.coach-box-green {
    background: #102128;
    border-left: 4px solid #00F59B;
    border-radius: 12px;
    padding: 16px 18px;
    margin-bottom: 14px;
}

.coach-box-orange {
    background: #231C1E;
    border-left: 4px solid #F97316;
    border-radius: 12px;
    padding: 16px 18px;
    margin-bottom: 14px;
}

/* Custom Streamlit Tabs Styling */
button[data-baseweb="tab"] {
    background-color: transparent !important;
    color: #94A3B8 !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    border-radius: 8px 8px 0 0 !important;
    padding: 10px 18px !important;
}

button[data-baseweb="tab"][aria-selected="true"] {
    color: #00F59B !important;
    border-bottom: 2px solid #00F59B !important;
}

/* Form input dark styling tweaks */
div[data-baseweb="input"] {
    background-color: #0D1424 !important;
    border-color: #27354E !important;
    border-radius: 10px !important;
}

div[data-baseweb="select"] {
    background-color: #0D1424 !important;
    border-radius: 10px !important;
}

/* Button overrides */
.stButton button {
    background: linear-gradient(135deg, #00F59B 0%, #00C878 100%) !important;
    color: #0A0E1A !important;
    font-weight: 700 !important;
    border-radius: 10px !important;
    border: none !important;
    padding: 8px 20px !important;
    transition: all 0.2s ease !important;
}

.stButton button:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 18px rgba(0, 245, 155, 0.35) !important;
}

/* Secondary Button style for simulation / utility */
.secondary-btn button {
    background: #1E293B !important;
    color: #F8FAFC !important;
    border: 1px solid #334155 !important;
}

/* Dataframe styling */
div[data-testid="stDataFrame"] {
    border: 1px solid #1E293B;
    border-radius: 12px;
    overflow: hidden;
}

/* Conversational Chat UI */
.chat-container {
    display: flex;
    flex-direction: column;
    gap: 16px;
    margin-bottom: 24px;
}

.chat-bubble-user {
    background: linear-gradient(135deg, #1C1938 0%, #171B30 100%);
    border: 1px solid rgba(139, 92, 246, 0.4);
    border-radius: 16px 16px 4px 16px;
    padding: 14px 18px;
    margin-left: 15%;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.3);
}

.chat-bubble-ai {
    background: linear-gradient(135deg, #0F1728 0%, #0D1422 100%);
    border: 1px solid rgba(0, 245, 155, 0.35);
    border-left: 4px solid #00F59B;
    border-radius: 16px 16px 16px 4px;
    padding: 18px 22px;
    margin-right: 8%;
    box-shadow: 0 4px 20px rgba(0, 245, 155, 0.08);
}

.chat-meta {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.75rem;
    font-weight: 600;
    margin-bottom: 6px;
}

.chat-meta-user {
    color: #C084FC;
    justify-content: flex-end;
}

.chat-meta-ai {
    color: #00F59B;
}

.chat-metric-tag {
    display: inline-block;
    background: #090E1A;
    border: 1px solid #1E293B;
    border-radius: 8px;
    padding: 6px 12px;
    margin: 4px 4px 4px 0;
    font-size: 0.82rem;
    color: #F8FAFC;
}

.suggestion-chip {
    display: inline-block;
    background: #141E34;
    border: 1px solid #28354E;
    color: #CBD5E1;
    border-radius: 9999px;
    padding: 6px 14px;
    font-size: 0.8rem;
    cursor: pointer;
    transition: all 0.2s;
    margin: 4px;
}
</style>
"""
