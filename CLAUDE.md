# 裁判评分系统 — 项目记忆

## 项目位置
C:\Users\lx\Desktop\judge-scoring-app
## 部署地址
https://judge-scoring-app-nusac.streamlit.app/

## 项目结构
- app.py — 主程序（页面路由 + UI + CSS 都在这里）
- utils/scoring.py — 评分标准定义
- utils/auth.py — 登录鉴权
- utils/data_manager.py — 数据存储 + Excel 导出 + GitHub 持久化同步
- data/ — 评分数据 JSON 文件（通过 GitHub API 自动持久化）
- .streamlit/secrets.example.toml — GitHub Token 配置模板

## 裁判分组（4组）
1. 线上实操（70分）— 数字输入 + 用时 + 扣分项 + 否决项
2. 线下实操（70分）— 选钮点选评分，内容同线上实操
3. 线上答辩（100分）— 4项：大模型30+视觉30+机器人30+创新10，无扣分
4. 甘肃线下实操（100分）— 依据具身智能精密装配赛题评分细则，17项评分项
   - 语音交互12分 + 大模型任务卡解析34分 + 装配流程24分 + 装配精度30分
   - 数字输入 + 用时 + 7项扣分项（含中断次数输入）+ 5项否决项

## 管理密码
zpds2026

## 数据持久化（2026-07-19 新增）
- 每次提交评分后自动通过 GitHub API 推送到仓库
- 每次应用启动时从 GitHub raw 拉取最新数据
- 需要配置 GitHub Personal Access Token（见下方说明）
- 未配置 token 时仍可本地使用（不回丢失已有功能）

## GitHub Token 配置
1. 创建 token：GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens
2. 权限：只选 Contents (Read and write)，仓库选择 xiaoxiao07/judge-scoring-app
3. 本地测试：复制 .streamlit/secrets.example.toml 为 .streamlit/secrets.toml，填入 token
4. 部署配置：Streamlit Cloud → App settings → Secrets → 填入 GITHUB_TOKEN = "xxx"

## Git 推送（网络问题）
如果连不上 github.com，用代理：
git config --global http.proxy http://127.0.0.1:7890
git config --global https.proxy http://127.0.0.1:7890
git push
git config --global --unset http.proxy
git config --global --unset https.proxy
