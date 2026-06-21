from __future__ import annotations

from pathlib import Path
import json
import re


IDENTITY_PATTERNS = [
    r"学校[:：]?.*",
    r"班级[:：]?.*",
    r"姓名[:：]?.*",
    r"性名.*",
    r"学号[:：]?.*",
    r".*密封.*",
    r".*封\s*线.*",
    r".*林.*(青|精).*",
]


def sanitize_public_text(text: str) -> str:
    lines = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if any(re.search(pattern, line, flags=re.IGNORECASE) for pattern in IDENTITY_PATTERNS):
            continue
        lines.append(line)
    return "\n".join(lines)


def load_wrong_items(root: Path) -> list[dict]:
    path = root / "wrongbook" / "wrong_items.json"
    if not path.exists():
        return []
    items = json.loads(path.read_text(encoding="utf-8"))
    sanitized = []
    for item in items:
        sanitized.append({**item, "excerpt": sanitize_public_text(str(item.get("excerpt", "")))})
    return sanitized


def summarize_wrong_topics(items: list[dict]) -> dict[str, list[dict]]:
    summaries: dict[str, dict[str, dict]] = {"语文": {}, "数学": {}}
    for item in items:
        subject = str(item.get("subject", ""))
        topic = str(item.get("topic", "综合易错题"))
        if subject not in summaries:
            continue
        bucket = summaries[subject].setdefault(topic, {"topic": topic, "count": 0, "samples": []})
        bucket["count"] += 1
        if len(bucket["samples"]) < 3:
            bucket["samples"].append(
                {
                    "name": item.get("name", ""),
                    "rel_path": item.get("rel_path", ""),
                    "excerpt": str(item.get("excerpt", ""))[:220],
                }
            )
    return {
        subject: sorted(topic_rows.values(), key=lambda row: (-row["count"], row["topic"]))
        for subject, topic_rows in summaries.items()
    }


def source_hits(root: Path, filename: str, keywords: list[str], limit: int = 3) -> list[str]:
    path = root / "knowledge" / filename
    if not path.exists():
        return []
    text = sanitize_public_text(path.read_text(encoding="utf-8"))
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    hits = []
    for keyword in keywords:
        for line in lines:
            if keyword in line and line not in hits:
                hits.append(line[:180])
                break
        if len(hits) >= limit:
            break
    return hits


def math_modules(root: Path) -> list[dict]:
    return [
        {
            "title": "时间与钟面：跨整点、单位换算、读钟面",
            "priority": "最高",
            "why": "错题里时间题和钟面题反复出现，孩子容易把分针大格、小格、经过时间和单位换算混在一起。",
            "textbook_sources": source_hits(root, "数学课本知识库.md", ["1时=60分", "分针", "经过"]),
            "teach": [
                "先让孩子说：这题问的是“时刻”还是“经过了多久”。时刻是几点几分，经过时间是多少分钟。",
                "跨整点一律拆成两段，不允许直接用后面的分钟减前面的分钟。",
                "单位换算先写等式：1时=60分，1分=60秒，再把多出来的部分接上。",
            ],
            "worked_examples": [
                {
                    "question": "9:50 到 10:20 经过多少分？",
                    "steps": "题干是9:50 到 10:20。先算9:50到10:00是10分；再算10:00到10:20是20分；10分+20分=30分。不能写50-20。",
                    "answer": "经过30分。",
                    "trap": "孩子最容易看到50和20就相减，实际跨了10点。",
                },
                {
                    "question": "75分=几时几分？",
                    "steps": "75分里面先拿出60分，60分=1时；还剩75-60=15分，所以75分=1时15分。",
                    "answer": "1时15分。",
                    "trap": "不要写成1时75分，也不要把75分当成75秒。",
                },
            ],
            "routines": [
                "读钟面：先短针后长针，分针指几就用几乘5。",
                "经过时间：画时间线，先到整点，再算剩下部分。",
                "单位换算：先写1时=60分、1分=60秒，再计算。",
                "竖式草稿：涉及加减分钟时，把分钟加减过程写出来，不口算跳步。",
            ],
            "drills": [
                "7:35到8:10经过多少分？",
                "1时20分=多少分？",
                "分针从12走到8，经过多少分？",
            ],
        },
        {
            "title": "有余数除法：最多、至少、周期题",
            "priority": "最高",
            "why": "有余数题看似会算，但满分关键在理解余数含义，尤其是“最多”和“至少”不能混。",
            "textbook_sources": source_hits(root, "数学课本知识库.md", ["余数", "最多", "至少"]),
            "teach": [
                "先圈关键词：最多、至少、平均、每份、还剩。",
                "写完除法后必须解释余数：剩下的够不够再占一份。",
                "检查余数一定比除数小，这是硬规则。",
            ],
            "worked_examples": [
                {
                    "question": "34个苹果，每盒装6个，最多装几盒，还剩几个？",
                    "steps": "34÷6=5……4。商5表示能装满5盒，余数4表示还剩4个，不够再装满一盒。",
                    "answer": "最多装5盒，还剩4个。",
                    "trap": "最多装满几盒只看商，不能因为还有4个就写6盒。",
                },
                {
                    "question": "34人坐车，每辆车坐6人，至少需要几辆车？",
                    "steps": "34÷6=5……4。5辆车只能坐30人，还剩4人也要坐车，所以5+1=6辆。",
                    "answer": "至少需要6辆车。",
                    "trap": "“至少需要”遇到余数通常要商加1。",
                },
            ],
            "routines": [
                "除法横式写完整：被除数÷除数=商……余数。",
                "草稿区写检查：余数 < 除数。",
                "答句必须带“最多”或“至少”，不要只写数字。",
            ],
            "drills": [
                "29本书，每人分4本，最多分给几人，还剩几本？",
                "29本书，每袋装4本，至少要几个袋子？",
                "红黄蓝三色循环，第38个是什么颜色？",
            ],
        },
        {
            "title": "两、三位数加减法：竖式、退位、验算",
            "priority": "最高",
            "why": "孩子基础不错时，计算失分通常不是不会，而是不列竖式、不标退位、不验算。",
            "textbook_sources": source_hits(root, "数学课本知识库.md", ["竖式", "验算", "退位"]),
            "teach": [
                "每道计算题先写竖式，个位对个位、十位对十位、百位对百位。",
                "退位题必须在草稿上标出借位，特别是中间有0的题。",
                "做完用反运算验算，不靠感觉。",
            ],
            "worked_examples": [
                {
                    "question": "306-128=",
                    "steps": "个位6-8不够，向十位借；十位是0，要先向百位借1，百位3变2，十位变10；十位借给个位1后变9，个位16-8=8，十位9-2=7，百位2-1=1。",
                    "answer": "178。",
                    "trap": "连续退位时，十位不能还当10直接减2，要先借给个位变9。",
                },
                {
                    "question": "487+236=",
                    "steps": "个位7+6=13，写3进1；十位8+3+1=12，写2进1；百位4+2+1=7。",
                    "answer": "723。",
                    "trap": "进位的小1不能漏加。",
                },
            ],
            "routines": [
                "竖式草稿模板：列式、竖式、验算、答句四行必须齐。",
                "横式答案要从竖式抄回去，再看一遍有没有抄错。",
                "估算检查：答案大概在哪个范围，明显离谱就重算。",
            ],
            "drills": ["604-279=", "358+467=", "900-436="],
        },
        {
            "title": "万以内数：0的读写、组成、比较、近似数",
            "priority": "高",
            "why": "这类题不难，但极容易在0的占位和读法上扣分。",
            "textbook_sources": source_hits(root, "数学课本知识库.md", ["千位", "读作", "写作"]),
            "teach": [
                "读写数先画数位表：千位、百位、十位、个位。",
                "中间有0要读一个零，末尾0不读，但写数必须占位。",
                "比较大小先看位数，位数相同从最高位开始比。",
            ],
            "worked_examples": [
                {
                    "question": "三千零六写作多少？",
                    "steps": "三千说明千位是3，零六说明百位和十位没有，要用0占位，个位是6。",
                    "answer": "3006。",
                    "trap": "不能写成306，少了一位。",
                },
                {
                    "question": "4020读作什么？",
                    "steps": "千位4读四千，百位0在中间读零，十位2读二十，个位0在末尾不读。",
                    "answer": "四千零二十。",
                    "trap": "末尾0不读，中间0要读。",
                },
            ],
            "routines": [
                "写数后从右往左数位数，看是否漏0。",
                "含0题读一遍、写一遍、再反查一遍。",
                "近似数题先看题目要接近整十、整百还是整千。",
            ],
            "drills": ["一个数由5个千、3个十、8个一组成，写作？", "6080读作？", "4970约等于几千？"],
        },
        {
            "title": "单位、方向、角、数据：小题防漏分",
            "priority": "中高",
            "why": "这些题常作为填空、选择、判断出现，分值不大但容易因为单位或观察点丢分。",
            "textbook_sources": source_hits(root, "数学课本知识库.md", ["厘米", "方向", "统计"]),
            "teach": [
                "长度单位先联系生活实际，再换算。",
                "方向题先找观察点，题目问A在B哪里，就站在B看A。",
                "角先找顶点和两条边，角大小看张口，不看边长。",
            ],
            "worked_examples": [
                {
                    "question": "6分米和58厘米哪个长？",
                    "steps": "先统一单位。1分米=10厘米，所以6分米=60厘米；60厘米>58厘米。",
                    "answer": "6分米长。",
                    "trap": "单位不同不能直接比较6和58。",
                },
                {
                    "question": "学校在公园东面，公园在学校哪面？",
                    "steps": "东和西相对。学校在公园东面，反过来看，公园就在学校西面。",
                    "answer": "西面。",
                    "trap": "观察点变了，方向要反过来。",
                },
            ],
            "routines": [
                "单位题先统一单位，再比较或计算。",
                "方向题手指按住观察点，再看目标位置。",
                "统计题先看表头，最多最少圈出来，相差多少用减法。",
            ],
            "drills": ["3厘米5毫米=多少毫米？", "一个正字加两画表示多少？", "长方形有几个直角？"],
        },
    ]


def chinese_modules(root: Path) -> list[dict]:
    return [
        {
            "title": "课文阅读理解：回原文定位，不凭印象答",
            "priority": "最高",
            "why": "二年级语文想拿满分，阅读题不能只凭记忆，必须训练用课文句子支撑答案。",
            "textbook_sources": source_hits(root, "语文课本知识库.md", ["找春天", "雷锋", "小马过河"]),
            "teach": [
                "题目问“从哪里看出”，答案必须来自原文具体词句。",
                "题目问“为什么”，用“因为……所以……”把原因和结果说完整。",
                "题目问人物品质，先写品质，再写一件课文中的事证明。",
            ],
            "worked_examples": [
                {
                    "question": "《找春天》中孩子们找到的春天有哪些？",
                    "steps": "回课文找具体景物：小草、野花、嫩芽、小溪。回答时写成完整句。",
                    "answer": "孩子们从小草、野花、树木的嫩芽和解冻的小溪里找到了春天。",
                    "trap": "不能只写“很多地方”，要写具体景物。",
                },
                {
                    "question": "《小马过河》告诉我们什么道理？",
                    "steps": "先说小马遇到问题，再说它听了老牛和松鼠的话，最后自己试了才知道。道理要联系故事。",
                    "answer": "遇到问题不能只听别人说，要自己动脑筋想一想、试一试。",
                    "trap": "不能只写“要勇敢”，太空泛。",
                },
            ],
            "routines": [
                "阅读题先读问题，再回原文定位。",
                "答题写完整句，不只写词语。",
                "写完检查有没有漏掉“为什么、怎样、从哪里看出”的要求。",
            ],
            "drills": [
                "《雷锋叔叔，你在哪里》中雷锋帮助了谁？",
                "《青蛙卖泥塘》中泥塘为什么后来不卖了？",
                "《大禹治水》中大禹为什么让人敬佩？",
            ],
        },
        {
            "title": "生字词和形近字：按结构检查笔画",
            "priority": "最高",
            "why": "语文基础题最容易因为漏笔、形近字、同音字丢分，满分必须靠检查动作。",
            "textbook_sources": source_hits(root, "语文课本知识库.md", ["生字", "词语", "语文园地"]),
            "teach": [
                "先看结构：左右、上下、半包围，别把部件写散。",
                "形近字放在词语里记，不单独死记。",
                "默写后用手指逐字检查偏旁、关键笔画和占格。",
            ],
            "worked_examples": [
                {
                    "question": "区分“值”和“植”。",
                    "steps": "“植树”是木字旁，和树木有关；“值日、价值”是单人旁，和人或价值有关。",
                    "answer": "植树、值日。",
                    "trap": "只听读音会写混，要看偏旁意思。",
                },
                {
                    "question": "写“暖”时检查什么？",
                    "steps": "左边是日字旁，右边部件不要写成爱，横画和撇捺要看清。",
                    "answer": "暖和、温暖。",
                    "trap": "右边部件容易漏笔。",
                },
            ],
            "routines": [
                "每天听写20个高频字词，错字当天重写3遍并组词。",
                "形近字用“偏旁意思+词语”复习。",
                "写完默读一遍词语，检查有没有同音替换。",
            ],
            "drills": ["州/舟、炒/抄、值/植、峰/锋、园/圆", "听写传统节日词语", "听写课文后生字词"],
        },
        {
            "title": "古诗和课文背诵：诗句、画面、关键词一起记",
            "priority": "高",
            "why": "古诗填空和课文内容填空看起来简单，但容易错在字、顺序和理解。",
            "textbook_sources": source_hits(root, "语文课本知识库.md", ["村居", "咏柳", "绝句"]),
            "teach": [
                "背古诗不能只背声音，要说出诗句画面。",
                "填空题先看上下句，再写缺的字。",
                "课文内容题抓人物、地点、事情和结果。",
            ],
            "worked_examples": [
                {
                    "question": "《咏柳》中“不知细叶谁裁出”后一句是什么？",
                    "steps": "先想画面：细细的柳叶像被剪刀裁出来，后一句写二月春风像剪刀。",
                    "answer": "二月春风似剪刀。",
                    "trap": "“似”不要写成“是”。",
                },
                {
                    "question": "《绝句》里有哪些景物？",
                    "steps": "按诗句找：黄鹂、翠柳、白鹭、青天、千秋雪、万里船。",
                    "answer": "诗中写了黄鹂、翠柳、白鹭、青天、雪和船等景物。",
                    "trap": "不要只背诗，不会说画面。",
                },
            ],
            "routines": [
                "背一首诗后，马上默写一遍，再讲一遍画面。",
                "错一个字，把整句重写2遍。",
                "课文复述用“谁在什么地方做什么，结果怎样”。",
            ],
            "drills": ["默写《村居》重点句", "说《雷雨》前中后三个阶段", "复述《羿射九日》起因经过结果"],
        },
        {
            "title": "句子、标点、仿写：按格式拿分",
            "priority": "中高",
            "why": "二年级句子题重在格式，孩子容易会意思但写不完整。",
            "textbook_sources": source_hits(root, "语文课本知识库.md", ["句子", "仿写", "标点"]),
            "teach": [
                "仿写先圈原句格式，再替换词语。",
                "连词成句先找谁，再找做什么，最后补地点或心情。",
                "标点题读语气：问问题用问号，感叹用感叹号，一般陈述用句号。",
            ],
            "worked_examples": [
                {
                    "question": "仿写：小草从地下探出头来。",
                    "steps": "原句是“谁从哪里怎么样”。可以换成花儿、柳枝、小鸟等。",
                    "answer": "花儿从草丛里露出笑脸。",
                    "trap": "不能只写“花儿很美”，格式不一致。",
                },
                {
                    "question": "给句子加标点：你去过科技馆吗",
                    "steps": "句子是在问别人有没有去过，语气是疑问。",
                    "answer": "你去过科技馆吗？",
                    "trap": "问句不能写句号。",
                },
            ],
            "routines": [
                "句子必须有主语和动作。",
                "仿写必须保留原句骨架。",
                "写完最后看标点是否和语气一致。",
            ],
            "drills": ["用“因为……所以……”写一句话", "把词语排成一句通顺的话", "给3个句子补标点"],
        },
        {
            "title": "看图写话：四要素和检查清单",
            "priority": "高",
            "why": "看图写话是语文拉分点，基础好的孩子也会因为少写要素、句子太短被扣分。",
            "textbook_sources": source_hits(root, "语文试题知识库.md", ["看图", "写话", "图画"]),
            "teach": [
                "先口头说：什么时候，谁在哪里，做什么，心情怎样。",
                "至少写3到5句，不能只写一两句流水账。",
                "结尾补一句感受或结果。",
            ],
            "worked_examples": [
                {
                    "question": "看到图上小朋友植树，怎么写开头？",
                    "steps": "先写时间地点人物：春天到了，同学们来到公园里植树。",
                    "answer": "春天到了，同学们来到公园里植树。",
                    "trap": "不要一上来只写“他们很开心”，缺少事情。",
                },
                {
                    "question": "写完后怎么检查？",
                    "steps": "检查有没有时间、地点、人物、事情、心情；再检查句号、逗号和错别字。",
                    "answer": "五项都有，句子通顺，标点正确。",
                    "trap": "只顾写多，不检查错别字。",
                },
            ],
            "routines": [
                "写前先说一遍四要素。",
                "每句话写完加标点。",
                "最后默读，发现不通顺就改。",
            ],
            "drills": ["写一次植树图", "写一次帮助同学图", "写一次下雨放学图"],
        },
    ]


def five_day_plan() -> list[dict]:
    return [
        {
            "day": "第1天",
            "title": "错题诊断和高危习惯纠正",
            "tasks": ["按错题主题排序，先做时间、有余数、阅读理解", "建立数学草稿格式", "语文字词听写一轮"],
            "output": "得到一张个人高危清单：最容易错的3类数学题、2类语文题。",
        },
        {
            "day": "第2天",
            "title": "数学满分基础日",
            "tasks": ["时间与钟面专项20分钟", "有余数除法专项20分钟", "竖式退位和验算专项20分钟"],
            "output": "每道题必须留下列式、竖式或时间线。",
        },
        {
            "day": "第3天",
            "title": "语文课本和阅读日",
            "tasks": ["课文关键问题口答", "古诗默写和画面解释", "阅读题回原文定位训练"],
            "output": "形成语文答题模板：因为所以、从文中哪句话看出、人物品质加事件。",
        },
        {
            "day": "第4天",
            "title": "同类题强化日",
            "tasks": ["每个错题主题做3道同类题", "做错的题当场讲一遍错因", "晚间复测上午错题"],
            "output": "把会做但马虎的题压到最低。",
        },
        {
            "day": "第5天",
            "title": "模拟和考前检查日",
            "tasks": ["限时做一套综合卷", "只改检查习惯，不再大量学新内容", "睡前看满分检查口令"],
            "output": "考场固定动作自动化：圈关键词、列式、验算、回原文、查标点。",
        },
    ]


def build_sprint_review_data(root: Path) -> dict:
    wrong_items = load_wrong_items(root)
    return {
        "title": "期末冲刺复习系统",
        "principle": "错题优先，课本兜底；不平均复习，专攻会做但容易丢分的地方。",
        "wrong_topic_summary": summarize_wrong_topics(wrong_items),
        "five_day_plan": five_day_plan(),
        "subjects": [
            {
                "name": "语文",
                "mission": "把课本内容转化成能答完整、写正确、少丢格式分的能力。",
                "modules": chinese_modules(root),
            },
            {
                "name": "数学",
                "mission": "把会算的题做稳，强制草稿、竖式、单位和验算，减少马虎扣分。",
                "modules": math_modules(root),
            },
        ],
    }
