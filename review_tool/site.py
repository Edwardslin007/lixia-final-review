from __future__ import annotations

from html import escape
from pathlib import Path
import json
import re

import markdown

from review_tool.textbook_map import textbook_map_data


IDENTITY_PATTERNS = [
    r"学校[:：]?.*",
    r"班级[:：]?.*",
    r"姓名[:：]?.*",
    r"性名.*",
    r"学号[:：]?.*",
    r".*密封.*",
    r".*封\s*线.*",
    r".*林.*(青|精).*",
    r".*争.*(妹|媒).*",
    r"^\s*Q\s*$",
    r"^\s*30\s*$",
]


def sanitize_text(text: str) -> str:
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if any(re.search(pattern, stripped, flags=re.IGNORECASE) for pattern in IDENTITY_PATTERNS):
            continue
        lines.append(stripped)
    return "\n".join(lines)


def subject_outline(subject: str) -> dict:
    if subject == "数学":
        return {
            "title": "数学期末复习大纲",
            "focus": ["时间与钟面", "有余数除法", "万以内数", "长度和质量单位", "应用题审题", "计算与验算"],
            "must_do": ["圈关键词", "写列式", "列竖式", "带单位", "写答句", "验算"],
            "risk": ["心算跳步", "单位漏写", "经过时间看错", "余数大于除数", "至少/最多读反"],
        }
    return {
        "title": "语文期末复习大纲",
        "focus": ["生字词", "形近字", "多音字", "句子与标点", "阅读理解", "看图写话"],
        "must_do": ["读完整题目", "回原文定位", "检查错别字", "写完整句", "检查标点"],
        "risk": ["漏字", "拼音声调错", "形近字混淆", "答题格式不完整", "看图写话缺要素"],
    }


def page(title: str, body: str, extra_head: str = "") -> str:
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)}</title>
  <link rel="icon" href="data:,">
  <link rel="stylesheet" href="../assets/site.css">
  {extra_head}
</head>
<body>
{body}
</body>
</html>
"""


def root_page(title: str, body: str) -> str:
    return page(title, body).replace('../assets/site.css', 'assets/site.css')


def load_wrong_items(root: Path) -> list[dict]:
    path = root / "wrongbook" / "wrong_items.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []


def render_wrongbook(root: Path, docs_dir: Path) -> None:
    items = load_wrong_items(root)
    cards = []
    for item in items:
        excerpt = escape(sanitize_text(item["excerpt"]))
        solution = escape(item["solution"])
        cards.append(
            f"""
<article class="wrong-card" data-subject="{escape(item['subject'])}">
  <div class="wrong-card__meta">
    <span>{escape(item['id'])}</span>
    <span>{escape(item['topic'])}</span>
    <span>红笔比例 {escape(str(item['red_ratio']))}</span>
  </div>
  <h2>{escape(item['subject'])} · {escape(item['topic'])}</h2>
  <p class="reason">{escape(item['reason'])}</p>
  <pre>{excerpt}</pre>
  <details class="knowledge-toggle">
    <summary><span class="star">★</span> 展开对应课本知识点和复习方法</summary>
    <div class="knowledge-panel">
      <h3>对应知识点</h3>
      <p>{escape(item['topic'])}</p>
      <h3>详细解题过程</h3>
      <pre>{solution}</pre>
    </div>
  </details>
</article>
"""
        )
    body = f"""
<header class="topbar">
  <a href="../index.html">首页</a>
  <a href="../textbook-map/index.html">课本知识点</a>
  <a href="../outline/index.html">复习大纲</a>
</header>
<main class="layout">
  <section class="page-head">
    <p class="eyebrow">Wrongbook</p>
    <h1>期末错题集锦</h1>
    <p>共 {len(items)} 个红笔候选错题片段。点击红色星星查看对应知识点和解题流程。</p>
  </section>
  <section class="toolbar">
    <button data-filter="全部" class="active">全部</button>
    <button data-filter="语文">语文</button>
    <button data-filter="数学">数学</button>
  </section>
  <section class="wrong-grid">
    {''.join(cards)}
  </section>
</main>
<script>
document.querySelectorAll('.toolbar button').forEach(button => {{
  button.addEventListener('click', () => {{
    document.querySelectorAll('.toolbar button').forEach(b => b.classList.remove('active'));
    button.classList.add('active');
    const filter = button.dataset.filter;
    document.querySelectorAll('.wrong-card').forEach(card => {{
      card.hidden = filter !== '全部' && card.dataset.subject !== filter;
    }});
  }});
}});
</script>
"""
    out = docs_dir / "wrongbook"
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(page("期末错题集锦", body), encoding="utf-8")


def render_outline(docs_dir: Path) -> None:
    sections = []
    for subject in ["语文", "数学"]:
        outline = subject_outline(subject)
        focus = "".join(f"<li>{escape(item)}</li>" for item in outline["focus"])
        must_do = "".join(f"<li>{escape(item)}</li>" for item in outline["must_do"])
        risk = "".join(f"<li>{escape(item)}</li>" for item in outline["risk"])
        sections.append(
            f"""
<section class="outline-section">
  <h2>{escape(outline['title'])}</h2>
  <div class="outline-columns">
    <div><h3>重点知识点</h3><ul>{focus}</ul></div>
    <div><h3>考试动作</h3><ul>{must_do}</ul></div>
    <div><h3>高风险失分点</h3><ul>{risk}</ul></div>
  </div>
</section>
"""
        )
    body = f"""
<header class="topbar">
  <a href="../index.html">首页</a>
  <a href="../textbook-map/index.html">课本知识点</a>
  <a href="../wrongbook/index.html">错题集</a>
</header>
<main class="layout">
  <section class="page-head">
    <p class="eyebrow">Review Map</p>
    <h1>语文和数学期末复习知识点大纲</h1>
    <p>按课本内容和错题暴露出的风险整理，优先复习会做但容易失分的部分。</p>
  </section>
  {''.join(sections)}
</main>
"""
    out = docs_dir / "outline"
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(page("期末复习知识点大纲", body), encoding="utf-8")


def render_knowledge_pages(root: Path, docs_dir: Path) -> None:
    out = docs_dir / "knowledge"
    out.mkdir(parents=True, exist_ok=True)
    links = []
    for md_path in sorted((root / "knowledge").glob("*.md")):
        text = sanitize_text(md_path.read_text(encoding="utf-8"))
        # Public pages intentionally keep a compact excerpt to avoid publishing full textbook OCR.
        excerpt = "\n".join(text.splitlines()[:240])
        html = markdown.markdown(excerpt, extensions=["fenced_code", "tables"])
        target = out / f"{md_path.stem}.html"
        body = f"""
<header class="topbar"><a href="../index.html">首页</a><a href="../textbook-map/index.html">课本知识点</a><a href="../outline/index.html">复习大纲</a></header>
<main class="layout article">
  <section class="page-head">
    <p class="eyebrow">Knowledge</p>
    <h1>{escape(md_path.stem)}</h1>
    <p>公开页面为脱敏节选；本地 Markdown 保留更完整 OCR 结果。</p>
  </section>
  {html}
</main>
"""
        target.write_text(page(md_path.stem, body), encoding="utf-8")
        links.append((md_path.stem, f"knowledge/{target.name}"))
    index_links = "".join(f'<a class="tile" href="{escape(href)}">{escape(title)}</a>' for title, href in links)
    (out / "index.html").write_text(
        page(
            "知识库索引",
            f'<header class="topbar"><a href="../index.html">首页</a></header><main class="layout"><section class="page-head"><h1>知识库索引</h1></section><section class="tile-grid">{index_links}</section></main>',
        ),
        encoding="utf-8",
    )


def render_index(docs_dir: Path) -> None:
    body = """
<main class="home">
  <section class="home-hero">
    <p class="eyebrow">Final Review Studio</p>
    <h1>二年级下学期期末特训工作台</h1>
    <p>围绕课本、试题、错题和考前检查动作，集中解决“会做但容易马虎丢分”。</p>
  </section>
  <section class="tile-grid">
    <a class="tile" href="textbook-map/index.html">课本知识点总览</a>
    <a class="tile" href="wrongbook/index.html">错题集锦</a>
    <a class="tile" href="outline/index.html">复习知识点大纲</a>
    <a class="tile" href="knowledge/index.html">结构化知识库</a>
    <a class="tile" href="downloads/index.html">打印 PDF</a>
  </section>
  <section class="exam-rules">
    <h2>考前固定动作</h2>
    <ol>
      <li>数学先圈关键词，再列式、竖式、验算。</li>
      <li>语文阅读题回原文定位，写完检查错别字和标点。</li>
      <li>不会题先跳过，会做题不省步骤。</li>
    </ol>
  </section>
</main>
"""
    (docs_dir / "index.html").write_text(root_page("期末特训工作台", body), encoding="utf-8")


def render_textbook_map(docs_dir: Path) -> None:
    data = textbook_map_data()
    subject_sections = []
    tabs = []
    for subject_index, subject in enumerate(data["subjects"]):
        active = " active" if subject_index == 0 else ""
        tabs.append(
            f'<button class="subject-tab{active}" data-subject="{escape(subject["name"])}">{escape(subject["name"])}</button>'
        )
        exam_moves = "".join(f"<li>{escape(item)}</li>" for item in subject["exam_moves"])
        risk_points = "".join(f"<li>{escape(item)}</li>" for item in subject["risk_points"])
        units = []
        for unit_index, unit in enumerate(subject["units"], start=1):
            lessons = "".join(f"<span>{escape(item)}</span>" for item in unit["lessons"])
            knowledge = "".join(f"<li>{escape(item)}</li>" for item in unit["knowledge"])
            checks = "".join(f"<li>{escape(item)}</li>" for item in unit["check"])
            detail_sections = []
            for detail in unit["details"]:
                detail_items = "".join(f"<li>{escape(item)}</li>" for item in detail["items"])
                detail_sections.append(
                    f"""
<section class="detail-group">
  <h5>{escape(detail['title'])}</h5>
  <ul>{detail_items}</ul>
</section>
"""
                )
            units.append(
                f"""
<article class="unit-card">
  <div class="unit-number">{unit_index:02d}</div>
  <div class="unit-body">
    <h3>{escape(unit['title'])}</h3>
    <div class="lesson-strip">{lessons}</div>
    <div class="unit-columns">
      <section><h4>核心知识点</h4><ul>{knowledge}</ul></section>
      <section><h4>复习检查</h4><ul>{checks}</ul></section>
    </div>
    <div class="detail-board">
      <h4>细化考点</h4>
      <div class="detail-grid">{''.join(detail_sections)}</div>
    </div>
  </div>
</article>
"""
            )
        subject_sections.append(
            f"""
<section class="subject-map{active}" data-subject-panel="{escape(subject['name'])}">
  <div class="subject-intro {escape(subject['theme'])}">
    <div>
      <p class="eyebrow">Textbook Track</p>
      <h2>{escape(subject['name'])}课本知识点</h2>
      <p>{escape(subject['subtitle'])}</p>
    </div>
    <div class="focus-box">
      <h3>考试固定动作</h3>
      <ol>{exam_moves}</ol>
    </div>
    <div class="focus-box risk-box">
      <h3>高风险失分点</h3>
      <ul>{risk_points}</ul>
    </div>
  </div>
  <div class="unit-timeline">{''.join(units)}</div>
</section>
"""
        )

    body = f"""
<header class="topbar">
  <a href="../index.html">首页</a>
  <a href="../wrongbook/index.html">错题集</a>
  <a href="../outline/index.html">复习大纲</a>
</header>
<main class="layout textbook-layout">
  <section class="page-head textbook-head">
    <p class="eyebrow">One Page Textbook Map</p>
    <h1>语文和数学课本知识点总览</h1>
    <p>把二年级下册语文、数学课本压缩成一张复习地图：按课本单元顺序看，先抓核心知识点，再看检查动作。</p>
  </section>
  <section class="subject-switch" aria-label="科目切换">
    {''.join(tabs)}
  </section>
  {''.join(subject_sections)}
</main>
<script>
document.querySelectorAll('.subject-tab').forEach(tab => {{
  tab.addEventListener('click', () => {{
    const subject = tab.dataset.subject;
    document.querySelectorAll('.subject-tab').forEach(item => item.classList.toggle('active', item === tab));
    document.querySelectorAll('.subject-map').forEach(panel => {{
      panel.classList.toggle('active', panel.dataset.subjectPanel === subject);
    }});
  }});
}});
</script>
"""
    out = docs_dir / "textbook-map"
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(page("课本知识点总览", body), encoding="utf-8")


def render_css(docs_dir: Path) -> None:
    assets = docs_dir / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    (assets / "site.css").write_text(
        """
:root{--ink:#17211b;--muted:#68746c;--paper:#fbfaf5;--line:#d8d8ce;--green:#23634b;--red:#c7352c;--blue:#2f5f98;--gold:#ad7a16}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font-family:"Microsoft YaHei","Noto Sans CJK SC",sans-serif;line-height:1.65}a{color:inherit}.topbar{height:56px;display:flex;gap:18px;align-items:center;padding:0 28px;border-bottom:1px solid var(--line);background:#fffdf8;position:sticky;top:0;z-index:2}.topbar a{text-decoration:none;color:var(--green);font-weight:700}.layout{max-width:1120px;margin:0 auto;padding:34px 22px 70px}.home{max-width:1080px;margin:0 auto;padding:56px 22px}.home-hero,.page-head{border-bottom:2px solid var(--ink);padding-bottom:22px;margin-bottom:24px}.eyebrow{text-transform:uppercase;letter-spacing:.08em;color:var(--gold);font-weight:800;margin:0 0 8px}h1{font-size:clamp(34px,5vw,64px);line-height:1.05;margin:0 0 14px}h2{font-size:28px;margin:26px 0 12px}h3{margin:14px 0 8px}.tile-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px;margin:24px 0}.tile{display:block;padding:22px;min-height:110px;text-decoration:none;border:1px solid var(--line);background:white;border-radius:8px;font-size:22px;font-weight:800;color:var(--green)}.exam-rules,.outline-section{background:white;border:1px solid var(--line);border-radius:8px;padding:22px;margin-top:20px}.outline-columns{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:18px}.toolbar{display:flex;gap:10px;margin:18px 0;flex-wrap:wrap}.toolbar button{border:1px solid var(--line);background:white;border-radius:999px;padding:8px 16px;font-weight:800;cursor:pointer}.toolbar button.active{background:var(--ink);color:white}.wrong-grid{display:grid;gap:16px}.wrong-card{background:white;border:1px solid var(--line);border-left:8px solid var(--red);border-radius:8px;padding:18px}.wrong-card__meta{display:flex;gap:10px;flex-wrap:wrap;color:var(--muted);font-size:14px}.reason{font-weight:700;color:var(--blue)}pre{white-space:pre-wrap;word-break:break-word;background:#f3f1e8;border:1px solid var(--line);border-radius:6px;padding:14px;max-height:420px;overflow:auto}.knowledge-toggle summary{cursor:pointer;font-weight:900;color:var(--red)}.star{font-size:24px;color:var(--red);vertical-align:-2px}.knowledge-panel{border-top:1px solid var(--line);margin-top:12px;padding-top:12px}.article{max-width:900px}.article code{white-space:pre-wrap}.textbook-layout{max-width:1240px}.textbook-head{display:grid;grid-template-columns:minmax(0,1fr);gap:10px}.subject-switch{display:flex;gap:8px;margin:18px 0 22px;position:sticky;top:56px;z-index:1;background:linear-gradient(#fbfaf5 70%,rgba(251,250,245,.75));padding:10px 0}.subject-tab{border:1px solid var(--line);background:#fffdf8;color:var(--ink);border-radius:8px;padding:10px 22px;font-weight:900;font-size:18px;cursor:pointer}.subject-tab.active{background:var(--ink);color:white}.subject-map{display:none}.subject-map.active{display:block}.subject-intro{display:grid;grid-template-columns:1.35fr .9fr .9fr;gap:14px;padding:20px;border:1px solid var(--line);border-radius:8px;background:#fffdf8}.subject-intro.language{border-top:8px solid var(--green)}.subject-intro.math{border-top:8px solid var(--blue)}.subject-intro h2{margin-top:0}.focus-box{background:white;border:1px solid var(--line);border-radius:8px;padding:16px}.risk-box{border-color:#e5b8aa}.focus-box ol,.focus-box ul{margin:0;padding-left:20px}.unit-timeline{position:relative;display:grid;gap:14px;margin-top:18px}.unit-timeline:before{content:"";position:absolute;left:28px;top:0;bottom:0;width:2px;background:var(--line)}.unit-card{display:grid;grid-template-columns:64px minmax(0,1fr);gap:14px;position:relative}.unit-number{height:56px;width:56px;border-radius:50%;background:var(--ink);color:white;display:grid;place-items:center;font-weight:900;z-index:1}.unit-body{background:white;border:1px solid var(--line);border-radius:8px;padding:18px}.unit-body h3{margin:0 0 10px;font-size:24px}.lesson-strip{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:14px}.lesson-strip span{border:1px solid var(--line);background:#f7f5ed;border-radius:999px;padding:4px 10px;font-size:14px}.unit-columns{display:grid;grid-template-columns:1fr 1fr;gap:12px}.unit-columns section{background:#fbfaf5;border:1px solid var(--line);border-radius:8px;padding:12px}.unit-columns h4{margin:0 0 6px;color:var(--green)}.unit-columns ul{margin:0;padding-left:20px}.detail-board{margin-top:14px;border-top:1px solid var(--line);padding-top:14px}.detail-board>h4{margin:0 0 10px;color:var(--blue);font-size:18px}.detail-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}.detail-group{border:1px solid var(--line);border-radius:8px;background:#fffdf8;padding:12px}.detail-group h5{margin:0 0 8px;font-size:16px;color:var(--ink)}.detail-group ul{margin:0;padding-left:19px}.detail-group li{margin:4px 0}@media(max-width:980px){.detail-grid{grid-template-columns:1fr 1fr}}@media(max-width:820px){.subject-intro,.unit-columns,.detail-grid{grid-template-columns:1fr}.topbar{overflow:auto}.unit-card{grid-template-columns:48px minmax(0,1fr)}.unit-number{width:44px;height:44px}.unit-timeline:before{left:22px}}@media print{.topbar,.toolbar,.subject-switch{display:none}.wrong-card,.unit-card{break-inside:avoid}body{background:white}.layout{padding:0}pre{max-height:none}.subject-map{display:block}.subject-intro,.unit-body{box-shadow:none}}
""".strip(),
        encoding="utf-8",
    )


def render_site(root: Path) -> None:
    docs_dir = root / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    render_css(docs_dir)
    render_index(docs_dir)
    render_wrongbook(root, docs_dir)
    render_outline(docs_dir)
    render_textbook_map(docs_dir)
    render_knowledge_pages(root, docs_dir)
