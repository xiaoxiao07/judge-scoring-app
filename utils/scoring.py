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

# 实操组评分标准（总分100分）- 依据具身智能精密装配赛题评分细则
PRACTICAL_CRITERIA = {
    # 一、语音交互功能实现 (12分) — 仅 0/满分 两档按钮
    "唤醒与基础回应": {
        "max": 2,
        "description": "机器人支持语音唤醒功能，统一唤醒词为'小具同学'，唤醒后机器人需语音回应'我已就绪，请下达指令'",
        "module": "一、语音交互功能实现(12分)",
        "score_range": "0~2分",
        "options": [0, 2],
    },
    "具备下达指令触发识别任务卡能力": {
        "max": 2,
        "description": "语音交互功能应具备通过语音唤醒交互开展任务卡识别的功能",
        "module": "一、语音交互功能实现(12分)",
        "score_range": "0~2分",
        "options": [0, 2],
    },
    "语音提示任务已完成": {
        "max": 4,
        "description": "每次任务卡执行完成后，需语音提示'任务已完成'",
        "module": "一、语音交互功能实现(12分)",
        "score_range": "0~4分",
        "options": [0, 4],
    },
    "语音提示两个任务均已完成": {
        "max": 4,
        "description": "两个任务卡全部完成要语音播报告知'两个任务均已完成'",
        "module": "一、语音交互功能实现(12分)",
        "score_range": "0~4分",
        "options": [0, 4],
    },
    # 二、大模型任务卡解析 (34分)
    "任务卡视觉识别": {
        "max": 4,
        "description": "裁判随机抽取任务卡共2张，选手通过视觉实时展示视觉流程与识别结果（2分/张）",
        "module": "二、大模型任务卡解析(34分)",
        "score_range": "0~4分（2分/张，共2张）",
        "options": [0, 2, 4],
    },
    "大模型推理过程展示": {
        "max": 6,
        "description": "大模型解析过程展示实时带时间戳的大模型分析文本记录，推理过程清晰可见",
        "module": "二、大模型任务卡解析(34分)",
        "score_range": "0~6分",
        "options": [0, 6],
    },
    "任务卡1内容播报": {
        "max": 12,
        "description": "按照任务卡1的6个场景进行正确的语音播报（2分/场景）",
        "module": "二、大模型任务卡解析(34分)",
        "score_range": "0~12分（2分/场景，共6场景）",
        "options": list(range(13)),
    },
    "任务卡2内容播报": {
        "max": 12,
        "description": "按照任务卡2的6个装配顺序进行正确的语音播报（2分/顺序）",
        "module": "二、大模型任务卡解析(34分)",
        "score_range": "0~12分（2分/顺序，共6顺序）",
        "options": list(range(13)),
    },
    # 三、装配流程 (24分)
    "视觉识别结果": {
        "max": 12,
        "description": "视觉识别包括方块物料与托盘放置位置、颜色信息，共12个识别结果（1分/个）",
        "module": "三、装配流程(24分)",
        "score_range": "0~12分（1分/个，共12个识别结果）",
        "options": list(range(13)),
    },
    "抓取正确": {
        "max": 6,
        "description": "6个物料方块是否按照任务卡要求进行正确抓取（1分/个）",
        "module": "三、装配流程(24分)",
        "score_range": "0~6分（1分/个，共6个物料）",
        "options": list(range(7)),
    },
    "放置正确": {
        "max": 6,
        "description": "6个物料方块所放置托盘位置是否按照任务卡要求进行正确放置（1分/个）",
        "module": "三、装配流程(24分)",
        "score_range": "0~6分（1分/个，共6个物料）",
        "options": list(range(7)),
    },
    # 四、装配精度 (30分)
    "方块1装配精度": {
        "max": 5,
        "description": "方块1放置精度：0mm→5分，1mm→4.9分，2mm→4.7分，3mm→4.4分，4mm→3.5分，5mm→2.5分，5-10mm→2分，10-15mm→1分，15-20mm→0.5分，超出20mm记0分",
        "module": "四、装配精度(30分)",
        "score_range": "0~5分",
        "options": [
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
        ],
    },
    "方块2装配精度": {
        "max": 5,
        "description": "方块2放置精度（参照上方精度判定标准）",
        "module": "四、装配精度(30分)",
        "score_range": "0~5分",
        "options": [
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
        ],
    },
    "方块3装配精度": {
        "max": 5,
        "description": "方块3放置精度（参照上方精度判定标准）",
        "module": "四、装配精度(30分)",
        "score_range": "0~5分",
        "options": [
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
        ],
    },
    "方块4装配精度": {
        "max": 5,
        "description": "方块4放置精度（参照上方精度判定标准）",
        "module": "四、装配精度(30分)",
        "score_range": "0~5分",
        "options": [
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
        ],
    },
    "方块5装配精度": {
        "max": 5,
        "description": "方块5放置精度（参照上方精度判定标准）",
        "module": "四、装配精度(30分)",
        "score_range": "0~5分",
        "options": [
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
        ],
    },
    "方块6装配精度": {
        "max": 5,
        "description": "方块6放置精度：超出20mm圈定范围记0分（参照上方精度判定标准）",
        "module": "四、装配精度(30分)",
        "score_range": "0~5分",
        "options": [
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
        ],
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

