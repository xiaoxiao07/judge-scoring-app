"""
数据存储管理模块
负责 JSON 数据的读写、Excel 导出、数据文件初始化、GitHub 持久化同步
"""

import base64
import hashlib
import json
import os
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import openpyxl
import requests
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

from .scoring import get_criteria, get_total_score, get_groups, normalize_group

# 数据目录
DATA_DIR = Path(__file__).parent.parent / "data"

# 裁判信息文件
JUDGES_FILE = DATA_DIR / "judges.json"

# 评分记录文件（沿用原文件名，保留已有评分数据）
SCORE_FILES = {
    "答辩组": DATA_DIR / "scores_线上答辩.json",
    "实操组": DATA_DIR / "scores_甘肃线下实操.json",
}

# GitHub 仓库信息。评分数据写入独立分支，避免每次提交触发应用重新部署。
GITHUB_REPO = "xiaoxiao07/judge-scoring-app"
GITHUB_BRANCH = "main"
GITHUB_DATA_BRANCH = "score-data"
GITHUB_RAW_BASE = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}/"
GITHUB_API_BASE = f"https://api.github.com/repos/{GITHUB_REPO}"
GITHUB_TIMEOUT = 15
GITHUB_SYNC_RETRIES = 24

_SCORE_DATA_LOCK = threading.RLock()
_INITIALIZED = False


class ScorePersistenceError(RuntimeError):
    """评分未能在远端完成持久化确认。"""


def _get_github_token() -> str:
    """从 Streamlit secrets 或环境变量获取 GitHub token。"""
    env_token = os.environ.get("GITHUB_TOKEN", "")
    if env_token:
        return env_token
    try:
        import streamlit as st

        return str(st.secrets.get("GITHUB_TOKEN", ""))
    except Exception:
        return ""


def _github_headers(token: str = "") -> dict:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Cache-Control": "no-cache",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _load_from_github(file_path: Path, repo_path: str) -> bool:
    """从 main 分支 raw 地址加载普通 JSON 列表文件。"""
    url = GITHUB_RAW_BASE + repo_path
    try:
        response = requests.get(
            url,
            headers={"Cache-Control": "no-cache"},
            params={"_": time.time_ns()},
            timeout=10,
        )
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                _write_json(file_path, data)
                return True
    except Exception:
        pass
    return False


def _sync_to_github(file_path: Path, repo_path: str, commit_msg: str) -> bool:
    """同步普通 JSON 文件（目前仅用于裁判注册信息）。"""
    token = _get_github_token()
    if not token:
        return False

    url = f"{GITHUB_API_BASE}/contents/{repo_path}"
    try:
        content = file_path.read_text(encoding="utf-8")
        encoded = base64.b64encode(content.encode("utf-8")).decode("utf-8")
        headers = _github_headers(token)
        response = requests.get(
            url,
            headers=headers,
            params={"ref": GITHUB_BRANCH},
            timeout=GITHUB_TIMEOUT,
        )
        sha = response.json().get("sha") if response.status_code == 200 else None
        payload = {
            "message": commit_msg,
            "content": encoded,
            "branch": GITHUB_BRANCH,
        }
        if sha:
            payload["sha"] = sha
        response = requests.put(
            url,
            json=payload,
            headers=headers,
            timeout=GITHUB_TIMEOUT,
        )
        return response.status_code in (200, 201)
    except Exception:
        return False


def _sync_judges_to_github() -> bool:
    """同步裁判信息到 GitHub。"""
    return _sync_to_github(
        JUDGES_FILE,
        "data/judges.json",
        "Auto-sync: update judges info",
    )


def _read_json(file_path: Path) -> list:
    """读取 JSON 列表文件。"""
    if not file_path.exists():
        return []
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, FileNotFoundError, OSError):
        return []


def _write_json(file_path: Path, data: list):
    """使用临时文件和原子替换写入 JSON，避免并发读取到半写文件。"""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = file_path.with_name(
        f".{file_path.name}.{os.getpid()}.{threading.get_ident()}.{uuid.uuid4().hex}.tmp"
    )
    try:
        with open(temp_path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temp_path, file_path)
    finally:
        if temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass


def _legacy_record_digest(record: dict) -> str:
    payload = {key: value for key, value in record.items() if key != "record_id"}
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _ensure_record_ids(records: list) -> list:
    """为旧记录生成稳定 ID；相同旧记录通过出现序号保留，不误去重。"""
    occurrences = {}
    normalized = []
    for source_record in records:
        if not isinstance(source_record, dict):
            continue
        record = dict(source_record)
        if not record.get("record_id"):
            digest = _legacy_record_digest(record)
            occurrences[digest] = occurrences.get(digest, 0) + 1
            record["record_id"] = f"legacy-{digest[:24]}-{occurrences[digest]}"
        normalized.append(record)
    return normalized


def _merge_score_records(*record_sets: list) -> list:
    """按 record_id 合并多份记录；先出现的版本优先，任何记录都不会被整文件覆盖。"""
    merged = []
    seen_ids = set()
    for records in record_sets:
        for record in _ensure_record_ids(records or []):
            record_id = record["record_id"]
            if record_id in seen_ids:
                continue
            seen_ids.add(record_id)
            merged.append(record)
    return merged


def _fetch_github_records(repo_path: str, branch: str, token: str = "") -> dict:
    """读取指定分支上的 JSON 记录文件，并返回内容及用于 CAS 的 SHA。"""
    url = f"{GITHUB_API_BASE}/contents/{repo_path}"
    try:
        response = requests.get(
            url,
            headers=_github_headers(token),
            params={"ref": branch},
            timeout=GITHUB_TIMEOUT,
        )
        if response.status_code == 404:
            return {"ok": True, "exists": False, "records": [], "sha": None, "error": ""}
        if response.status_code != 200:
            # 未配置令牌的只读场景可能触发 GitHub API 速率限制；
            # 后台读取可退回 raw 文件，但写入仍必须使用带 SHA 的认证 API。
            if not token:
                raw_url = (
                    f"https://raw.githubusercontent.com/{GITHUB_REPO}/"
                    f"{branch}/{repo_path}"
                )
                raw_response = requests.get(
                    raw_url,
                    headers={"Cache-Control": "no-cache"},
                    params={"_": time.time_ns()},
                    timeout=GITHUB_TIMEOUT,
                )
                if raw_response.status_code == 404:
                    return {
                        "ok": True,
                        "exists": False,
                        "records": [],
                        "sha": None,
                        "error": "",
                    }
                if raw_response.status_code == 200:
                    records = raw_response.json()
                    if isinstance(records, list):
                        return {
                            "ok": True,
                            "exists": True,
                            "records": records,
                            "sha": None,
                            "error": "",
                        }
            return {
                "ok": False,
                "exists": False,
                "records": [],
                "sha": None,
                "error": f"GitHub 读取失败（HTTP {response.status_code}）",
            }

        payload = response.json()
        if payload.get("encoding") == "base64" and payload.get("content"):
            raw = base64.b64decode(payload["content"]).decode("utf-8")
        elif payload.get("download_url"):
            download = requests.get(
                payload["download_url"],
                headers={"Cache-Control": "no-cache"},
                params={"_": time.time_ns()},
                timeout=GITHUB_TIMEOUT,
            )
            if download.status_code != 200:
                return {
                    "ok": False,
                    "exists": True,
                    "records": [],
                    "sha": payload.get("sha"),
                    "error": f"GitHub 文件下载失败（HTTP {download.status_code}）",
                }
            raw = download.text
        else:
            return {
                "ok": False,
                "exists": True,
                "records": [],
                "sha": payload.get("sha"),
                "error": "GitHub 返回的评分文件内容不可读取",
            }

        records = json.loads(raw)
        if not isinstance(records, list):
            raise ValueError("评分文件不是 JSON 列表")
        return {
            "ok": True,
            "exists": True,
            "records": records,
            "sha": payload.get("sha"),
            "error": "",
        }
    except Exception as exc:
        return {
            "ok": False,
            "exists": False,
            "records": [],
            "sha": None,
            "error": f"GitHub 读取异常：{exc}",
        }


def _put_github_records(
    repo_path: str,
    records: list,
    sha: Optional[str],
    token: str,
    commit_msg: str,
) -> dict:
    """使用当前文件 SHA 更新 score-data 分支；SHA 不匹配时由上层重新合并重试。"""
    url = f"{GITHUB_API_BASE}/contents/{repo_path}"
    content = json.dumps(records, ensure_ascii=False, indent=2)
    payload = {
        "message": commit_msg,
        "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
        "branch": GITHUB_DATA_BRANCH,
    }
    if sha:
        payload["sha"] = sha
    try:
        response = requests.put(
            url,
            json=payload,
            headers=_github_headers(token),
            timeout=GITHUB_TIMEOUT,
        )
        if response.status_code in (200, 201):
            return {"ok": True, "conflict": False, "status": response.status_code, "error": ""}
        message = ""
        try:
            message = response.json().get("message", "")
        except Exception:
            message = response.text[:200]
        return {
            "ok": False,
            "conflict": response.status_code in (409, 422),
            "status": response.status_code,
            "error": f"GitHub 写入失败（HTTP {response.status_code}）：{message}",
        }
    except Exception as exc:
        return {
            "ok": False,
            "conflict": True,
            "status": 0,
            "error": f"GitHub 写入异常：{exc}",
        }


def _ensure_data_branch(token: str) -> tuple[bool, str]:
    """确保独立评分数据分支存在。"""
    headers = _github_headers(token)
    data_ref_url = f"{GITHUB_API_BASE}/git/ref/heads/{GITHUB_DATA_BRANCH}"
    try:
        response = requests.get(data_ref_url, headers=headers, timeout=GITHUB_TIMEOUT)
        if response.status_code == 200:
            return True, ""
        if response.status_code != 404:
            return False, f"无法检查数据分支（HTTP {response.status_code}）"

        main_ref_url = f"{GITHUB_API_BASE}/git/ref/heads/{GITHUB_BRANCH}"
        response = requests.get(main_ref_url, headers=headers, timeout=GITHUB_TIMEOUT)
        if response.status_code != 200:
            return False, f"无法读取主分支（HTTP {response.status_code}）"
        main_sha = response.json()["object"]["sha"]

        response = requests.post(
            f"{GITHUB_API_BASE}/git/refs",
            headers=headers,
            json={"ref": f"refs/heads/{GITHUB_DATA_BRANCH}", "sha": main_sha},
            timeout=GITHUB_TIMEOUT,
        )
        if response.status_code == 201:
            return True, ""
        if response.status_code == 422:
            verify = requests.get(data_ref_url, headers=headers, timeout=GITHUB_TIMEOUT)
            if verify.status_code == 200:
                return True, ""
        return False, f"无法创建数据分支（HTTP {response.status_code}）"
    except Exception as exc:
        return False, f"检查数据分支异常：{exc}"


def _sleep_for_retry(attempt: int):
    time.sleep(min(0.05 * (attempt + 1), 0.5))


def _persist_score_records_to_github(
    group: str,
    local_records: list,
    required_record_id: str,
) -> tuple[bool, list, str]:
    """
    将本地记录与 score-data、main 两个分支合并后以 SHA 条件更新。
    并发冲突会重新读取、合并并重试，成功返回表示远端已确认包含该提交。
    """
    token = _get_github_token()
    if not token:
        return False, local_records, "未配置 GITHUB_TOKEN，无法确认云端持久化"

    branch_ok, branch_error = _ensure_data_branch(token)
    if not branch_ok:
        return False, local_records, branch_error

    file_path = SCORE_FILES[group]
    repo_path = f"data/{file_path.name}"
    last_error = "GitHub 同步未完成"

    for attempt in range(GITHUB_SYNC_RETRIES):
        primary = _fetch_github_records(repo_path, GITHUB_DATA_BRANCH, token)
        legacy = _fetch_github_records(repo_path, GITHUB_BRANCH, token)
        if not primary["ok"] or not legacy["ok"]:
            last_error = primary["error"] or legacy["error"]
            _sleep_for_retry(attempt)
            continue

        candidate = _merge_score_records(
            primary["records"],
            legacy["records"],
            local_records,
        )
        candidate_ids = {record["record_id"] for record in candidate}
        if required_record_id not in candidate_ids:
            return False, local_records, "待保存记录未进入合并结果"

        primary_records = _ensure_record_ids(primary["records"])
        primary_ids = {record["record_id"] for record in primary_records}
        if candidate_ids.issubset(primary_ids):
            return True, _merge_score_records(primary_records, candidate), ""

        result = _put_github_records(
            repo_path,
            candidate,
            primary["sha"],
            token,
            f"Score-sync: append {group} record {required_record_id[:12]}",
        )
        if result["ok"]:
            return True, candidate, ""

        last_error = result["error"]
        if not result["conflict"] and result["status"] in (400, 401, 403, 404):
            break
        _sleep_for_retry(attempt)

    # 处理“远端已成功但客户端响应丢失”的情况：最终再读取一次确认全部本地记录。
    final_snapshot = _fetch_github_records(repo_path, GITHUB_DATA_BRANCH, token)
    if final_snapshot["ok"]:
        remote_records = _ensure_record_ids(final_snapshot["records"])
        remote_ids = {record["record_id"] for record in remote_records}
        local_ids = {record["record_id"] for record in _ensure_record_ids(local_records)}
        if required_record_id in remote_ids and local_ids.issubset(remote_ids):
            return True, remote_records, ""

    return False, local_records, last_error


def refresh_score_cache(group: str, require_remote: bool = False) -> list:
    """合并 score-data、main 和本地缓存，供历史页与后台完整导出。"""
    normalized_group = normalize_group(group)
    file_path = SCORE_FILES.get(normalized_group)
    if not file_path:
        return []

    token = _get_github_token()
    repo_path = f"data/{file_path.name}"
    with _SCORE_DATA_LOCK:
        local_records = _read_json(file_path)
        primary = _fetch_github_records(repo_path, GITHUB_DATA_BRANCH, token)
        legacy = _fetch_github_records(repo_path, GITHUB_BRANCH, token)
        if require_remote and (not primary["ok"] or not legacy["ok"]):
            detail = primary["error"] or legacy["error"] or "远端历史记录读取失败"
            raise ScorePersistenceError(detail)

        record_sets = []
        if primary["ok"]:
            record_sets.append(primary["records"])
        if legacy["ok"]:
            record_sets.append(legacy["records"])
        record_sets.append(local_records)
        merged = _merge_score_records(*record_sets)
        _write_json(file_path, merged)
        return merged


def init_data_files():
    """初始化数据文件，并在每个进程首次启动时合并远端历史记录。"""
    global _INITIALIZED
    with _SCORE_DATA_LOCK:
        if _INITIALIZED:
            return
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        if not JUDGES_FILE.exists():
            _write_json(JUDGES_FILE, [])
        for group in get_groups():
            if group in SCORE_FILES and not SCORE_FILES[group].exists():
                _write_json(SCORE_FILES[group], [])

        _load_from_github(JUDGES_FILE, "data/judges.json")
        for group in get_groups():
            if group in SCORE_FILES:
                refresh_score_cache(group, require_remote=False)
        _INITIALIZED = True


# ===================== 裁判管理 =====================


def register_judge(name: str, judge_id: str, group: str) -> dict:
    """注册裁判（如已存在则更新），返回裁判信息字典。"""
    judges = _read_json(JUDGES_FILE)
    for judge in judges:
        if judge["judge_id"] == judge_id:
            judge["name"] = name
            judge["group"] = group
            _write_json(JUDGES_FILE, judges)
            return judge

    token = hashlib.sha256(f"{name}|{judge_id}".encode()).hexdigest()[:12]
    judge_info = {
        "name": name,
        "judge_id": judge_id,
        "group": group,
        "token": token,
    }
    judges.append(judge_info)
    _write_json(JUDGES_FILE, judges)
    _sync_judges_to_github()
    return judge_info


def find_judge_by_token(token: str) -> Optional[dict]:
    """根据 token 查找裁判信息。"""
    for judge in _read_json(JUDGES_FILE):
        if judge.get("token") == token:
            return judge
    return None


def find_judge_by_id(judge_id: str) -> Optional[dict]:
    """根据编号查找裁判信息。"""
    for judge in _read_json(JUDGES_FILE):
        if judge["judge_id"] == judge_id:
            return judge
    return None


def get_all_judges() -> list:
    """获取所有已注册裁判。"""
    return _read_json(JUDGES_FILE)


# ===================== 评分记录管理 =====================


def save_score(
    judge_info: dict,
    contestant_id: str,
    scores: dict,
    deductions: Optional[dict] = None,
    final_score: Optional[float] = None,
    veto_triggered: bool = False,
    veto_items: Optional[list] = None,
    score_zero_triggered: bool = False,
    score_zero_items: Optional[list] = None,
    score_overrides: Optional[list] = None,
    duration: Optional[str] = None,
    record_id: Optional[str] = None,
) -> dict:
    """
    保存一条评分记录。仅当 GitHub 已确认包含该 record_id 时返回成功；
    同一个 record_id 可安全重试，不会产生重复记录。
    """
    group = normalize_group(judge_info["group"])
    file_path = SCORE_FILES.get(group)
    if not file_path:
        raise ValueError(f"未知的裁判组: {group}")

    record_id = record_id or uuid.uuid4().hex
    with _SCORE_DATA_LOCK:
        records = _ensure_record_ids(_read_json(file_path))
        existing = next(
            (record for record in records if record.get("record_id") == record_id),
            None,
        )
        if existing:
            record = existing
        else:
            score_total = sum(scores.values())
            record = {
                "record_id": record_id,
                "judge_name": judge_info["name"],
                "judge_id": judge_info["judge_id"],
                "judge_group": group,
                "contestant_id": contestant_id,
                "scores": {
                    key: int(value)
                    if isinstance(value, float) and value.is_integer()
                    else value
                    for key, value in scores.items()
                },
                "total_score": final_score if final_score is not None else score_total,
                "raw_score": score_total,
                "total_max": get_total_score(group),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "saved_at_utc": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            }
            if duration:
                record["duration"] = duration
            if deductions:
                record["deductions"] = deductions
                record["deduction_total"] = sum(
                    value
                    for value in deductions.values()
                    if isinstance(value, (int, float))
                )
            if veto_triggered:
                record["veto_triggered"] = True
                record["veto_items"] = veto_items or []
            if score_zero_triggered:
                record["score_zero_triggered"] = True
                record["score_zero_items"] = score_zero_items or []
            if score_overrides:
                record["score_overrides"] = score_overrides

        local_records = _merge_score_records(records, [record])
        success, confirmed_records, error = _persist_score_records_to_github(
            group,
            local_records,
            record_id,
        )
        if not success:
            raise ScorePersistenceError(
                f"云端未确认保存，系统没有显示成功：{error}。请保持当前页面并重试"
            )

        confirmed_records = _merge_score_records(confirmed_records, local_records)
        _write_json(file_path, confirmed_records)
        return next(
            confirmed
            for confirmed in confirmed_records
            if confirmed.get("record_id") == record_id
        )


def get_all_scores(
    group: str,
    refresh_remote: bool = False,
    require_remote: bool = False,
) -> list:
    """获取某组全部记录；后台导出可要求远端刷新必须成功。"""
    normalized_group = normalize_group(group)
    file_path = SCORE_FILES.get(normalized_group)
    if not file_path:
        return []
    if refresh_remote:
        return refresh_score_cache(normalized_group, require_remote=require_remote)
    with _SCORE_DATA_LOCK:
        records = _ensure_record_ids(_read_json(file_path))
        _write_json(file_path, records)
        return records


# ===================== Excel 导出 =====================


def _style_header(ws, headers: list, row: int = 1):
    """设置表头样式。"""
    header_font = Font(bold=True, size=11, color="FFFFFF")
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    thin_border = Border(
        left=Side(style="thin", color="B7C9E2"),
        right=Side(style="thin", color="B7C9E2"),
        top=Side(style="thin", color="B7C9E2"),
        bottom=Side(style="thin", color="B7C9E2"),
    )
    for col_idx, header in enumerate(headers, 1):
        cell = ws.cell(row=row, column=col_idx, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
        cell.border = thin_border
    ws.row_dimensions[row].height = 42


def _format_mapping(mapping: Optional[dict]) -> str:
    if not mapping:
        return ""
    return "；".join(f"{key}：{value}" for key, value in mapping.items())


def _format_items(items: Optional[list]) -> str:
    return "；".join(str(item) for item in (items or []))


def _apply_sheet_layout(ws, headers: list, width_cap: int = 30):
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions
    ws.sheet_view.showGridLines = False
    for col_idx, header_text in enumerate(headers, 1):
        text_width = sum(2 if ord(char) > 127 else 1 for char in str(header_text)) + 2
        ws.column_dimensions[openpyxl.utils.get_column_letter(col_idx)].width = min(
            max(text_width, 10),
            width_cap,
        )


def export_to_excel(group: str) -> Optional[Path]:
    """刷新并导出某组全部历史评分；远端读取失败时拒绝生成不完整文件。"""
    normalized_group = normalize_group(group)
    records = get_all_scores(
        normalized_group,
        refresh_remote=True,
        require_remote=True,
    )
    if not records:
        return None

    criteria = get_criteria(normalized_group)
    workbook = openpyxl.Workbook()
    score_sheet = workbook.active
    score_sheet.title = f"{normalized_group}评分记录"

    score_headers = [f"{key}({value['max']})" for key, value in criteria.items()]
    has_duration = any(record.get("duration") for record in records)
    headers = ["提交ID", "裁判姓名", "裁判编号", "裁判组", "选手编号/姓名"]
    if has_duration:
        headers.append("用时")
    headers += score_headers + ["原始总分", "扣分合计", "最终总分", "满分", "评分时间"]
    _style_header(score_sheet, headers)

    data_font = Font(size=11)
    center_align = Alignment(horizontal="center", vertical="center")
    thin_border = Border(
        left=Side(style="thin", color="D9E2F3"),
        right=Side(style="thin", color="D9E2F3"),
        top=Side(style="thin", color="D9E2F3"),
        bottom=Side(style="thin", color="D9E2F3"),
    )

    for row_idx, record in enumerate(records, 2):
        row_data = [
            record.get("record_id", ""),
            record.get("judge_name", ""),
            record.get("judge_id", ""),
            record.get("judge_group", normalized_group),
            record.get("contestant_id", ""),
        ]
        if has_duration:
            row_data.append(record.get("duration", ""))
        for criterion_key in criteria:
            row_data.append(record.get("scores", {}).get(criterion_key, 0))
        raw_score = record.get("raw_score", record.get("total_score", 0))
        deduction_total = record.get("deduction_total", 0)
        row_data += [
            raw_score,
            deduction_total if deduction_total else "",
            record.get("total_score", 0),
            record.get("total_max", get_total_score(normalized_group)),
            record.get("timestamp", ""),
        ]
        for col_idx, value in enumerate(row_data, 1):
            cell = score_sheet.cell(row=row_idx, column=col_idx, value=value)
            cell.font = data_font
            cell.alignment = center_align
            cell.border = thin_border

    _apply_sheet_layout(score_sheet, headers, width_cap=30)
    score_sheet.column_dimensions["A"].width = 34

    audit_sheet = workbook.create_sheet(f"{normalized_group}提交审计")
    record_jsons = [
        json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        for record in records
    ]
    json_chunk_size = 30000
    max_json_chunks = max(
        1,
        max((len(value) + json_chunk_size - 1) // json_chunk_size for value in record_jsons),
    )
    audit_headers = [
        "提交ID",
        "裁判姓名",
        "裁判编号",
        "裁判组",
        "选手编号/姓名",
        "用时",
        "扣分明细",
        "自动归零说明",
        "总分归零",
        "总分归零项",
        "否决触发",
        "否决项",
        "评分时间",
    ] + [f"完整记录JSON-{index + 1}" for index in range(max_json_chunks)]
    _style_header(audit_sheet, audit_headers)

    for row_idx, (record, record_json) in enumerate(zip(records, record_jsons), 2):
        chunks = [
            record_json[start : start + json_chunk_size]
            for start in range(0, len(record_json), json_chunk_size)
        ] or [""]
        chunks += [""] * (max_json_chunks - len(chunks))
        row_data = [
            record.get("record_id", ""),
            record.get("judge_name", ""),
            record.get("judge_id", ""),
            record.get("judge_group", normalized_group),
            record.get("contestant_id", ""),
            record.get("duration", ""),
            _format_mapping(record.get("deductions")),
            _format_items(record.get("score_overrides")),
            "是" if record.get("score_zero_triggered") else "否",
            _format_items(record.get("score_zero_items")),
            "是" if record.get("veto_triggered") else "否",
            _format_items(record.get("veto_items")),
            record.get("timestamp", ""),
        ] + chunks
        for col_idx, value in enumerate(row_data, 1):
            cell = audit_sheet.cell(row=row_idx, column=col_idx, value=value)
            cell.font = data_font
            cell.alignment = Alignment(
                horizontal="left" if col_idx >= 7 else "center",
                vertical="top",
                wrap_text=col_idx >= 7,
            )
            cell.border = thin_border
        audit_sheet.row_dimensions[row_idx].height = 42

    _apply_sheet_layout(audit_sheet, audit_headers, width_cap=38)
    audit_sheet.column_dimensions["A"].width = 34
    for col_idx in range(7, 14):
        audit_sheet.column_dimensions[openpyxl.utils.get_column_letter(col_idx)].width = 38
    # 原始 JSON 用于完整取证，默认隐藏以保持审计表可读；需要时可在 Excel 中取消隐藏。
    for col_idx in range(14, len(audit_headers) + 1):
        dimension = audit_sheet.column_dimensions[
            openpyxl.utils.get_column_letter(col_idx)
        ]
        dimension.width = 20
        dimension.hidden = True

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = DATA_DIR / f"{normalized_group}_评分记录_{timestamp}.xlsx"
    workbook.save(file_path)
    return file_path


def export_all_to_excel() -> dict:
    """导出所有组的完整历史记录，返回 {组名: 文件路径}。"""
    results = {}
    for group in get_groups():
        file_path = export_to_excel(group)
        if file_path:
            results[group] = file_path
    return results
