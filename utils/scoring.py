"""
评分标准定义模块。

对外提供“答辩组”“实操组”和“北京线上实操组”；旧名称仅用于兼容
已经保存的裁判信息和自动登录链接。
"""

import math


def normalize_score_number(value):
    """将评分数值统一到一位小数，并把整数结果保存为 int。"""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return value
    numeric_value = float(value)
    if not math.isfinite(numeric_value):
        raise ValueError("评分数值必须是有限数字")
    rounded_value = round(numeric_value, 1)
    if rounded_value == 0:
        rounded_value = 0.0
    if rounded_value.is_integer():
        return int(rounded_value)
    return rounded_value


# 答辩组评分标准（总分100分）- 依据 01答辩打分表end.xlsx
DEFENSE_CRITERIA = {
    "大模型思路讲解/语音交互方案": {
        "max": 30,
        "description": "讲解大模型解析思路、智能体设计及语音交互方案",
        "score_range": "0~30分",
    },
    "视觉流程": {
        "max": 30,
        "description": "讲解VisionMaster视觉流程设计与数据协议实现",
        "score_range": "0~30分",
    },
    "机器人控制": {
        "max": 30,
        "description": "讲解机器人控制逻辑与仿真运动方案",
        "score_range": "0~30分",
    },
    "创新性/答辩流畅": {
        "max": 10,
        "description": "方案创新性、答辩表达流畅度与时间把控",
        "score_range": "0~10分",
    },
}

# 实操组评分标准（总分100分）
# 依据《仿真操作打分表》和《具身智能精密装配赛题评分细则》，
# 第二、第三部分按评分表小项汇总列出，裁判直接点选该小项得分。
VOICE_MODULE = "一、语音交互功能实现（12分）"
TASK_CARD_MODULE = "二、大模型任务卡解析（34分）"
ASSEMBLY_MODULE = "三、装配流程（24分）"
PRECISION_MODULE = "四、装配精度（30分）"

PRECISION_OPTIONS = [
    {"label": "0mm → 5分", "value": 5},
    {"label": "1mm → 4.9分", "value": 4.9},
    {"label": "2mm → 4.7分", "value": 4.7},
    {"label": "3mm → 4.4分", "value": 4.4},
    {"label": "4mm → 3.5分", "value": 3.5},
    {"label": "5mm → 2.5分", "value": 2.5},
    {"label": "5-10mm → 2分", "value": 2},
    {"label": "10-15mm → 1分", "value": 1},
    {"label": "15-20mm → 0.5分", "value": 0.5},
    {"label": ">20mm → 0分", "value": 0},
]


def _score_item(
    max_score,
    module,
    options,
    submodule=None,
    display_name=None,
    inline_deduction=None,
):
    """构造一个只通过按钮点选的实操得分项。"""
    item = {
        "max": max_score,
        "module": module,
        "options": options,
    }
    if submodule:
        item["submodule"] = submodule
    if display_name:
        item["display_name"] = display_name
    if inline_deduction:
        item["inline_deduction"] = inline_deduction
    return item


PRACTICAL_CRITERIA = {
    # 一、语音交互功能实现（4个得分项）
    "唤醒与基础回应": _score_item(2, VOICE_MODULE, [0, 2]),
    "具备下达指令触发识别任务卡能力": _score_item(
        2, VOICE_MODULE, [0, 2]
    ),
    "语音提示任务已完成": _score_item(4, VOICE_MODULE, [0, 4]),
    "语音提示两个任务均已完成": _score_item(4, VOICE_MODULE, [0, 4]),

    # 二、大模型任务卡解析（4个汇总得分项）
    "任务卡视觉识别": _score_item(
        4, TASK_CARD_MODULE, [0, 2, 4]
    ),
    "大模型推理过程展示": _score_item(
        6, TASK_CARD_MODULE, [0, 6]
    ),
    "任务卡1内容播报": _score_item(
        12, TASK_CARD_MODULE, list(range(0, 13, 2))
    ),
    "任务卡2内容播报": _score_item(
        12, TASK_CARD_MODULE, list(range(0, 13, 2))
    ),

    # 三、装配流程（3个汇总得分项）
    "视觉识别结果": _score_item(
        12, ASSEMBLY_MODULE, list(range(13))
    ),
    "抓取正确": _score_item(
        6, ASSEMBLY_MODULE, list(range(7))
    ),
    "放置正确": _score_item(
        6, ASSEMBLY_MODULE, list(range(7))
    ),

    # 四、装配精度（6个方块分别记录偏移位置）
    **{
        f"方块{index}装配精度": _score_item(
            5,
            PRECISION_MODULE,
            PRECISION_OPTIONS,
            submodule="物料方块偏移精度（5分/个，共6个方块）",
            display_name=f"方块{index}",
        )
        for index in range(1, 7)
    },
}

# 实操组扣分项（依据具身智能精密装配赛题打分表）
# per_count：输入发生次数并按 deduct 自动计算；其余模式使用按钮选择。
PRACTICAL_DEDUCTIONS = {
    "使用文本输入功能": {
        "deduct": 3,
        "mode": "per_count",
        "description": "每条文本输入指令扣3分",
    },
    "碰撞扣分": {
        "deduct": 1,
        "mode": "per_count",
        "description": "每次碰撞扣1分，每个装配流程最多扣1分",
    },
    "人为辅助机器人/智能体识别": {
        "deduct": 0,
        "mode": "task_card_override",
        "description": "选择被人为辅助识别的任务卡，并自动清零对应得分",
    },
    "二次调整": {
        "deduct": 5,
        "mode": "per_count",
        "description": "每次二次调整扣5分",
    },
    "人为介入装配环节": {
        "deduct": 0,
        "mode": "assembly_override",
        "description": "选择介入后，装配流程和装配精度均记0分",
    },
    "中断": {
        "deduct": 5,
        "mode": "per_count",
        "description": "每次中断扣5分，扣完为止",
    },
    "示教": {
        "deduct": 50,
        "mode": "binary_deduct",
        "description": "使用示教方式扣50分",
    },
    "使用非指定方式输入指令": {
        "deduct": 0,
        "mode": "score_zero",
        "description": "选择后总分记0分",
    },
    "误删系统文件": {
        "deduct": 0,
        "mode": "score_zero",
        "description": "选择后总分记0分",
    },
}

TASK_CARD_1_BROADCAST_CRITERIA = ("任务卡1内容播报",)
TASK_CARD_2_BROADCAST_CRITERIA = ("任务卡2内容播报",)
ASSEMBLY_AND_PRECISION_CRITERIA = tuple(
    name
    for name, item in PRACTICAL_CRITERIA.items()
    if item["module"] in (ASSEMBLY_MODULE, PRECISION_MODULE)
)


def apply_practical_score_overrides(
    scores: dict,
    auxiliary_task_card: str = "",
    assembly_intervened: bool = False,
) -> tuple[dict, list]:
    """应用任务卡辅助识别和人为介入装配对应的强制归零规则。"""
    adjusted_scores = dict(scores)
    override_notes = []

    def zero_scores(criteria_names, note):
        for criterion_name in criteria_names:
            adjusted_scores[criterion_name] = 0
        if note not in override_notes:
            override_notes.append(note)

    if auxiliary_task_card in ("任务卡1", "任务卡1及任务卡2"):
        zero_scores(TASK_CARD_1_BROADCAST_CRITERIA, "任务卡1内容播报")

    if auxiliary_task_card in ("任务卡2", "任务卡1及任务卡2"):
        zero_scores(TASK_CARD_2_BROADCAST_CRITERIA, "任务卡2内容播报")
        zero_scores(
            ASSEMBLY_AND_PRECISION_CRITERIA,
            "第三部分装配流程与第四部分装配精度（任务卡2辅助识别）",
        )

    if assembly_intervened:
        zero_scores(
            ASSEMBLY_AND_PRECISION_CRITERIA,
            "第三部分装配流程与第四部分装配精度（人为介入）",
        )

    return adjusted_scores, override_notes

# 实操组否决项（勾选后总分归零）
PRACTICAL_VETO = {
    "作弊/大碰撞/破坏物品": {
        "description": "求助于场外人员、机器人发生较大碰撞导致自锁急停、对参赛区域内物品暴力使用或破坏，取消比赛资格",
    },
    "伪装作弊": {
        "description": "通过伪装手段掩盖违规行为，全部分数扣除计0分",
    },
}

# 北京线上实操组评分标准（总分70分）
# 依据桌面《仿真操作打分表-lx.xlsx》：12分项目按6个步骤、每步2分点选。
BEIJING_MODEL_MODULE = "一、大模型智能体（30分）"
BEIJING_VISION_MODULE = "二、VM视觉（20分）"
BEIJING_ROBOT_MODULE = "三、机器人仿真（20分）"
BEIJING_STEP_OPTIONS = list(range(0, 13, 2))
BEIJING_DEDUCTION_OPTIONS = list(range(13))

BEIJING_ONLINE_CRITERIA = {
    "推理过程展示": _score_item(
        6, BEIJING_MODEL_MODULE, [0, 6]
    ),
    "任务一": _score_item(
        12, BEIJING_MODEL_MODULE, BEIJING_STEP_OPTIONS
    ),
    "任务二": _score_item(
        12,
        BEIJING_MODEL_MODULE,
        BEIJING_STEP_OPTIONS,
        inline_deduction="任务二步骤扣分",
    ),
    "视觉流程": _score_item(
        8, BEIJING_VISION_MODULE, [0, 8]
    ),
    "格式数值输出": _score_item(
        12,
        BEIJING_VISION_MODULE,
        BEIJING_STEP_OPTIONS,
        inline_deduction="格式数据输出步骤扣分",
    ),
    "数据接收": _score_item(
        8, BEIJING_ROBOT_MODULE, [0, 8]
    ),
    "偏移与复位": _score_item(
        12,
        BEIJING_ROBOT_MODULE,
        BEIJING_STEP_OPTIONS,
        inline_deduction="偏移与复位步骤扣分",
    ),
}

BEIJING_ONLINE_DEDUCTIONS = {
    "任务二步骤扣分": {
        "deduct": 1,
        "mode": "inline_amount",
        "options": BEIJING_DEDUCTION_OPTIONS,
        "score_target": "任务二",
    },
    "格式数据输出步骤扣分": {
        "deduct": 1,
        "mode": "inline_amount",
        "options": BEIJING_DEDUCTION_OPTIONS,
        "score_target": "格式数值输出",
    },
    "偏移与复位步骤扣分": {
        "deduct": 1,
        "mode": "inline_amount",
        "options": BEIJING_DEDUCTION_OPTIONS,
        "score_target": "偏移与复位",
    },
    "仿真动画展示不直观": {
        "deduct": 8,
        "mode": "binary_deduct",
        "inactive_label": "未发生",
        "active_label": "发生（扣8分）",
    },
    "初始位姿设置错误": {
        "deduct": 5,
        "mode": "binary_deduct",
        "inactive_label": "未发生",
        "active_label": "发生（扣5分）",
    },
    "屏幕共享没有设置时钟": {
        "deduct": 10,
        "mode": "binary_deduct",
        "inactive_label": "未发生",
        "active_label": "发生（扣10分）",
    },
    "中断扣分": {
        "deduct": 5,
        "mode": "per_count",
        "description": "每次中断扣5分",
    },
}

BEIJING_ONLINE_VETO = {
    "纯文本硬编码伪装": {
        "description": "大模型交互界面被证实为纯文本硬编码伪装",
    },
    "数据逻辑脱节/预设动画": {
        "description": "VM输出数据与机器人动作逻辑脱节，或播放预设轨迹动画",
    },
}

PRACTICAL_GROUPS = ("实操组", "北京线上实操组")

# 旧组名兼容映射。“线上实操”沿用相同的70分规则进入北京线上实操组。
GROUP_ALIASES = {
    "线上答辩": "答辩组",
    "甘肃线下实操": "实操组",
    "线上实操": "北京线上实操组",
}


def normalize_group(group: str) -> str:
    """将历史组名转换为当前组名。"""
    return GROUP_ALIASES.get(group, group)


def is_practical_group(group: str) -> bool:
    """判断组别是否使用实操评分、完成时间和实操导出格式。"""
    return normalize_group(group) in PRACTICAL_GROUPS


# 当前对外开放的组别映射
GROUP_CRITERIA = {
    "答辩组": DEFENSE_CRITERIA,
    "实操组": PRACTICAL_CRITERIA,
    "北京线上实操组": BEIJING_ONLINE_CRITERIA,
}

# 各组总分
GROUP_TOTAL = {
    "答辩组": sum(c["max"] for c in DEFENSE_CRITERIA.values()),
    "实操组": sum(c["max"] for c in PRACTICAL_CRITERIA.values()),
    "北京线上实操组": sum(c["max"] for c in BEIJING_ONLINE_CRITERIA.values()),
}


def get_criteria(group: str) -> dict:
    """获取指定裁判组的评分标准"""
    return GROUP_CRITERIA.get(normalize_group(group), {})


def get_total_score(group: str) -> int:
    """获取指定裁判组的满分"""
    return GROUP_TOTAL.get(normalize_group(group), 0)


def get_groups() -> list:
    """获取所有裁判组列表"""
    return list(GROUP_CRITERIA.keys())


def get_deductions(group: str) -> dict:
    """获取扣分项定义"""
    normalized_group = normalize_group(group)
    if normalized_group == "实操组":
        return PRACTICAL_DEDUCTIONS
    if normalized_group == "北京线上实操组":
        return BEIJING_ONLINE_DEDUCTIONS
    return {}


def calculate_deduction_total(group: str, scores: dict, deductions: dict):
    """计算有效扣分；内嵌步骤扣分不能超过其对应得分项的当前得分。"""
    deduction_definitions = get_deductions(group)
    total = 0

    for deduction_name, selected_amount in (deductions or {}).items():
        if isinstance(selected_amount, bool) or not isinstance(
            selected_amount, (int, float)
        ):
            continue

        effective_amount = max(0, selected_amount)
        definition = deduction_definitions.get(deduction_name, {})
        if definition.get("mode") == "inline_amount":
            score_target = definition.get("score_target")
            target_score = (scores or {}).get(score_target, 0)
            if isinstance(target_score, bool) or not isinstance(
                target_score, (int, float)
            ):
                target_score = 0
            effective_amount = min(effective_amount, max(0, target_score))

        total += effective_amount

    return normalize_score_number(total)


def get_veto(group: str) -> dict:
    """获取否决项定义"""
    normalized_group = normalize_group(group)
    if normalized_group == "实操组":
        return PRACTICAL_VETO
    if normalized_group == "北京线上实操组":
        return BEIJING_ONLINE_VETO
    return {}
