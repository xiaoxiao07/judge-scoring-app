"""
登录鉴权模块
负责裁判登录、登出、token 验证、session 管理
"""

import hashlib
from typing import Optional

import streamlit as st

from .data_manager import register_judge, find_judge_by_token
from .scoring import get_groups


def _generate_token(name: str, judge_id: str) -> str:
    """生成裁判唯一 token"""
    return hashlib.sha256(f"{name}|{judge_id}".encode()).hexdigest()[:12]


def login(name: str, judge_id: str, group: str) -> dict:
    """
    裁判登录
    1. 注册/更新裁判信息
    2. 写入 session_state
    3. 将裁判信息写入 URL 参数（用于下次自动登录）
    4. 返回裁判信息
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

    # 注册裁判信息（用作管理后台查看，不影响登录）
    judge_info = register_judge(name, judge_id, group)

    # 写入 session_state
    st.session_state.logged_in = True
    st.session_state.judge_name = judge_info["name"]
    st.session_state.judge_id = judge_info["judge_id"]
    st.session_state.judge_group = judge_info["group"]
    st.session_state.judge_token = judge_info["token"]

    # 将裁判信息写入 URL 参数（不依赖文件存储，冷启动后依然可用）
    st.query_params["token"] = judge_info["token"]
    st.query_params["judge_name"] = judge_info["name"]
    st.query_params["judge_id"] = judge_info["judge_id"]
    st.query_params["judge_group"] = judge_info["group"]

    # 标记为手动登录（用于显示书签提示）
    st.session_state._manual_login = True

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
    for key in ["token", "judge_name", "judge_id", "judge_group"]:
        if key in st.query_params:
            del st.query_params[key]

    st.rerun()


def auto_login_from_token() -> bool:
    """
    从 URL 参数中通过 token 查询文件登录
    优先尝试此方式，但文件可能在冷启动后丢失
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


def auto_login_from_params() -> bool:
    """
    从 URL 参数中直接恢复登录（不依赖文件查询）
    作为 token 查询失败后的兜底方案
    """
    name = st.query_params.get("judge_name")
    judge_id = st.query_params.get("judge_id")
    group = st.query_params.get("judge_group")
    token = st.query_params.get("token", "")

    if not all([name, judge_id, group]):
        return False
    if group not in get_groups():
        return False

    st.session_state.logged_in = True
    st.session_state.judge_name = name
    st.session_state.judge_id = judge_id
    st.session_state.judge_group = group
    st.session_state.judge_token = token
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
    裁判手动输入信息登录，不支持切换他人账号
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

    st.markdown("---")
    st.caption("💡 首次登录后，再次访问此链接将自动进入评分页，无需重复登录。")
