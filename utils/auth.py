"""
登录鉴权模块
负责裁判登录、登出、token 验证、session 管理
"""

import hashlib
from typing import Optional

import streamlit as st

from .data_manager import register_judge, find_judge_by_token, find_judge_by_id, get_all_judges
from .scoring import get_groups


def _generate_token(name: str, judge_id: str) -> str:
    """生成裁判唯一 token"""
    return hashlib.sha256(f"{name}|{judge_id}".encode()).hexdigest()[:12]


def login(name: str, judge_id: str, group: str) -> dict:
    """
    裁判登录
    1. 注册/更新裁判信息
    2. 写入 session_state
    3. 返回裁判信息
    """
    if not name or not name.strip():
        st.error("请输入裁判姓名")
        return None
    if not judge_id or not judge_id.strip():
        st.error("请输入裁判编号")
        return None
    if not group or group not in get_groups():
        st.error("请选择裁判组")
        return None

    name = name.strip()
    judge_id = judge_id.strip()

    # 注册裁判信息
    judge_info = register_judge(name, judge_id, group)

    # 写入 session_state
    st.session_state.logged_in = True
    st.session_state.judge_name = judge_info["name"]
    st.session_state.judge_id = judge_info["judge_id"]
    st.session_state.judge_group = judge_info["group"]
    st.session_state.judge_token = judge_info["token"]

    # 写入 URL query params
    st.query_params["token"] = judge_info["token"]

    return judge_info


def logout():
    """
    裁判登出
    清除 session_state 和 URL 参数
    """
    keys = ["logged_in", "judge_name", "judge_id", "judge_group", "judge_token"]
    for k in keys:
        if k in st.session_state:
            del st.session_state[k]

    # 清除 URL 参数
    if "token" in st.query_params:
        del st.query_params["token"]

    st.rerun()


def auto_login_from_token() -> bool:
    """
    从 URL 参数中自动登录
    如果 URL 中有 token 且有效，自动填充 session_state
    返回是否成功
    """
    token = st.query_params.get("token")
    if not token:
        return False

    judge = find_judge_by_token(token)
    if not judge:
        return False

    st.session_state.logged_in = True
    st.session_state.judge_name = judge["name"]
    st.session_state.judge_id = judge["judge_id"]
    st.session_state.judge_group = judge["group"]
    st.session_state.judge_token = judge["token"]
    return True


def is_logged_in() -> bool:
    """检查是否已登录"""
    return st.session_state.get("logged_in", False)


def get_current_judge() -> Optional[dict]:
    """获取当前登录裁判信息"""
    if not is_logged_in():
        return None
    return {
        "name": st.session_state.get("judge_name"),
        "judge_id": st.session_state.get("judge_id"),
        "group": st.session_state.get("judge_group"),
        "token": st.session_state.get("judge_token"),
    }


def render_login_page():
    """
    渲染登录页面
    包括：输入框、已注册裁判一键登录
    """
    st.title("🏅 裁判评分系统")
    st.markdown("---")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.image(
            "https://img.icons8.com/fluency/96/judge.png",
            width=120,
        )

    with col2:
        st.markdown("### 裁判登录")
        name = st.text_input("👤 裁判姓名", placeholder="请输入您的姓名", key="login_name")
        judge_id = st.text_input("🔑 裁判编号", placeholder="请输入您的编号", key="login_id")
        group = st.selectbox("📋 裁判组", get_groups(), key="login_group")

        if st.button("✅ 登录", type="primary", use_container_width=True):
            result = login(name, judge_id, group)
            if result:
                st.success(f"欢迎，{result['name']} 裁判！")
                st.rerun()

    # 显示已注册裁判列表（方便再次登录）
    st.markdown("---")
    st.markdown("### 📋 已注册裁判")
    st.caption("点击您的名字可直接登录（无需重复输入信息）")

    judges = get_all_judges()
    if not judges:
        st.info("暂无已注册裁判，请填写上方信息进行首次登录。")
    else:
        # 按组分类显示
        for group in get_groups():
            group_judges = [j for j in judges if j.get("group") == group]
            if not group_judges:
                continue

            st.markdown(f"**{group}**")
            cols = st.columns(min(len(group_judges), 4))
            for idx, j in enumerate(group_judges):
                col_idx = idx % 4
                with cols[col_idx]:
                    if st.button(
                        f"{j['name']} ({j['judge_id']})",
                        key=f"quick_login_{j['judge_id']}",
                        use_container_width=True,
                    ):
                        # 一键登录
                        login(j["name"], j["judge_id"], j["group"])
                        st.rerun()
