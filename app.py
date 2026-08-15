"""
裁判评分系统 — Streamlit 主程序

裁判通过手机浏览器访问，进行评分操作。
支持答辩组和实操组两类裁判，自动保存评分记录到 JSON，
并支持导出为 Excel 格式。

部署方式：Streamlit Community Cloud
"""

import hashlib
import importlib
import json
import uuid

import pandas as pd
import streamlit as st

# Streamlit Cloud 可能在代码热更新时保留旧的已导入模块。仅在版本不匹配时
# 重载依赖，确保 app.py 与持久化模块来自同一部署版本。
from utils import auth as _auth_module
from utils import data_manager as _data_manager_module
from utils import scoring as _scoring_module

if getattr(_data_manager_module, "MODULE_VERSION", "") != "2026-08-15-admin-delete-v1":
    _scoring_module = importlib.reload(_scoring_module)
    _data_manager_module = importlib.reload(_data_manager_module)
    _auth_module = importlib.reload(_auth_module)

from utils.auth import (
    auto_login_from_token,
    auto_login_from_params,
    is_logged_in,
    get_current_judge,
    render_login_page,
    logout,
)
from utils.scoring import (
    apply_practical_score_overrides,
    get_criteria,
    get_deductions,
    get_groups,
    get_total_score,
    get_veto,
)
from utils.data_manager import (
    ScorePersistenceError,
    init_data_files,
    save_score,
    get_all_scores,
    get_all_judges,
    delete_judges,
    delete_score_records,
    export_records_to_excel,
    export_to_excel,
    export_all_to_excel,
)

# ===================== 页面配置 =====================

st.set_page_config(
    page_title="裁判评分系统",
    page_icon="🏅",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ===================== 初始化 =====================

init_data_files()

# ===================== 主题定制（移动端优化） =====================

st.markdown(
    """
\n<style>\n    /* === \u5168\u5c40\u767d\u5e95 === */\n    .stApp, .stAppViewContainer, .main, .block-container,\n    header, footer, section[data-testid=\"stSidebar\"] {\n        background: #FFFFFF !important;\n    }\n    /* === \u6240\u6709\u6587\u5b57\u6df1\u8272 === */\n    body, p, span, div, li, h1, h2, h3, h4, h5, h6,\n    label, .stTextInput label, .stNumberInput label,\n    .stSelectbox label, .stSelectbox div, .stSelectbox span,\n    .stMarkdown, .stMarkdown p, .stMarkdown div, .stMarkdown span,\n    .stCaption, caption, .stAlert, .stAlert p, .stAlert div,\n    .stDataFrame, .stDataFrame td, .stDataFrame th,\n    [data-testid=\"stMetricValue\"], [data-testid=\"stMetricLabel\"],\n    [data-testid=\"baseButton-secondary\"] {\n        color: #1a1a1a !important;\n    }\n    h1, h2, h3, h4, h5, h6, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {\n        color: #1a1a1a !important;\n    }\n    /* === \u8f93\u5165\u6846 === */\n    .stTextInput input, .stNumberInput input, input, textarea, select {\n        color: #1a1a1a !important;\n        background: #FFFFFF !important;\n        border-color: #b0b0b0 !important;\n    }\n    .stNumberInput button {\n        background: #f0f0f0 !important;\n        color: #1a1a1a !important;\n        border: 1px solid #b0b0b0 !important;\n    }\n    /* === \u6309\u94ae === */\n    .stButton button {\n        font-size: 17px !important;\n        min-height: 48px !important;\n    }\n    /* \u4e3b\u6309\u94ae - \u63d0\u4ea4\u8bc4\u5206 */\n    button[kind=\"primary\"], .stButton button[kind=\"primary\"],\n    button[type=\"primary\"], .stButton button[type=\"primary\"] {\n        background: #4472C4 !important;\n        color: #FFFFFF !important;\n        font-weight: 700 !important;\n        border: 2px solid #2a4e8c !important;\n    }\n    button[kind=\"primary\"]:hover, .stButton button[kind=\"primary\"]:hover {\n        background: #3561a8 !important;\n    }\n    button[kind=\"primary\"] * { color: #FFFFFF !important; }\n    /* \u6b21\u6309\u94ae - \u5207\u6362 */\n    button:not([kind=\"primary\"]), .stButton button:not([kind=\"primary\"]) {\n        background: #f0f2f6 !important;\n        color: #1a1a1a !important;\n        border: 1px solid #c0c0c0 !important;\n    }\n    button:not([kind=\"primary\"]):hover {\n        background: #e0e2e6 !important;\n    }\n    /* === Tab === */\n    button[data-testid=\"stTab\"], button[data-testid=\"stTab\"] span {\n        color: #1a1a1a !important;\n    }\n    button[data-testid=\"stTab\"][aria-selected=\"true\"] {\n        border-bottom-color: #4472C4 !important;\n    }\n    /* === selectbox \u4e0b\u62c9\u6846 === */\n    .stSelectbox, .stSelectbox div, .stSelectbox span,\n    .stSelectbox [data-baseweb=\"select\"],\n    .stSelectbox [data-baseweb=\"select\"] div,\n    .stSelectbox [data-baseweb=\"select\"] span {\n        background: #FFFFFF !important;\n        color: #1a1a1a !important;\n    }\n    .stSelectbox svg, [data-baseweb=\"select\"] svg {\n        fill: #1a1a1a !important;\n        color: #1a1a1a !important;\n    }\n    /* \u4e0b\u62c9\u83dc\u5355\u5f39\u51fa */\n    ul[role=\"listbox\"], li[role=\"option\"],\n    div[data-baseweb=\"popover\"], div[data-baseweb=\"popover\"] *,\n    div[data-testid=\"stSelectbox\"] div[role=\"listbox\"],\n    div[data-testid=\"stSelectbox\"] li[role=\"option\"] {\n        background: #FFFFFF !important;\n        color: #1a1a1a !important;\n    }\n    li[role=\"option\"]:hover, div[role=\"option\"]:hover,\n    li[role=\"option\"][aria-selected=\"true\"] {\n        background: #e3ecfa !important;\n        color: #1a1a1a !important;\n    }\n    /* \u4e0b\u62c9\u83dc\u5355\u9009\u9879 - \u5185\u5c42\u5bb9\u5668\u5f3a\u5316 */\n    div[data-baseweb=\"popover\"] {\n        background-color: #FFFFFF !important;\n        border: 1px solid #c0c0c0 !important;\n    }\n    div[data-baseweb=\"popover\"] ul,\n    div[data-baseweb=\"popover\"] li,\n    div[data-baseweb=\"popover\"] div[role=\"option\"],\n    div[data-baseweb=\"popover\"] span {\n        background: #FFFFFF !important;\n        color: #1a1a1a !important;\n    }\n    div[data-baseweb=\"popover\"] li[role=\"option\"]:hover,\n    div[data-baseweb=\"popover\"] div[role=\"option\"]:hover {\n        background: #e3ecfa !important;\n        color: #1a1a1a !important;\n    }\n    /* === radio \u9009\u94ae === */\n    div[role=\"radiogroup\"] { gap: 6px !important; flex-wrap: wrap !important; }\n    div[role=\"radiogroup\"] label {\n        font-size: 18px !important; min-height: 44px !important;\n        min-width: 44px !important; padding: 8px 18px !important;\n        border-radius: 8px !important; border: 2px solid #c0c0c0 !important;\n        background: #f0f0f0 !important; display: flex !important;\n        align-items: center !important; justify-content: center !important;\n        margin: 2px !important; cursor: pointer !important;\n        color: #1a1a1a !important;\n    }\n    div[role=\"radiogroup\"] label:hover {\n        border-color: #4472C4 !important; background: #e3ecfa !important;\n    }\n    div[role=\"radiogroup\"] label[data-checked=\"true\"] {\n        border-color: #4472C4 !important; background: #4472C4 !important;\n        color: #FFFFFF !important;\n    }\n    div[role=\"radiogroup\"] input { display: none !important; }\n    /* === tooltip \u60ac\u505c\u63d0\u793a === */\n    div[role=\"tooltip\"], [data-testid=\"tooltip\"],\n    div[data-baseweb=\"tooltip\"], div[data-baseweb=\"tooltip\"] *,\n    .stTooltip, .stTooltip div, .stTooltip span, .stTooltip p {\n        background: #333333 !important;\n        color: #FFFFFF !important;\n        border: 1px solid #555555 !important;\n        border-radius: 6px !important;\n        box-shadow: 2px 2px 8px rgba(0,0,0,0.3) !important;\n        font-size: 14px !important;\n        padding: 8px 12px !important;\n        z-index: 9999 !important;\n    }\n    /* help \u56fe\u6807 - \u84dd\u8272\u9ad8\u4eae */\n    .stTooltipIcon, .stTooltipIcon svg,\n    [data-testid=\"stTooltipIcon\"],\n    [data-testid=\"stTooltipIcon\"] svg {\n        fill: #4472C4 !important;\n        color: #4472C4 !important;\n        opacity: 1 !important;\n        background: transparent !important;\n    }\n    /* === \u8bc4\u5206\u5361 === */\n    .score-card {\n        background: #f8f9fa; border-radius: 12px;\n        padding: 18px 18px 8px 18px; margin-bottom: 14px;\n        border: 1px solid #d0d0d0;\n    }\n    .score-card .criterion-name {\n        font-size: 18px; font-weight: 700; color: #1a1a1a !important;\n        margin-bottom: 4px;\n    }\n    .score-card .criterion-desc {\n        font-size: 15px; color: #333333 !important; line-height: 1.5;\n        margin-bottom: 10px;\n    }\n    .score-card .criterion-range {\n        font-size: 14px; color: #e67e22 !important; font-weight: 600;\n        margin-bottom: 8px;\n    }\n    /* === \u6a21\u5757\u6807\u9898 === */\n    .module-title {\n        font-size: 17px; font-weight: 700; color: #FFFFFF !important;\n        margin: 16px 0 10px 0; padding: 10px 14px; border-radius: 6px;\n        background: #4472C4;\n    }\n    /* === \u88c1\u5224\u4fe1\u606f === */\n    .judge-info-bar {\n        background: #e8f4f8; border-radius: 10px; padding: 10px 15px;\n        margin-bottom: 15px; border-left: 4px solid #2196F3;\n        color: #1a1a1a !important;\n    }\n    .judge-info-bar strong, .judge-info-bar span { color: #1a1a1a !important; }\n    /* === \u6307\u6807 === */\n    [data-testid=\"stMetricValue\"] { font-size: 24px !important; color: #1a1a1a !important; }\n    [data-testid=\"stMetricLabel\"] { font-size: 15px !important; color: #1a1a1a !important; }\n    /* === \u8868\u683c === */\n    .stDataFrame, .stDataFrame td, .stDataFrame th {\n        font-size: 15px !important; color: #1a1a1a !important; background: #FFFFFF !important;\n    }\n    .stDataFrame th { background: #f5f5f5 !important; }\n    /* === \u603b\u5206 === */\n    .total-score-box {\n        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);\n        color: white; border-radius: 15px; padding: 15px;\n        text-align: center; margin: 15px 0;\n    }\n    .total-score-box .score-value { font-size: 36px; font-weight: bold; color: white !important; }\n    .total-score-box .score-label { font-size: 14px; opacity: 0.9; color: white !important; }\n    /* === caption === */\n    .stCaption, .caption, .stMarkdown small { color: #555555 !important; }\n    hr { border-color: #e0e0e0 !important; }\n    /* === \u63d0\u793a\u6846 === */\n    div[data-testid=\"stAlertInfo\"] {\n        background: #e3f2fd !important; border: 1px solid #bbdefb !important;\n        color: #1a1a1a !important;\n    }\n    div[data-testid=\"stAlertError\"] {\n        background: #ffebee !important; border: 1px solid #ffcdd2 !important;\n        color: #b71c1c !important;\n    }\n    div[data-testid=\"stAlertWarning\"] {\n        background: #fff8e1 !important; border: 1px solid #ffe082 !important;\n        color: #1a1a1a !important;\n    }\n    div[data-testid=\"stAlertSuccess\"] {\n        background: #e8f5e9 !important; border: 1px solid #c8e6c9 !important;\n        color: #1a1a1a !important;\n    }\n    /* === selectbox 下拉选项 - 全力覆盖 === */
    div[data-baseweb=\"popover\"] li[role=\"option\"],
    div[data-baseweb=\"popover\"] [role=\"option\"],
    [role=\"listbox\"] [role=\"option\"],
    ul[role=\"listbox\"] li {
        background-color: #FFFFFF !important;
        color: #1a1a1a !important;
    }
    div[data-baseweb=\"popover\"] li[role=\"option\"]:hover,
    div[data-baseweb=\"popover\"] [role=\"option\"]:hover,
    [role=\"listbox\"] [role=\"option\"]:hover,
    ul[role=\"listbox\"] li:hover {
        background-color: #e3ecfa !important;
        color: #1a1a1a !important;
    }
    div[data-baseweb=\"popover\"],
    [role=\"listbox\"],
    ul[role=\"listbox\"] {
        background-color: #FFFFFF !important;
        border: 1px solid #c0c0c0 !important;
    }
    /* === checkbox 问号提示弹窗 - 白字深背景 === */
    .stCheckbox div[role=\"tooltip\"],
    .stCheckbox [data-testid=\"tooltip\"],
    .stCheckbox [data-baseweb=\"tooltip\"],
    .stCheckbox [data-baseweb=\"tooltip\"] *,
    [data-testid=\"stWidgetLabel\"] [role=\"tooltip\"],
    [data-testid=\"stWidgetLabel\"] [data-baseweb=\"tooltip\"],
    [data-testid=\"stWidgetLabel\"] [data-baseweb=\"tooltip\"] *,
    label [role=\"tooltip\"],
    label [data-baseweb=\"tooltip\"],
    label [data-baseweb=\"tooltip\"] * {
        background: #333333 !important;
        color: #FFFFFF !important;
    }
    /* 问号图标本身 */
    .stCheckbox .stTooltipIcon,
    .stCheckbox [data-testid=\"stTooltipIcon\"],
    .stCheckbox [data-testid=\"stTooltipIcon\"] svg {
        fill: #4472C4 !important;
        color: #4472C4 !important;
        background: transparent !important;
    }

    /* === tooltip 全局强制覆盖 === */
    /* 所有 tooltip 弹窗，包括 checkbox 和其他元素的悬停提示 */
    div[data-baseweb=\"tooltip\"],
    div[role=\"tooltip\"],
    [data-testid=\"tooltip\"] {
        background: #333333 !important;
        background-color: #333333 !important;
    }
    div[data-baseweb=\"tooltip\"] *,
    div[role=\"tooltip\"] *,
    [data-testid=\"tooltip\"] * {
        color: #FFFFFF !important;
        fill: #FFFFFF !important;
        background: transparent !important;
        font-size: 14px !important;
    }
    /* 弹窗内的 div 和 span 可能被 global 覆盖 */
    [data-baseweb=\"tooltip\"] div,
    [data-baseweb=\"tooltip\"] span,
    [data-baseweb=\"tooltip\"] p,
    [role=\"tooltip\"] div,
    [role=\"tooltip\"] span,
    [role=\"tooltip\"] p,
    [data-testid=\"tooltip\"] div,
    [data-testid=\"tooltip\"] span,
    [data-testid=\"tooltip\"] p {
        color: #FFFFFF !important;
        background: transparent !important;
    }
    [data-baseweb=\"tooltip\"] [style*=\"arrow\"],
    [data-baseweb=\"tooltip\"] [style*=\"Arrow\"] {
        background-color: #333333 !important;
    }

    /* === tooltip 弹窗强制覆盖 === */
    /* 这里要覆盖上面的下拉菜单规则 */
    /* Streamlit checkbox的help tooltip弹窗是用baseweb Popover渲染的 */
    [data-baseweb=\"popover\"][role=\"tooltip\"],
    [data-baseweb=\"popover\"][role=\"tooltip\"] div,
    [data-baseweb=\"popover\"][role=\"tooltip\"] span,
    [data-baseweb=\"popover\"][role=\"tooltip\"] p,
    [data-baseweb=\"popover\"][aria-label*=\"tooltip\"],
    [data-baseweb=\"popover\"].tooltip,
    div[data-baseweb=\"tooltip\"],
    div[data-baseweb=\"tooltip\"] div,
    div[data-baseweb=\"tooltip\"] span,
    div[data-baseweb=\"tooltip\"] p {
        background: #333333 !important;
        background-color: #333333 !important;
        color: #FFFFFF !important;
    }
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
    <style>
    /* 当前评分页：紧凑的表格式行 */
    .score-row-name {
        min-height: 48px;
        display: flex;
        align-items: center;
        font-size: 17px;
        font-weight: 700;
        line-height: 1.35;
        color: #1a1a1a !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.score-row-name) {
        border: 1px solid #cfd6e4 !important;
        border-radius: 4px !important;
        margin-bottom: -1px !important;
        background: #FFFFFF !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.score-row-name) {
        align-items: center !important;
        flex-wrap: nowrap !important;
    }
    .submodule-title {
        font-size: 16px;
        font-weight: 700;
        color: #2a4e8c !important;
        margin: 14px 0 6px 0;
        padding: 7px 10px;
        border-left: 4px solid #4472C4;
        background: #eef3fb;
    }
    /* 手机端：评分项名称与选项上下排列，按钮在屏幕宽度内自动换行。 */
    @media (max-width: 640px) {
        html, body,
        .stApp,
        .stAppViewContainer,
        [data-testid="stAppViewContainer"],
        [data-testid="stMain"],
        .main,
        .block-container {
            max-width: 100% !important;
            overflow-x: hidden !important;
        }

        .block-container {
            width: 100% !important;
            padding: 0.75rem 0.65rem 3rem !important;
        }

        h1, .stMarkdown h1 { font-size: 1.55rem !important; }
        h2, .stMarkdown h2 { font-size: 1.3rem !important; }
        h3, .stMarkdown h3 { font-size: 1.12rem !important; }
        h4, .stMarkdown h4 { font-size: 1rem !important; }

        div[data-testid="stHorizontalBlock"] {
            max-width: 100% !important;
            min-width: 0 !important;
            gap: 0.35rem !important;
        }

        div[data-testid="stColumn"] {
            min-width: 0 !important;
        }

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.score-row-name) {
            width: 100% !important;
            max-width: 100% !important;
            overflow: hidden !important;
        }

        div[data-testid="stHorizontalBlock"]:has(.score-row-name) {
            flex-direction: column !important;
            flex-wrap: wrap !important;
            align-items: stretch !important;
            gap: 0.2rem !important;
            width: 100% !important;
        }

        div[data-testid="stHorizontalBlock"]:has(.score-row-name)
        > div[data-testid="stColumn"] {
            flex: 0 0 auto !important;
            min-height: 0 !important;
            height: auto !important;
            overflow: visible !important;
        }

        div[data-testid="stHorizontalBlock"]:has(.score-row-name)
        > div[data-testid="stColumn"]
        > div[data-testid="stVerticalBlockBorderWrapper"] {
            height: auto !important;
            min-height: 0 !important;
            overflow: visible !important;
        }

        /* Streamlit 列元素保留了桌面端的固定高度，窄屏改为内容自适应。 */
        div[data-testid="stHorizontalBlock"]:has(.score-row-name)
        [data-testid="stElementContainer"],
        div[data-testid="stHorizontalBlock"]:has(.score-row-name)
        [data-testid="stVerticalBlock"] {
            height: auto !important;
            min-height: 0 !important;
        }


        div[data-testid="stHorizontalBlock"]:has(.score-row-name)
        > div[data-testid="stColumn"]:has(.score-row-name),
        div[data-testid="stHorizontalBlock"]:has(.score-row-name)
        > div[data-testid="stColumn"]:has(.score-row-name)
        > div[data-testid="stVerticalBlockBorderWrapper"],
        div[data-testid="stHorizontalBlock"]:has(.score-row-name)
        > div[data-testid="stColumn"]:has(.score-row-name)
        [data-testid="stVerticalBlock"],
        div[data-testid="stHorizontalBlock"]:has(.score-row-name)
        > div[data-testid="stColumn"]:has(.score-row-name)
        [data-testid="stElementContainer"] {
            min-height: 24px !important;
        }

        .score-row-name {
            min-height: 0;
            padding: 0.1rem 0;
            font-size: 14px;
            line-height: 1.3;
            overflow-wrap: anywhere;
        }

        .module-title {
            margin: 0.75rem 0 0.35rem;
            padding: 0.45rem 0.6rem;
            font-size: 14px;
            line-height: 1.3;
        }

        .submodule-title {
            margin: 0.55rem 0 0.3rem;
            padding: 0.35rem 0.5rem;
            font-size: 13px;
            line-height: 1.3;
        }

        div[role="radiogroup"] {
            display: flex !important;
            flex-wrap: wrap !important;
            width: 100% !important;
            max-width: 100% !important;
            min-width: 0 !important;
            gap: 4px !important;
        }

        div[role="radiogroup"] label {
            flex: 0 1 auto !important;
            max-width: 100% !important;
            min-width: 0 !important;
            min-height: 36px !important;
            margin: 0 !important;
            padding: 5px 8px !important;
            border-width: 1px !important;
            border-radius: 6px !important;
            font-size: 13px !important;
            line-height: 1.15 !important;
            white-space: normal !important;
            overflow-wrap: anywhere !important;
        }

        div[role="radiogroup"] label p,
        div[role="radiogroup"] label span {
            max-width: 100% !important;
            margin: 0 !important;
            font-size: inherit !important;
            line-height: inherit !important;
            white-space: normal !important;
            overflow-wrap: anywhere !important;
        }

        .stButton button {
            min-height: 40px !important;
            padding: 0.35rem 0.6rem !important;
            font-size: 14px !important;
        }

        button[data-testid="stTab"] {
            min-width: 0 !important;
            padding: 0.4rem 0.45rem !important;
        }

        button[data-testid="stTab"] p,
        button[data-testid="stTab"] span {
            font-size: 13px !important;
            white-space: nowrap !important;
        }

        .judge-info-bar {
            padding: 0.45rem 0.55rem;
            margin-bottom: 0.35rem;
            font-size: 13px;
            overflow-wrap: anywhere;
        }

        .total-score-box {
            padding: 0.65rem;
            margin: 0.65rem 0;
        }

        .total-score-box .score-value {
            font-size: 28px;
        }
    }

    @media (max-width: 380px) {
        .block-container {
            padding-right: 0.45rem !important;
            padding-left: 0.45rem !important;
        }

        div[role="radiogroup"] label {
            min-height: 34px !important;
            padding: 4px 6px !important;
            font-size: 12px !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ===================== 页面路由 =====================


def main():
    # 尝试从 URL 自动登录（优先用 token 查询文件，失败则从参数直接恢复）
    if not is_logged_in():
        if not auto_login_from_token():
            auto_login_from_params()

    # ===== 未登录 → 显示登录页 =====
    if not is_logged_in():
        render_login_page()
        return

    # ===== 已登录 → 进入评分系统 =====
    judge = get_current_judge()

    # --- 顶部导航栏 ---
    col_logo, col_info, col_btn = st.columns([1, 3, 1])
    with col_logo:
        st.markdown("🏅")
    with col_info:
        st.markdown(
            f"<div class='judge-info-bar'>"
            f"<strong>{judge['name']}</strong> 裁判 "
            f"<span style='background:#2196F3;color:white;padding:2px 8px;border-radius:10px;font-size:12px;'>{judge['group']}</span>"
            f"<br><span style='font-size:12px;color:#666;'>编号: {judge['judge_id']}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )
    with col_btn:
        if st.button("🔄 切换", help="切换裁判账号"):
            logout()

    st.markdown("---")

    # --- 页面 Tab ---
    tab1, tab2, tab3 = st.tabs(["📝 评分", "📊 记录", "⚙️ 管理"])

    # ===== Tab 1: 评分 =====
    with tab1:
        render_scoring_page(judge)

    # ===== Tab 2: 历史记录 =====
    with tab2:
        render_history_page(judge)

    # ===== Tab 3: 管理 =====
    with tab3:
        render_admin_page()


# ===================== 评分页面 =====================


def _render_score_buttons(
    criterion_name: str,
    criterion_info: dict,
    submit_round: int,
):
    """渲染评分按钮，并返回按钮对应的实际分值。"""
    max_score = criterion_info["max"]
    options = criterion_info.get("options", list(range(max_score + 1)))
    widget_key = f"score_{criterion_name}_{submit_round}"

    if options and isinstance(options[0], dict):
        option_labels = [option["label"] for option in options]
        label_to_value = {
            option["label"]: option["value"] for option in options
        }
        zero_index = next(
            (
                index
                for index, option in enumerate(options)
                if option["value"] == 0
            ),
            0,
        )
        selected_label = st.radio(
            label=criterion_name,
            options=option_labels,
            index=zero_index,
            horizontal=True,
            key=widget_key,
            label_visibility="collapsed",
        )
        return label_to_value[selected_label]

    option_values = list(options)
    zero_index = option_values.index(0) if 0 in option_values else 0
    return st.radio(
        label=criterion_name,
        options=option_values,
        index=zero_index,
        format_func=lambda value: f"{value:g}分",
        horizontal=True,
        key=widget_key,
        label_visibility="collapsed",
    )


def render_scoring_page(judge: dict):
    """渲染评分表单"""
    group = judge["group"]
    criteria = get_criteria(group)
    total_max = get_total_score(group)
    deductions_def = get_deductions(group)
    veto_def = get_veto(group)

    st.markdown(f"### 📝 {group}评分")

    # 提交计数器：每次提交后 +1，使输入框重新从 0 开始
    if "submit_round" not in st.session_state:
        st.session_state.submit_round = 0
    submit_round = st.session_state.submit_round

    # 选手编号输入
    contestant_id = st.text_input(
        "🎯 被评分选手编号/姓名",
        placeholder="请输入选手编号或姓名",
        key=f"contestant_id_{submit_round}",
    )

    contestant_group = st.selectbox(
        "👥 选手组别",
        options=["本科研究生组", "高职高专组", "国际留学生组"],
        index=None,
        placeholder="请选择选手组别",
        key=f"contestant_group_{submit_round}",
    )

    # 实操组必须保留并记录评分表中的完成时间 T
    duration = ""
    if group == "实操组":
        with st.container(border=True):
            name_col, value_col = st.columns([2, 5])
            with name_col:
                st.markdown(
                    "<div class='score-row-name'>完成时间 T</div>",
                    unsafe_allow_html=True,
                )
            with value_col:
                duration = st.text_input(
                    label="完成时间 T",
                    key=f"duration_{submit_round}",
                    label_visibility="collapsed",
                )

    # 评分项
    scores = {}
    deductions_applied = {}
    deduction_total = 0
    score_zero_items = []
    score_override_notes = []
    st.markdown("#### 评分项")

    if group == "实操组":
        # 实操组：表格式选钮评分 + 扣分项 + 否决项
        modules = {}
        for name, info in criteria.items():
            module = info.get("module", "其他")
            modules.setdefault(module, []).append((name, info))

        for module_name, items in modules.items():
            st.markdown(
                f"<div class='module-title'>{module_name}</div>",
                unsafe_allow_html=True,
            )
            last_submodule = None
            for criterion_name, criterion_info in items:
                submodule = criterion_info.get("submodule")
                if submodule and submodule != last_submodule:
                    st.markdown(
                        f"<div class='submodule-title'>{submodule}</div>",
                        unsafe_allow_html=True,
                    )
                last_submodule = submodule
                display_name = criterion_info.get("display_name", criterion_name)

                with st.container(border=True):
                    name_col, score_col = st.columns([2, 5])
                    with name_col:
                        st.markdown(
                            f"<div class='score-row-name'>{display_name}</div>",
                            unsafe_allow_html=True,
                        )
                    with score_col:
                        scores[criterion_name] = _render_score_buttons(
                            criterion_name,
                            criterion_info,
                            submit_round,
                        )

        # 扣分项：次数类自动乘以单次扣分，规则类使用按钮选择
        auxiliary_task_card = ""
        assembly_intervened = False

        if deductions_def:
            st.markdown("---")
            st.markdown("#### ⚠️ 扣分项")
            for ded_name, ded_info in deductions_def.items():
                deduct_val = ded_info["deduct"]
                mode = ded_info.get("mode", "per_count")

                if mode == "per_count":
                    with st.container(border=True):
                        name_col, count_col, total_col = st.columns([3, 2, 2])
                        with name_col:
                            st.markdown(
                                f"<div class='score-row-name'>{ded_name}（次数）</div>",
                                unsafe_allow_html=True,
                            )
                        with count_col:
                            count = st.number_input(
                                label=f"{ded_name}次数",
                                min_value=0,
                                max_value=100,
                                value=0,
                                step=1,
                                key=f"ded_count_{ded_name}_{submit_round}",
                                label_visibility="collapsed",
                            )
                        with total_col:
                            penalty = count * deduct_val
                            st.markdown(
                                f"<div class='score-row-name'>扣 {penalty} 分</div>",
                                unsafe_allow_html=True,
                            )
                    if count > 0:
                        deductions_applied[ded_name] = penalty

                elif mode == "task_card_override":
                    with st.container(border=True):
                        name_col, value_col = st.columns([3, 4])
                        with name_col:
                            st.markdown(
                                f"<div class='score-row-name'>{ded_name}</div>",
                                unsafe_allow_html=True,
                            )
                        with value_col:
                            auxiliary_task_card = st.radio(
                                label=ded_name,
                                options=["未发生", "任务卡1", "任务卡2", "任务卡1及任务卡2"],
                                index=0,
                                horizontal=True,
                                key=f"ded_choice_{ded_name}_{submit_round}",
                                label_visibility="collapsed",
                            )
                    if auxiliary_task_card != "未发生":
                        deductions_applied[ded_name] = auxiliary_task_card

                elif mode == "assembly_override":
                    with st.container(border=True):
                        name_col, value_col = st.columns([3, 4])
                        with name_col:
                            st.markdown(
                                f"<div class='score-row-name'>{ded_name}</div>",
                                unsafe_allow_html=True,
                            )
                        with value_col:
                            assembly_choice = st.radio(
                                label=ded_name,
                                options=["未介入", "介入"],
                                index=0,
                                horizontal=True,
                                key=f"ded_choice_{ded_name}_{submit_round}",
                                label_visibility="collapsed",
                            )
                    assembly_intervened = assembly_choice == "介入"
                    if assembly_intervened:
                        deductions_applied[ded_name] = "介入"

                elif mode == "binary_deduct":
                    with st.container(border=True):
                        name_col, value_col = st.columns([3, 4])
                        with name_col:
                            st.markdown(
                                f"<div class='score-row-name'>{ded_name}</div>",
                                unsafe_allow_html=True,
                            )
                        with value_col:
                            binary_choice = st.radio(
                                label=ded_name,
                                options=["未使用", f"使用（扣{deduct_val}分）"],
                                index=0,
                                horizontal=True,
                                key=f"ded_choice_{ded_name}_{submit_round}",
                                label_visibility="collapsed",
                            )
                    if binary_choice != "未使用":
                        deductions_applied[ded_name] = deduct_val

                elif mode == "score_zero":
                    with st.container(border=True):
                        name_col, value_col = st.columns([3, 4])
                        with name_col:
                            st.markdown(
                                f"<div class='score-row-name'>{ded_name}</div>",
                                unsafe_allow_html=True,
                            )
                        with value_col:
                            zero_choice = st.radio(
                                label=ded_name,
                                options=["否", "是（总分记0分）"],
                                index=0,
                                horizontal=True,
                                key=f"ded_choice_{ded_name}_{submit_round}",
                                label_visibility="collapsed",
                            )
                    if zero_choice != "否":
                        deductions_applied[ded_name] = "总分记0分"
                        score_zero_items.append(ded_name)

            scores, score_override_notes = apply_practical_score_overrides(
                scores,
                auxiliary_task_card=auxiliary_task_card,
                assembly_intervened=assembly_intervened,
            )
            deduction_total = sum(
                value
                for value in deductions_applied.values()
                if isinstance(value, (int, float))
            )
            if score_override_notes:
                st.warning("自动归零：" + "；".join(score_override_notes))
            if deduction_total > 0:
                st.warning(f"扣分合计：{deduction_total} 分")

    else:
        # 答辩组：表格式按钮评分，列出 0 至满分的全部分值
        st.markdown(
            "<div class='module-title'>答辩评分（100分）</div>",
            unsafe_allow_html=True,
        )
        for criterion_name, criterion_info in criteria.items():
            with st.container(border=True):
                name_col, score_col = st.columns([2, 5])
                with name_col:
                    st.markdown(
                        f"<div class='score-row-name'>{criterion_name}</div>",
                        unsafe_allow_html=True,
                    )
                with score_col:
                    scores[criterion_name] = _render_score_buttons(
                        criterion_name,
                        criterion_info,
                        submit_round,
                    )

    # 答辩组没有扣分项
    if group == "答辩组":
        deductions_applied = {}
        deduction_total = 0

    # === 否决项（勾选后总分归零） ===
    veto_triggered_items = []
    if veto_def:
        for veto_name in veto_def:
            checked = st.checkbox(
                f"🚨 **{veto_name}**",
                key=f"veto_{veto_name}_{submit_round}",
            )
            if checked:
                veto_triggered_items.append(veto_name)

    veto_triggered = bool(veto_triggered_items)
    score_zero_triggered = bool(score_zero_items)

    # 实时总分（已应用强制归零、扣分和总分归零规则）
    raw_total = sum(scores.values())
    if veto_triggered or score_zero_triggered:
        final_total = 0
    else:
        final_total = max(0, raw_total - deduction_total)

    if veto_triggered or score_zero_triggered:
        zero_reasons = veto_triggered_items + score_zero_items
        reason_text = "、".join(zero_reasons)
        st.markdown(
            f"<div style='background:#f8d7da;border:2px solid #dc3545;border-radius:15px;padding:20px;text-align:center;margin:15px 0;'>"
            f"<div style='font-size:18px;font-weight:bold;color:#dc3545;'>🚫 总分归零项已触发</div>"
            f"<div style='font-size:36px;font-weight:bold;color:#dc3545;margin:10px 0;'>0 / {total_max}</div>"
            f"<div style='font-size:14px;color:#666;'>{reason_text}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
    elif deductions_def:
        st.markdown(
            f"<div class='total-score-box'>"
            f"<div class='score-label'>得分项合计</div>"
            f"<div class='score-value'>{raw_total} / {total_max}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
        if deduction_total > 0:
            st.markdown(
                f"<div style='background:#fff3cd;border-radius:10px;padding:10px;text-align:center;margin:10px 0;'>"
                f"<div style='font-size:14px;'>扣分：{deduction_total} 分</div>"
                f"<div style='font-size:24px;font-weight:bold;color:#dc3545;'>最终得分：{final_total} / {total_max}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            f"<div class='total-score-box'>"
            f"<div class='score-label'>当前总分</div>"
            f"<div class='score-value'>{raw_total} / {total_max}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    # 提交按钮
    col_submit, _ = st.columns([2, 1])
    with col_submit:
        submitted = st.button(
            "✅ 提交评分",
            type="primary",
            use_container_width=True,
            disabled=not contestant_id.strip() or not contestant_group,
        )

    if submitted:
        if not contestant_id or not contestant_id.strip():
            st.error("请输入被评分选手的编号或姓名")
        elif not contestant_group:
            st.error("请选择选手组别")
        elif group == "实操组" and not duration.strip():
            st.error("请输入完成时间 T")
        else:
            submission_payload = {
                "judge_id": judge["judge_id"],
                "judge_group": group,
                "contestant_id": contestant_id.strip(),
                "contestant_group": contestant_group,
                "scores": scores,
                "deductions": deductions_applied,
                "final_score": final_total,
                "veto_items": veto_triggered_items,
                "score_zero_items": score_zero_items,
                "score_overrides": score_override_notes,
                "duration": duration.strip() if group == "实操组" else "",
            }
            submission_fingerprint = hashlib.sha256(
                json.dumps(
                    submission_payload,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            ).hexdigest()
            pending_submission = st.session_state.get("pending_score_submission")
            if (
                not pending_submission
                or pending_submission.get("fingerprint") != submission_fingerprint
            ):
                pending_submission = {
                    "fingerprint": submission_fingerprint,
                    "record_id": uuid.uuid4().hex,
                }
                st.session_state.pending_score_submission = pending_submission

            try:
                record = save_score(
                    judge,
                    contestant_id.strip(),
                    scores,
                    deductions=deductions_applied if deductions_applied else None,
                    final_score=final_total,
                    veto_triggered=veto_triggered,
                    veto_items=veto_triggered_items if veto_triggered_items else None,
                    score_zero_triggered=score_zero_triggered,
                    score_zero_items=score_zero_items if score_zero_items else None,
                    score_overrides=score_override_notes if score_override_notes else None,
                    duration=duration.strip() if group == "实操组" else None,
                    record_id=pending_submission["record_id"],
                    contestant_group=contestant_group,
                )
            except ScorePersistenceError as exc:
                st.error(f"❌ {exc}")
            else:
                st.session_state.pop("pending_score_submission", None)
                st.success(
                    f"✅ {judge['name']} 裁判 → 选手 {record['contestant_id']} "
                    f"得分 {record['total_score']}/{record['total_max']}，云端已确认保存！"
                )
                st.session_state.submit_round += 1
                st.rerun()


# ===================== 历史记录页面 =====================


def render_history_page(judge: dict):
    """渲染历史评分记录"""
    group = judge["group"]
    records = get_all_scores(group, refresh_remote=True)

    st.markdown(f"### 📊 {group}评分记录")

    # 当前裁判的记录
    my_records = [r for r in records if r["judge_id"] == judge["judge_id"]]

    col_all, col_mine = st.columns(2)
    with col_all:
        st.metric("总评分次数", len(records))
    with col_mine:
        st.metric("我的评分次数", len(my_records))

    if not my_records:
        st.info("您还没有评分记录，请前往评分页进行评分。")
        return

    # 显示评分记录表格
    criteria = get_criteria(group)
    score_headers = list(criteria.keys())
    has_deductions = any(r.get("deductions") for r in my_records)
    has_duration = any(r.get("duration") for r in my_records)
    if has_duration:
        time_header = ["选手编号", "选手组别", "用时"] + score_headers
    else:
        time_header = ["选手编号", "选手组别"] + score_headers
    if has_deductions:
        headers = time_header + ["原始分", "扣分", "最终得分", "评分时间"]
    else:
        headers = time_header + ["总分", "评分时间"]

    table_data = []
    for r in reversed(my_records):  # 最新的在前
        row = [r["contestant_id"], r.get("contestant_group", "")]
        if has_duration:
            row.append(r.get("duration", ""))
        for c in score_headers:
            row.append(str(r["scores"].get(c, 0)))
        if has_deductions:
            raw = r.get("raw_score", r["total_score"])
            deduct = r.get("deduction_total", 0)
            row.append(str(raw))
            row.append(str(deduct) if deduct else "0")
            row.append(f"{r['total_score']}/{r['total_max']}")
        else:
            row.append(f"{r['total_score']}/{r['total_max']}")
        row.append(r["timestamp"])
        table_data.append(row)

    st.dataframe(
        table_data,
        column_config={
            c: st.column_config.TextColumn(c) for c in headers
        },
        hide_index=True,
        use_container_width=True,
    )


# ===================== 管理页面 =====================


def _judge_identity(name, judge_id) -> tuple:
    return (str(name or "").strip(), str(judge_id or "").strip())


def _summarize_judge_records(records_by_group: dict) -> list:
    """按裁判姓名+编号聚合评分记录，跨选手编号只显示一行。"""
    summaries = {}
    for group, records in (records_by_group or {}).items():
        for record in records or []:
            key = _judge_identity(
                record.get("judge_name", ""),
                record.get("judge_id", ""),
            )
            summary = summaries.setdefault(
                key,
                {
                    "judge_name": key[0],
                    "judge_id": key[1],
                    "groups": set(),
                    "records_by_group": {},
                    "times": [],
                },
            )
            summary["groups"].add(group)
            summary["records_by_group"].setdefault(group, []).append(record)
            record_time = record.get("timestamp") or record.get("saved_at_utc") or ""
            if record_time:
                summary["times"].append(str(record_time))

    result = []
    for summary in summaries.values():
        summary["groups"] = sorted(summary["groups"])
        summary["record_count"] = sum(
            len(records) for records in summary["records_by_group"].values()
        )
        ordered_times = sorted(summary.pop("times"))
        summary["first_time"] = ordered_times[0] if ordered_times else ""
        summary["last_time"] = ordered_times[-1] if ordered_times else ""
        result.append(summary)
    return sorted(
        result,
        key=lambda item: (item["judge_name"], item["judge_id"]),
    )


def render_admin_page():
    """渲染管理页面（导出 Excel 等）"""
    st.markdown("### ⚙️ 数据管理")

    # 简单的访问控制
    if "admin_verified" not in st.session_state:
        st.session_state.admin_verified = False

    if not st.session_state.admin_verified:
        password = st.text_input(
            "🔐 请输入管理密码",
            type="password",
            key="admin_pwd",
        )
        if st.button("验证", use_container_width=True):
            if password == "zpds2026":
                st.session_state.admin_verified = True
                st.rerun()
            else:
                st.error("密码错误")
        return

    # 验证通过后显示管理功能
    st.success("✅ 已通过管理验证")
    admin_notice = st.session_state.pop("admin_notice", None)
    admin_warning = st.session_state.pop("admin_warning", None)
    if admin_notice:
        st.success(admin_notice)
    if admin_warning:
        st.warning(admin_warning)

    admin_records = {}
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 导出评分数据")
        for group in get_groups():
            try:
                records = get_all_scores(
                    group,
                    refresh_remote=True,
                    require_remote=True,
                )
                admin_records[group] = records
            except ScorePersistenceError as exc:
                st.error(f"**{group}**：无法读取完整历史记录：{exc}")
                continue
            if records:
                st.markdown(f"**{group}**: {len(records)} 条记录")
                if st.button(f"📥 导出 {group} Excel", key=f"export_{group}", use_container_width=True):
                    export_failed = False
                    try:
                        file_path = export_to_excel(group)
                    except ScorePersistenceError as exc:
                        st.error(f"无法生成完整历史记录：{exc}")
                        file_path = None
                        export_failed = True
                    if file_path:
                        with open(file_path, "rb") as f:
                            st.download_button(
                                label="⬇️ 下载 Excel 文件",
                                data=f,
                                file_name=file_path.name,
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                use_container_width=True,
                            )
                        st.success(f"✅ {group} 评分数据已生成")
                    elif not export_failed:
                        st.warning(f"{group} 暂无评分数据")
            else:
                st.info(f"**{group}**: 暂无评分数据")

    with col2:
        st.markdown("#### 导出全部数据")
        if st.button("📥 导出所有组 Excel", use_container_width=True, type="primary"):
            export_failed = False
            try:
                results = export_all_to_excel()
            except ScorePersistenceError as exc:
                st.error(f"无法生成全部历史记录：{exc}")
                results = {}
                export_failed = True
            if results:
                for group, file_path in results.items():
                    with open(file_path, "rb") as f:
                        st.download_button(
                            label=f"⬇️ 下载 {group} Excel",
                            data=f,
                            file_name=file_path.name,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True,
                        )
                st.success("✅ 所有组数据已生成")
            elif not export_failed:
                st.warning("暂无评分数据可导出")

    st.markdown("---")
    st.markdown("#### 👥 按裁判选择导出")
    all_groups_loaded = set(admin_records) == set(get_groups())
    judge_summaries = _summarize_judge_records(admin_records)

    if not all_groups_loaded:
        st.warning("部分评分组读取失败，无法保证裁判数据完整，暂不提供按裁判导出")
    elif not judge_summaries:
        st.info("暂无评分记录")
    else:
        judge_rows = [
            {
                "选择": False,
                "裁判姓名": summary["judge_name"],
                "裁判编号": summary["judge_id"],
                "评分组": "、".join(summary["groups"]),
                "记录数": summary["record_count"],
                "最早评分": summary["first_time"],
                "最近评分": summary["last_time"],
            }
            for summary in judge_summaries
        ]
        judge_frame = pd.DataFrame(judge_rows)
        edited_judges = st.data_editor(
            judge_frame,
            column_config={
                "选择": st.column_config.CheckboxColumn("选择", default=False),
                "裁判姓名": st.column_config.TextColumn("裁判姓名", width="small"),
                "裁判编号": st.column_config.TextColumn("裁判编号", width="small"),
                "评分组": st.column_config.TextColumn("评分组", width="small"),
                "记录数": st.column_config.NumberColumn("记录数", width="small"),
                "最早评分": st.column_config.TextColumn("最早评分", width="medium"),
                "最近评分": st.column_config.TextColumn("最近评分", width="medium"),
            },
            disabled=[column for column in judge_frame.columns if column != "选择"],
            hide_index=True,
            use_container_width=True,
            key="admin_judge_export_selector",
        )
        selected_judge_keys = {
            _judge_identity(row["裁判姓名"], row["裁判编号"])
            for _, row in edited_judges.loc[
                edited_judges["选择"].fillna(False)
            ].iterrows()
        }
        selected_summaries = [
            summary
            for summary in judge_summaries
            if _judge_identity(summary["judge_name"], summary["judge_id"])
            in selected_judge_keys
        ]
        selected_record_ids = sorted(
            str(record.get("record_id", ""))
            for summary in selected_summaries
            for records in summary["records_by_group"].values()
            for record in records
        )
        st.caption(
            f"已选择 {len(selected_summaries)} 位裁判，"
            f"共 {len(selected_record_ids)} 条评分记录"
        )

        selection_signature = hashlib.sha256(
            json.dumps(
                {
                    "judges": sorted([list(key) for key in selected_judge_keys]),
                    "record_ids": selected_record_ids,
                },
                ensure_ascii=False,
                sort_keys=True,
            ).encode("utf-8")
        ).hexdigest()

        if st.button(
            "📥 生成选中裁判的全部数据",
            type="primary",
            use_container_width=True,
            disabled=not selected_summaries,
        ):
            try:
                export_files = []
                for group in get_groups():
                    group_records = [
                        record
                        for summary in selected_summaries
                        for record in summary["records_by_group"].get(group, [])
                    ]
                    if not group_records:
                        continue
                    file_path = export_records_to_excel(
                        group,
                        group_records,
                        file_label="按裁判选择导出",
                    )
                    with open(file_path, "rb") as export_file:
                        export_files.append(
                            {
                                "group": group,
                                "file_name": file_path.name,
                                "data": export_file.read(),
                            }
                        )
            except (OSError, ValueError) as exc:
                st.error(f"选中裁判数据导出失败：{exc}")
            else:
                st.session_state.selected_judge_export = {
                    "signature": selection_signature,
                    "files": export_files,
                }

        selected_export = st.session_state.get("selected_judge_export", {})
        if (
            selected_export.get("signature") == selection_signature
            and selected_summaries
        ):
            for export_file in selected_export.get("files", []):
                st.download_button(
                    label=f"⬇️ 下载 {export_file['group']} 全部选中裁判数据",
                    data=export_file["data"],
                    file_name=export_file["file_name"],
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    key=f"download_selected_judges_{export_file['group']}",
                )

    st.markdown("---")
    st.markdown("#### 🗑️ 删除管理")
    with st.expander("删除已注册裁判或已有评分数据", expanded=False):
        st.markdown("##### 删除已注册裁判")
        try:
            judges = get_all_judges(refresh_remote=True, require_remote=True)
        except ScorePersistenceError as exc:
            st.error(f"无法读取完整裁判列表：{exc}")
            judges = None

        if judges:
            registered = {}
            for judge in judges:
                key = _judge_identity(
                    judge.get("name", ""),
                    judge.get("judge_id", ""),
                )
                registered.setdefault(key, set()).add(str(judge.get("group", "")))
            registered_rows = [
                {
                    "删除": False,
                    "裁判姓名": name,
                    "裁判编号": judge_id,
                    "注册组别": "、".join(sorted(groups)),
                }
                for (name, judge_id), groups in sorted(registered.items())
            ]
            registered_frame = pd.DataFrame(registered_rows)
            edited_registered = st.data_editor(
                registered_frame,
                column_config={
                    "删除": st.column_config.CheckboxColumn("删除", default=False),
                    "裁判姓名": st.column_config.TextColumn("裁判姓名"),
                    "裁判编号": st.column_config.TextColumn("裁判编号"),
                    "注册组别": st.column_config.TextColumn("注册组别"),
                },
                disabled=[
                    column for column in registered_frame.columns if column != "删除"
                ],
                hide_index=True,
                use_container_width=True,
                key="admin_registered_judge_delete_selector",
            )
            selected_registered_keys = [
                _judge_identity(row["裁判姓名"], row["裁判编号"])
                for _, row in edited_registered.loc[
                    edited_registered["删除"].fillna(False)
                ].iterrows()
            ]
            registered_delete_signature = hashlib.sha256(
                json.dumps(
                    sorted([list(key) for key in selected_registered_keys]),
                    ensure_ascii=False,
                ).encode("utf-8")
            ).hexdigest()[:12]
            st.caption(
                "删除注册信息不会自动删除该裁判已经提交的评分数据。"
            )
            confirm_judge_delete = st.checkbox(
                f"确认删除选中的 {len(selected_registered_keys)} 位注册裁判",
                key=f"confirm_registered_judge_delete_{registered_delete_signature}",
            )
            if st.button(
                "🗑️ 删除选中注册裁判",
                use_container_width=True,
                disabled=not selected_registered_keys or not confirm_judge_delete,
            ):
                try:
                    removed_count = delete_judges(selected_registered_keys)
                except ScorePersistenceError as exc:
                    st.error(f"裁判删除失败：{exc}")
                else:
                    st.session_state.admin_notice = (
                        f"已删除 {removed_count} 条裁判注册信息"
                    )
                    st.rerun()
        elif judges == []:
            st.info("暂无注册裁判")

        st.markdown("---")
        st.markdown("##### 删除已有评分数据")
        if not all_groups_loaded:
            st.warning("部分评分组读取失败，不能执行评分数据删除")
        elif not judge_summaries:
            st.info("暂无评分数据")
        else:
            score_delete_rows = [
                {
                    "删除": False,
                    "裁判姓名": summary["judge_name"],
                    "裁判编号": summary["judge_id"],
                    "评分组": "、".join(summary["groups"]),
                    "记录数": summary["record_count"],
                    "最近评分": summary["last_time"],
                }
                for summary in judge_summaries
            ]
            score_delete_frame = pd.DataFrame(score_delete_rows)
            edited_score_delete = st.data_editor(
                score_delete_frame,
                column_config={
                    "删除": st.column_config.CheckboxColumn("删除", default=False),
                    "裁判姓名": st.column_config.TextColumn("裁判姓名"),
                    "裁判编号": st.column_config.TextColumn("裁判编号"),
                    "评分组": st.column_config.TextColumn("评分组"),
                    "记录数": st.column_config.NumberColumn("记录数"),
                    "最近评分": st.column_config.TextColumn("最近评分"),
                },
                disabled=[
                    column for column in score_delete_frame.columns if column != "删除"
                ],
                hide_index=True,
                use_container_width=True,
                key="admin_score_data_delete_selector",
            )
            selected_score_judge_keys = {
                _judge_identity(row["裁判姓名"], row["裁判编号"])
                for _, row in edited_score_delete.loc[
                    edited_score_delete["删除"].fillna(False)
                ].iterrows()
            }
            selected_score_summaries = [
                summary
                for summary in judge_summaries
                if _judge_identity(summary["judge_name"], summary["judge_id"])
                in selected_score_judge_keys
            ]
            record_ids_by_group = {}
            for summary in selected_score_summaries:
                for group, records in summary["records_by_group"].items():
                    record_ids_by_group.setdefault(group, []).extend(
                        str(record.get("record_id", ""))
                        for record in records
                        if record.get("record_id")
                    )
            selected_score_count = sum(
                len(record_ids) for record_ids in record_ids_by_group.values()
            )
            score_delete_signature = hashlib.sha256(
                json.dumps(
                    {
                        group: sorted(record_ids)
                        for group, record_ids in sorted(record_ids_by_group.items())
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                ).encode("utf-8")
            ).hexdigest()[:12]
            st.caption("评分记录删除后不会在系统中自动恢复，请先导出需要的备份。")
            confirm_score_delete = st.checkbox(
                f"确认删除选中裁判的 {selected_score_count} 条评分记录",
                key=f"confirm_score_data_delete_{score_delete_signature}",
            )
            if st.button(
                "🗑️ 删除选中裁判的全部评分数据",
                use_container_width=True,
                disabled=not selected_score_count or not confirm_score_delete,
            ):
                try:
                    delete_result = delete_score_records(record_ids_by_group)
                except ScorePersistenceError as exc:
                    st.error(f"评分数据删除失败：{exc}")
                else:
                    st.session_state.pop("selected_judge_export", None)
                    st.session_state.admin_notice = (
                        f"已删除 {delete_result['deleted_count']} 条评分记录"
                    )
                    if delete_result["cleanup_warnings"]:
                        st.session_state.admin_warning = (
                            "删除标记已生效，但部分历史文件物理清理失败："
                            + "；".join(delete_result["cleanup_warnings"])
                        )
                    st.rerun()

    # 登出管理
    if st.button("🔒 退出管理", use_container_width=True):
        st.session_state.admin_verified = False
        st.rerun()


# ===================== 入口 =====================

if __name__ == "__main__":
    main()
