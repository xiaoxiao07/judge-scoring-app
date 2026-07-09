# 裁判评分系统 🏅

基于 Streamlit 的裁判评分 Web 应用，支持答辩组和实操组两类裁判在线评分。

## 功能

- **裁判登录**：姓名 + 编号 + 组别选择，支持一键重新登录
- **分组评分**：
  - 答辩组：内容完整性(0-20)、表达能力(0-20)、逻辑清晰度(0-20)、回答准确性(0-20)、创新性(0-20)
  - 实操组：操作规范性(0-25)、完成度(0-25)、效率(0-25)、安全性(0-25)
- **数据记录**：所有评分自动保存，支持实时查看
- **Excel 导出**：一键导出评分记录为 Excel 文件
- **移动端适配**：手机浏览器即可使用

## 快速开始

### 本地运行

```bash
# 安装依赖
pip install -r requirements.txt

# 启动应用
streamlit run app.py
```

### 部署到 Streamlit Cloud

1. 将代码推送到 GitHub 仓库
2. 访问 https://share.streamlit.io/
3. 点击 "New app" → 选择仓库 → Deploy

## 管理后台

访问管理页面需要密码，默认密码：`admin123`

## 技术栈

- Python 3.13
- Streamlit
- openpyxl
- pandas
