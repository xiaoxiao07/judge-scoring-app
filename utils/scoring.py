"""
评分标准定义模块。

对外仅提供“答辩组”和“实操组”两个裁判分组；旧名称仅用于兼容
已经保存的裁判信息和自动登录链接。
"""

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
# 每个可独立判分的对象均单列一行，裁判只需点选该点允许的分值。
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


def _score_item(max_score, module, options, submodule=None, display_name=None):
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
    return item


PRACTICAL_CRITERIA = {
    # 一、语音交互功能实现（4个独立得分点）
    "唤醒与基础回应": _score_item(2, VOICE_MODULE, [0, 2]),
    "具备下达指令触发识别任务卡能力": _score_item(
        2, VOICE_MODULE, [0, 2]
    ),
    "语音提示任务已完成": _score_item(4, VOICE_MODULE, [0, 4]),
    "语音提示两个任务均已完成": _score_item(4, VOICE_MODULE, [0, 4]),

    # 二、大模型任务卡解析（2张任务卡 + 1个推理过程 + 12个播报点）
    "任务卡1视觉识别": _score_item(
        2,
        TASK_CARD_MODULE,
        [0, 2],
        submodule="任务卡视觉识别（2分/张，共2张）",
        display_name="任务卡1",
    ),
    "任务卡2视觉识别": _score_item(
        2,
        TASK_CARD_MODULE,
        [0, 2],
        submodule="任务卡视觉识别（2分/张，共2张）",
        display_name="任务卡2",
    ),
    "大模型推理过程展示": _score_item(
        6,
        TASK_CARD_MODULE,
        [0, 6],
        submodule="大模型推理过程展示（6分）",
    ),
    **{
        f"任务卡1场景{index}内容播报": _score_item(
            2,
            TASK_CARD_MODULE,
            [0, 2],
            submodule="任务卡1内容播报（2分/场景，共6个场景）",
            display_name=f"场景{index}",
        )
        for index in range(1, 7)
    },
    **{
        f"任务卡2顺序{index}内容播报": _score_item(
            2,
            TASK_CARD_MODULE,
            [0, 2],
            submodule="任务卡2内容播报（2分/顺序，共6个顺序）",
            display_name=f"顺序{index}",
        )
        for index in range(1, 7)
    },

    # 三、装配流程（12个识别结果 + 6次抓取 + 6次放置）
    **{
        f"视觉识别结果{index}": _score_item(
            1,
            ASSEMBLY_MODULE,
            [0, 1],
            submodule="视觉识别（1分/个，共12个识别结果）",
            display_name=f"识别结果{index}",
        )
        for index in range(1, 13)
    },
    **{
        f"方块{index}抓取正确": _score_item(
            1,
            ASSEMBLY_MODULE,
            [0, 1],
            submodule="抓取正确（1分/个，共6个方块）",
            display_name=f"方块{index}",
        )
        for index in range(1, 7)
    },
    **{
        f"方块{index}放置正确": _score_item(
            1,
            ASSEMBLY_MODULE,
            [0, 1],
            submodule="放置正确（1分/个，共6个方块）",
            display_name=f"方块{index}",
        )
        for index in range(1, 7)
    },

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
PRACTICAL_DEDUCTIONS = {
    "使用文本输入功能": {
        "deduct": 3,
        "description": "使用文本输入功能进行交互，每条指令扣3分",
    },
    "碰撞扣分": {
        "deduct": 1,
        "description": "物料方块抓取与放置过程中发生碰撞刮碰，每次扣1分，每次装配最多扣1分",
    },
    "人为辅助机器人/智能体识别": {
        "deduct": 34,
        "description": "参赛选手通过人为介入方式辅助机器人或智能体实现识别，该任务卡对应任务计0分",
    },
    "二次调整": {
        "deduct": 5,
        "description": "物料方块放置后仍通过程序控制机器人调整位置，或后续装配动作中改变已装配方块位置，每次扣除5分",
    },
    "人为介入装配环节": {
        "deduct": 54,
        "description": "通过人为介入方式移动托盘或物料方块位置，装配流程(24分)与装配精度(30分)得分记为0分",
    },
    "中断": {
        "deduct": 5,
        "mode": "per_step",
        "description": "操作过程中由于自身原因导致装配中断（不含碰撞），每次扣5分，扣完为止",
    },
    "示教": {
        "deduct": 50,
        "description": "未使用相机，仅采用示教方式安装零件，扣50分",
    },
    "使用非指定方式输入指令": {
        "deduct": 100,
        "mode": "score_zero",
        "description": "使用按键、触摸屏、串口等非指定方式输入指令，总分计0分",
    },
    "误删系统文件": {
        "deduct": 100,
        "mode": "score_zero",
        "description": "调试期间误删机器人系统文件导致系统崩溃，总分计0分",
    },
}

# 实操组否决项（勾选后总分归零）
PRACTICAL_VETO = {
    "作弊/大碰撞/破坏物品": {
        "description": "求助于场外人员、机器人发生较大碰撞导致自锁急停、对参赛区域内物品暴力使用或破坏，取消比赛资格",
    },
    "伪装作弊": {
        "description": "通过伪装手段掩盖违规行为，全部分数扣除计0分",
    },
}

# 旧组名兼容映射。已删除的“线上实操”和“线下实操”不再映射。
GROUP_ALIASES = {
    "线上答辩": "答辩组",
    "甘肃线下实操": "实操组",
}


def normalize_group(group: str) -> str:
    """将历史组名转换为当前组名。"""
    return GROUP_ALIASES.get(group, group)


# 当前对外开放的组别映射
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
    return GROUP_CRITERIA.get(normalize_group(group), {})


def get_total_score(group: str) -> int:
    """获取指定裁判组的满分"""
    return GROUP_TOTAL.get(normalize_group(group), 0)


def get_groups() -> list:
    """获取所有裁判组列表"""
    return list(GROUP_CRITERIA.keys())


def get_deductions(group: str) -> dict:
    """获取扣分项定义"""
    if normalize_group(group) == "实操组":
        return PRACTICAL_DEDUCTIONS
    return {}


def get_veto(group: str) -> dict:
    """获取否决项定义"""
    if normalize_group(group) == "实操组":
        return PRACTICAL_VETO
    return {}
