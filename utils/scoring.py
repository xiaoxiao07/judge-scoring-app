"""
评分标准定义模块
定义答辩组和实操组的评分项、分值范围及描述
"""

# 答辩组评分标准
DEFENSE_CRITERIA = {
    "内容完整性": {"max": 20, "description": "选手回答内容的完整程度"},
    "表达能力": {"max": 20, "description": "语言表达的流畅性和条理性"},
    "逻辑清晰度": {"max": 20, "description": "论证逻辑的严密性和清晰度"},
    "回答准确性": {"max": 20, "description": "对问题的回答准确程度"},
    "创新性": {"max": 20, "description": "观点或方法的新颖程度"},
}

# 实操组评分标准
PRACTICAL_CRITERIA = {
    "操作规范性": {"max": 25, "description": "操作流程的规范程度"},
    "完成度": {"max": 25, "description": "任务完成的完整程度"},
    "效率": {"max": 25, "description": "操作效率和用时控制"},
    "安全性": {"max": 25, "description": "操作过程中的安全意识"},
}

# 组别映射
GROUP_CRITERIA = {
    "答辩组": DEFENSE_CRITERIA,
    "实操组": PRACTICAL_CRITERIA,
}

# 各组总分
GROUP_TOTAL = {
    "答辩组": sum(c["max"] for c in DEFENSE_CRITERIA.values()),
    "实操组": sum(c["max"] for c in PRACTICAL_CRITERIA.values()),
}


def get_criteria(group: str) -> dict:
    """获取指定裁判组的评分标准"""
    return GROUP_CRITERIA.get(group, {})


def get_total_score(group: str) -> int:
    """获取指定裁判组的满分"""
    return GROUP_TOTAL.get(group, 0)


def get_groups() -> list:
    """获取所有裁判组列表"""
    return list(GROUP_CRITERIA.keys())
