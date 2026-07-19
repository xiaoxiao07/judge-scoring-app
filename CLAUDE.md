# 裁判评分系统 — 项目记忆

## 项目位置
C:\Users\lx\Desktop\judge-scoring-app
## 部署地址
https://judge-scoring-app-nusac.streamlit.app/

## 项目结构
- app.py — 主程序（页面路由 + UI + CSS 都在这里）
- utils/scoring.py — 评分标准定义
- utils/auth.py — 登录鉴权
- utils/data_manager.py — 数据存储 + Excel 导出
- data/ — 评分数据 JSON 文件（部署更新会丢失！注意备份）

## 裁判分组（4组）
1. 线上实操（70分）— 数字输入 + 用时 + 扣分项 + 否决项
2. 线下实操（70分）— 选钮点选评分，内容同线上实操
3. 线上答辩（100分）— 4项：大模型30+视觉30+机器人30+创新10，无扣分
4. 甘肃线下实操（100分）— 依据具身智能精密装配赛题评分细则，17项评分项
   - 语音交互12分 + 大模型任务卡解析34分 + 装配流程24分 + 装配精度30分
   - 数字输入 + 用时 + 7项扣分项（含中断次数输入）+ 5项否决项

## 管理密码
zpds2026

## 数据备份
每次 git push 部署新版本，data/ 目录会丢失。部署前先在管理页导出 Excel 备份。

## Git 推送（网络问题）
如果连不上 github.com，用代理：
git config --global http.proxy http://127.0.0.1:7890
git config --global https.proxy http://127.0.0.1:7890
git push
git config --global --unset http.proxy
git config --global --unset https.proxy
