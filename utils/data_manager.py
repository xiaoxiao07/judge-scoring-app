"""
数据存储管理模块
负责 JSON 数据的读写、Excel 导出、数据文件初始化
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

from .scoring import get_criteria, get_total_score, get_groups

# 数据目录
DATA_DIR = Path(__file__).parent.parent / "data"

# 裁判信息文件
JUDGES_FILE = DATA_DIR / "judges.json"

# 评分记录文件（每组一个文件）
SCORE_FILES = {
    "答辩组": DATA_DIR / "scores_答辩组.json",
    "实操组": DATA_DIR / "scores_实操组.json",
    "线上赛": DATA_DIR / "scores_线上赛.json",
}


def init_data_files():
    """
    初始化数据文件和目录
    在程序启动时调用，确保所有必需的数据文件存在
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # 初始化裁判信息文件
    if not JUDGES_FILE.exists():
        _write_json(JUDGES_FILE, [])

    # 初始化各组评分记录文件
    for group in get_groups():
        if group not in SCORE_FILES:
            continue
        if not SCORE_FILES[group].exists():
            _write_json(SCORE_FILES[group], [])


def _read_json(file_path: Path) -> list:
    """读取 JSON 文件"""
    if not file_path.exists():
        return []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def _write_json(file_path: Path, data: list):
    """写入 JSON 文件"""
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ===================== 裁判管理 =====================


def register_judge(name: str, judge_id: str, group: str) -> dict:
    """
    注册裁判（如已存在则更新）
    返回裁判信息字典
    """
    judges = _read_json(JUDGES_FILE)

    # 检查是否已存在
    for j in judges:
        if j["judge_id"] == judge_id:
            # 更新信息
            j["name"] = name
            j["group"] = group
            _write_json(JUDGES_FILE, judges)
            return j

    # 新增裁判
    import hashlib

    token = hashlib.sha256(f"{name}|{judge_id}".encode()).hexdigest()[:12]
    judge_info = {
        "name": name,
        "judge_id": judge_id,
        "group": group,
        "token": token,
    }
    judges.append(judge_info)
    _write_json(JUDGES_FILE, judges)
    return judge_info


def find_judge_by_token(token: str) -> Optional[dict]:
    """根据 token 查找裁判信息"""
    judges = _read_json(JUDGES_FILE)
    for j in judges:
        if j.get("token") == token:
            return j
    return None


def find_judge_by_id(judge_id: str) -> Optional[dict]:
    """根据编号查找裁判信息"""
    judges = _read_json(JUDGES_FILE)
    for j in judges:
        if j["judge_id"] == judge_id:
            return j
    return None


def get_all_judges() -> list:
    """获取所有已注册裁判"""
    return _read_json(JUDGES_FILE)


# ===================== 评分记录管理 =====================


def save_score(
    judge_info: dict,
    contestant_id: str,
    scores: dict,
    deductions: Optional[dict] = None,
    final_score: Optional[int] = None,
    veto_triggered: bool = False,
    veto_items: Optional[list] = None,
) -> dict:
    """
    保存一条评分记录
    返回保存的记录字典
    """
    group = judge_info["group"]
    file_path = SCORE_FILES.get(group)
    if not file_path:
        raise ValueError(f"未知的裁判组: {group}")

    records = _read_json(file_path)
    criteria = get_criteria(group)
    total_max = get_total_score(group)
    score_total = sum(scores.values())

    record = {
        "judge_name": judge_info["name"],
        "judge_id": judge_info["judge_id"],
        "judge_group": group,
        "contestant_id": contestant_id,
        "scores": {k: int(v) for k, v in scores.items()},
        "total_score": final_score if final_score is not None else score_total,
        "raw_score": score_total,
        "total_max": total_max,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    if deductions:
        record["deductions"] = deductions
        record["deduction_total"] = sum(
            v for v in deductions.values() if isinstance(v, (int, float))
        )
    if veto_triggered:
        record["veto_triggered"] = True
        record["veto_items"] = veto_items or []

    records.append(record)
    _write_json(file_path, records)
    return record


def get_all_scores(group: str) -> list:
    """获取某组的所有评分记录"""
    file_path = SCORE_FILES.get(group)
    if not file_path:
        return []
    return _read_json(file_path)


# ===================== Excel 导出 =====================


def _style_header(ws, headers: list, row: int = 1):
    """设置表头样式"""
    header_font = Font(bold=True, size=11, color="FFFFFF")
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    thin_border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )

    for col_idx, header in enumerate(headers, 1):
        cell = ws.cell(row=row, column=col_idx, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
        cell.border = thin_border


def export_to_excel(group: str) -> Optional[Path]:
    """
    将某组评分记录导出为 Excel 文件
    返回文件路径
    """
    records = get_all_scores(group)
    if not records:
        return None

    criteria = get_criteria(group)
    has_deductions = any("deductions" in r for r in records)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"{group}评分记录"

    # 构建表头
    score_headers = [f"{k}({v['max']})" for k, v in criteria.items()]
    headers = ["裁判姓名", "裁判编号", "裁判组", "选手编号/姓名"] + score_headers + ["原始总分", "扣分", "最终总分", "评分时间"]

    _style_header(ws, headers)

    # 填充数据
    data_font = Font(size=11)
    center_align = Alignment(horizontal="center", vertical="center")
    thin_border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )

    for row_idx, record in enumerate(records, 2):
        row_data = [
            record["judge_name"],
            record["judge_id"],
            record["judge_group"],
            record["contestant_id"],
        ]
        # 各评分项得分
        for criterion_key in criteria:
            row_data.append(record["scores"].get(criterion_key, 0))
        # 原始总分、扣分、最终总分、评分时间
        raw_score = record.get("raw_score", record["total_score"])
        deduction_total = record.get("deduction_total", 0)
        row_data.append(raw_score)
        row_data.append(deduction_total if deduction_total else "")
        row_data.append(record["total_score"])
        row_data.append(record["timestamp"])

        for col_idx, value in enumerate(row_data, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            cell.font = data_font
            cell.alignment = center_align
            cell.border = thin_border

    # 自动调整列宽
    for col_idx in range(1, len(headers) + 1):
        header_text = headers[col_idx - 1]
        # 计算合适的列宽（中文字符按2个宽度计算）
        width = sum(2 if ord(c) > 127 else 1 for c in header_text) + 2
        ws.column_dimensions[openpyxl.utils.get_column_letter(col_idx)].width = max(width, 10)

    # 保存到 data 目录
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = DATA_DIR / f"{group}_评分记录_{timestamp}.xlsx"
    wb.save(file_path)
    return file_path


def export_all_to_excel() -> dict:
    """导出所有组的评分记录，返回 {组名: 文件路径} 字典"""
    results = {}
    for group in get_groups():
        file_path = export_to_excel(group)
        if file_path:
            results[group] = file_path
    return results
