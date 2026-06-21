# 立夏期末复习特训工作台

这个仓库用于把二年级下学期语文、数学课本和试题照片整理成“期末冲刺复习系统”。

当前公开页面只保留新版入口：

- `docs/index.html`
- `docs/sprint/index.html`

旧版的知识点总览、错题页、知识库节选和下载页已经转入本地 `private_archive/`，不再从 GitHub Pages 当前站点发布。

## 隐私与版权规则

- 原始照片不提交到 GitHub。
- 孩子姓名、学校、班级、学号等信息需要在公开页面中脱敏。
- 课本原文的完整 OCR 结果只在本地保存；公开页面只发布脱敏后的复习摘要、错题主题和训练方案。

## 本地目录

```text
数学课本拍照/
数学试题拍照/
语文课本拍照/
语文试题拍照/
```

## 常用命令

```powershell
python scripts/01_scan_photos.py
python scripts/02_score_red_marks.py
python scripts/06_build_static_site.py
pytest -q
```
