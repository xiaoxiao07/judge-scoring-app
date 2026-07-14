"""
评分标准定义模块
定义答辩组、实操组和线上实操的评分项、分值范围及描述
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

# 线上实操评分标准（总分70分）- 依据 02仿真评分表.xlsx
ONLINE_CRITERIA = {
    # 一、大模型智能体解析 (30分)
    "大模型推理过程展示": {
        "max": 6,
        "description": "直观展示大模型分析过程（流式文本或时间戳日志），只放最终结果不得分",
        "module": "一、大模型智能体解析(30分)",
        "score_range": "0~6分（完整展示推理过程6分，展示部分过程3~5分，只放结果0分）",
    },
    "任务一：场景语义解析": {
        "max": 12,
        "description": "大模型接收任务卡1识别结果，正确理解场景语义并输出解析文本。共一张图六个物品，每个物品两分",
        "module": "一、大模型智能体解析(30分)",
        "score_range": "0~12分（每个物品正确识别0~2分，共6个物品）",
    },
    "任务二：指令提取与步骤输出": {
        "max": 12,
        "description": "大模型精准提取任务卡2指令顺序，输出规范中文步骤及触发字符。共六步骤，每步骤两分",
        "module": "一、大模型智能体解析(30分)",
        "score_range": "0~12分（每步骤0~2分，共6步骤）",
        "deduction_key": "任务2指令提取顺序错误",
    },
    # 二、VM视觉流程与数据协议 (20分)
    "视觉流程运行状态": {
        "max": 8,
        "description": "VM软件流程流畅运行无报错，界面展示识别逻辑状态，并且展示VM软件接收到的数据，证明通讯成功",
        "module": "二、VM视觉流程与数据协议(20分)",
        "score_range": "0~8分（流程流畅无报错、展示接收数据8分，有瑕疵酌情扣分）",
    },
    "固定数据格式与数值输出": {
        "max": 12,
        "description": "VM运行完毕，界面明确显示发送了协议表规定的#0;X;Y;RZ数据。格式错或数值伪造扣分。共六步骤，每步骤两分",
        "module": "二、VM视觉流程与数据协议(20分)",
        "score_range": "0~12分（每步骤0~2分，共6步骤）",
        "deduction_key": "VM发送数据格式不符",
    },
    # 三、机器人仿真动作与闭环 (20分)
    "数据接收与代码响应": {
        "max": 8,
        "description": "必须在机器人仿真软件展示主页日志区，实时打印出接收到的VM数据或触发字符，证明通讯闭环",
        "module": "三、机器人仿真动作与闭环(20分)",
        "score_range": "0~8分（日志区实时显示接收数据8分，缺失酌情扣分）",
    },
    "初始位姿偏移与复位": {
        "max": 12,
        "description": "机器人仿真软件主页3D画面中，机械臂基于固定的初始位姿偏移执行动作；每步后必须清晰回归初始位姿再执行下一步。共六步骤，每步骤两分",
        "module": "三、机器人仿真动作与闭环(20分)",
        "score_range": "0~12分（每步骤0~2分，共6步骤）",
        "deduction_key": "机械臂未按规定位姿",
    },
}

# 线上实操扣分项
ONLINE_DEDUCTIONS = {
    "大模型界面只显示最终指令": {
        "deduct": 6,
        "description": "大模型界面只显示最终指令，无法展示推理思考过程（扣除6分）",
    },
    "VM软件通讯界面无数据": {
        "deduct": 8,
        "description": "VM软件通讯界面没有收到字符数据，通讯失败（扣除8分）",
    },
    "机器人日志区无数据": {
        "deduct": 8,
        "description": "机器人仿真软件日志区没有收到VM发送的固定数据，通讯失败（扣除8分）",
    },
    "任务2指令提取顺序错误": {
        "deduct": "half",
        "description": "任务2指令提取顺序错误，或输出步骤缺少触发字符/执行状态（每步扣除一半分数）",
    },
    "VM发送数据格式不符": {
        "deduct": "half",
        "description": "VM发送数据格式不含#前缀，或X,Y,RZ数值与协议表规定不符（每步扣除一半分数）",
    },
    "机械臂未按规定位姿": {
        "deduct": "half",
        "description": "机械臂未从规定初始位姿出发，或每步执行后未回到初始位姿（每步扣除一半分数）",
    },
    "机器人仿真动画不直观": {
        "deduct": 8,
        "description": "机器人仿真动画展示不直观（扣除8分）",
    },
    "屏幕共享未设置时钟": {
        "deduct": 10,
        "description": "仿真演示环节屏幕共享没有设置时钟（扣除10分）",
    },
}

# 线上实操否决项（演示环节计0分）
ONLINE_VETO = {
    "日志区无数据/硬编码伪装": {
        "description": "机器人仿真软件自带的日志区无数据接收日志，或大模型交互界面被证实为纯文本硬编码伪装",
    },
    "播放预设轨迹动画": {
        "description": "VM输出的坐标数据与机器人接收数据逻辑脱节，确认为播放预设轨迹动画",
    },
}

# 组别映射
GROUP_CRITERIA = {
    "答辩组": DEFENSE_CRITERIA,
    "实操组": PRACTICAL_CRITERIA,
    "线上实操": ONLINE_CRITERIA,
}

# 各组总分
GROUP_TOTAL = {
    "答辩组": sum(c["max"] for c in DEFENSE_CRITERIA.values()),
    "实操组": sum(c["max"] for c in PRACTICAL_CRITERIA.values()),
    "线上实操": sum(c["max"] for c in ONLINE_CRITERIA.values()),
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


def get_deductions(group: str) -> dict:
    """获取扣分项定义（目前仅线上实操有）"""
    if group == "线上实操":
        return ONLINE_DEDUCTIONS
    return {}


def get_veto(group: str) -> dict:
    """获取否决项定义（目前仅线上实操有）"""
    if group == "线上实操":
        return ONLINE_VETO
    return {}
