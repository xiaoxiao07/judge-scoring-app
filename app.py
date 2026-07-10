"""
裁判评分系统 — Streamlit 主程序

裁判通过手机浏览器访问，进行评分操作。
支持答辩组和实操组两类裁判，自动保存评分记录到 JSON，
并支持导出为 Excel 格式。

部署方式：Streamlit Community Cloud
"""

import streamlit as st

from utils.auth import (
    auto_login_from_token,
    auto_login_from_params,
    is_logged_in,
    get_current_judge,
    render_login_page,
    logout,
)
from utils.scoring import get_criteria, get_total_score, get_groups, get_deductions, get_veto
from utils.data_manager import (
    init_data_files,
    save_score,
    get_all_scores,
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
<style>
    /* 移动端触摸友好 */
    .stSlider > div[data-testid="stThumbValue"] {
        font-size: 16px !important;
        font-weight: bold;
    }
    div.stButton > button {
        min-height: 44px;  /* 移动端最小触摸目标 */
        font-size: 16px;
    }
    /* 评分项卡片样式 */
    .score-card {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 15px 15px 5px 15px;
        margin-bottom: 10px;
        border: 1px solid #e9ecef;
    }
    .score-card .criterion-name {
        font-size: 16px;
        font-weight: 600;
        margin-bottom: 2px;
        color: #1a1a1a !important;
    }
    .score-card .criterion-desc {
        font-size: 12px;
        color: #555555 !important;
        margin-bottom: 8px;
    }
    .score-card .criterion-range {
        font-size: 12px;
        color: #e67e22 !important;
        font-weight: 500;
        margin-bottom: 6px;
    }
    /* 评分项卡片内数字输入框标签 */
    .score-card label {
        color: #1a1a1a !important;
    }
    /* 模块标题 */
    .module-title {
        font-size: 15px;
        font-weight: 700;
        color: #1a1a1a !important;
        margin: 12px 0 8px 0;
        padding-bottom: 4px;
        border-bottom: 2px solid #4472C4;
    }
    /* 裁判信息栏 */
    .judge-info-bar {
        background: #e8f4f8;
        border-radius: 10px;
        padding: 10px 15px;
        margin-bottom: 15px;
        border-left: 4px solid #2196F3;
        color: #1a1a1a !important;
    }
    /* 总分显示 */
    .total-score-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 15px;
        padding: 15px;
        text-align: center;
        margin: 15px 0;
    }
    .total-score-box .score-value {
        font-size: 36px;
        font-weight: bold;
    }
    .total-score-box .score-label {
        font-size: 14px;
        opacity: 0.9;
    }
    /* 裁判信息栏 */
    .judge-info-bar {
        background: #e8f4f8;
        border-radius: 10px;
        padding: 10px 15px;
        margin-bottom: 15px;
        border-left: 4px solid #2196F3;
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

    # --- 手动登录后显示书签提示 ---
    if st.session_state.pop("_manual_login", False):
        st.info(
            "🔖 **登录成功！**\n\n"
            "请在手机浏览器中**将此页面添加到书签**，下次直接打开书签即可进入评分页，无需再次输入信息。\n\n"
            "👉 在 Safari/Chrome 中点击分享按钮 → **添加到主屏幕** 使用更方便",
            icon="📌",
        )

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


def render_scoring_page(judge: dict):
    """渲染评分表单"""
    group = judge["group"]
    criteria = get_criteria(group)
    total_max = get_total_score(group)
    deductions_def = get_deductions(group)
    veto_def = get_veto(group)

    st.markdown(f"### 📝 {group}评分")
    st.caption("请为参赛选手的每个评分项打分")

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

    # 评分项 — 使用数字输入
    scores = {}
    st.markdown("#### 评分项")

    if group == "线上赛":
        # 线上赛按考核模块分组显示
        modules = {}
        for name, info in criteria.items():
            module = info.get("module", "其他")
            modules.setdefault(module, []).append((name, info))
        for module_name, items in modules.items():
            st.markdown(f"<div class='module-title'>{module_name}</div>", unsafe_allow_html=True)
            for criterion_name, criterion_info in items:
                max_score = criterion_info["max"]
                desc = criterion_info["description"]
                score_range = criterion_info.get("score_range", f"0~{max_score}分")
                st.markdown(
                    f"<div class='score-card'>"
                    f"<div class='criterion-name'>{criterion_name}</div>"
                    f"<div class='criterion-desc'>{desc}</div>"
                    f"<div class='criterion-range'>📊 评分区间：{score_range}</div>",
                    unsafe_allow_html=True,
                )
                scores[criterion_name] = st.number_input(
                    label=criterion_name,
                    min_value=0,
                    max_value=max_score,
                    value=0,
                    step=1,
                    key=f"score_{criterion_name}_{submit_round}",
                    label_visibility="collapsed",
                )
                st.markdown("</div>", unsafe_allow_html=True)
    else:
        # 其他组直接显示
        for criterion_name, criterion_info in criteria.items():
            max_score = criterion_info["max"]
            desc = criterion_info["description"]
            st.markdown(
                f"<div class='score-card'>"
                f"<div class='criterion-name'>{criterion_name}</div>"
                f"<div class='criterion-desc'>{desc}（满分 {max_score} 分）</div>",
                unsafe_allow_html=True,
            )
            scores[criterion_name] = st.number_input(
                label=criterion_name,
                min_value=0,
                max_value=max_score,
                value=0,
                step=1,
                key=f"score_{criterion_name}_{submit_round}",
                label_visibility="collapsed",
            )
            st.markdown("</div>", unsafe_allow_html=True)

    # === 线上赛：扣分项 ===
    deduction_total = 0
    deductions_applied = {}
    if deductions_def:
        st.markdown("---")
        st.markdown("#### ⚠️ 扣分项")
        st.caption("如存在以下情况，勾选对应扣分项")
        for ded_name, ded_info in deductions_def.items():
            deduct_val = ded_info["deduct"]
            desc = ded_info["description"]
            if deduct_val == "half":
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**{ded_name}**")
                    st.caption(desc)
                with col2:
                    bad_steps = st.number_input(
                        label=f"问题步数-{ded_name}",
                        min_value=0,
                        max_value=6,
                        value=0,
                        step=1,
                        key=f"ded_steps_{ded_name}_{submit_round}",
                        label_visibility="collapsed",
                    )
                    if bad_steps > 0:
                        step_deduct = bad_steps * 1
                        deductions_applied[ded_name] = step_deduct
                        st.caption(f"扣 {step_deduct} 分")
            else:
                checked = st.checkbox(
                    f"{ded_name}（扣 {deduct_val} 分）",
                    key=f"ded_{ded_name}_{submit_round}",
                    help=desc,
                )
                if checked:
                    deductions_applied[ded_name] = deduct_val

        deduction_total = sum(deductions_applied.values())
        if deduction_total > 0:
            st.warning(f"扣分合计：{deduction_total} 分")

    # === 线上赛：否决项（勾选后总分归零） ===
    veto_triggered = False
    if veto_def:
        st.markdown("---")
        st.markdown("#### 🚫 否决项")
        st.caption("如触发以下任何否决项，选手总分直接计 0 分，请谨慎勾选")
        for veto_name, veto_info in veto_def.items():
            checked = st.checkbox(
                f"🚨 **{veto_name}**",
                key=f"veto_{veto_name}_{submit_round}",
                help=veto_info["description"],
            )
            if checked:
                veto_triggered = True
                st.error(f"⚠️ 已触发否决项：{veto_info['description']}")

    # 实时总分（含扣分和否决项）
    raw_total = sum(scores.values())
    if veto_triggered:
        final_total = 0
    else:
        final_total = max(0, raw_total - deduction_total)

    if veto_triggered:
        st.markdown(
            f"<div style='background:#f8d7da;border:2px solid #dc3545;border-radius:15px;padding:20px;text-align:center;margin:15px 0;'>"
            f"<div style='font-size:18px;font-weight:bold;color:#dc3545;'>🚫 否决项已触发</div>"
            f"<div style='font-size:36px;font-weight:bold;color:#dc3545;margin:10px 0;'>0 / {total_max}</div>"
            f"<div style='font-size:14px;color:#666;'>选手演示环节总分计 0 分</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
    elif deductions_def:
        st.markdown(
            f"<div class='total-score-box'>"
            f"<div class='score-label'>原始总分</div>"
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
            disabled=not contestant_id,
        )

    if submitted:
        if not contestant_id or not contestant_id.strip():
            st.error("请输入被评分选手的编号或姓名")
        else:
            # 收集触发的否决项
            veto_triggered_items = []
            if veto_def:
                for veto_name in veto_def:
                    if st.session_state.get(f"veto_{veto_name}_{submit_round}", False):
                        veto_triggered_items.append(veto_name)
            record = save_score(
                judge,
                contestant_id.strip(),
                scores,
                deductions=deductions_applied if deductions_applied else None,
                final_score=final_total,
                veto_triggered=veto_triggered,
                veto_items=veto_triggered_items if veto_triggered_items else None,
            )
            st.success(
                f"✅ {judge['name']} 裁判 → 选手 {record['contestant_id']} "
                f"得分 {record['total_score']}/{record['total_max']}，已记录！"
            )
            st.session_state.submit_round += 1
            st.rerun()


# ===================== 历史记录页面 =====================


def render_history_page(judge: dict):
    """渲染历史评分记录"""
    group = judge["group"]
    records = get_all_scores(group)

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
    if has_deductions:
        headers = ["选手编号"] + score_headers + ["原始分", "扣分", "最终得分", "评分时间"]
    else:
        headers = ["选手编号"] + score_headers + ["总分", "评分时间"]

    table_data = []
    for r in reversed(my_records):  # 最新的在前
        row = [r["contestant_id"]]
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

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 导出评分数据")
        for group in get_groups():
            records = get_all_scores(group)
            if records:
                st.markdown(f"**{group}**: {len(records)} 条记录")
                if st.button(f"📥 导出 {group} Excel", key=f"export_{group}", use_container_width=True):
                    file_path = export_to_excel(group)
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
                    else:
                        st.warning(f"{group} 暂无评分数据")
            else:
                st.info(f"**{group}**: 暂无评分数据")

    with col2:
        st.markdown("#### 导出全部数据")
        if st.button("📥 导出所有组 Excel", use_container_width=True, type="primary"):
            results = export_all_to_excel()
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
            else:
                st.warning("暂无评分数据可导出")

    # 查看所有裁判注册信息
    st.markdown("---")
    st.markdown("#### 📋 已注册裁判列表")
    from utils.data_manager import get_all_judges

    judges = get_all_judges()
    if judges:
        judge_table = [[j["name"], j["judge_id"], j["group"]] for j in judges]
        st.dataframe(
            judge_table,
            column_config={
                0: st.column_config.TextColumn("裁判姓名"),
                1: st.column_config.TextColumn("裁判编号"),
                2: st.column_config.TextColumn("裁判组"),
            },
            hide_index=True,
            use_container_width=True,
        )
    else:
        st.info("暂无注册裁判")

    # 登出管理
    if st.button("🔒 退出管理", use_container_width=True):
        st.session_state.admin_verified = False
        st.rerun()


# ===================== 入口 =====================

if __name__ == "__main__":
    main()
