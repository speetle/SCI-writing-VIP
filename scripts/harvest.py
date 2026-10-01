#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
harvest.py — SCI-writing-VIP 每周文献猎取与分层引擎（纯标准库，可直接运行）

流程（S1 阶段）
  1. esearch   多检索块 × 周时间窗（EDAT）→ PMID 合集
  2. 去重      按 PMID
  3. esummary  批量取元数据（期刊 ISO 缩写 / 标题 / 出版类型 / DOI / PMCID）
  4. efetch    批量取结构化摘要 + MeSH + 出版类型
  5. 初筛      排除社论/评论/勘误/撤回/新闻等非研究性文献；要求摘要长度达标
  6. 打标      生信主题标签、方法标签、数据来源标签、干湿实验判定（纯生信 / 干湿结合）
  7. 排序      相关性得分 = 生信信号 + 纯生信加权 + 期刊层级 + 摘要信息量
  8. 精选      ≥ target 篇（默认 520）
  9. 分层      合并 journal_metrics.csv 的 IF → 区间（1-3 / 3-5 / 5-10 / >10）
 10. 输出      papers_master.csv / bins_summary.json / topic_clusters.json / search_log.md

红线：所有字段来自 NCBI/期刊指标表的真实抓取；IF 缺失一律标 UNBINNED，绝不臆测填值。

用法
  python3 harvest.py --out-dir <目录> --start 2026/09/14 --end 2026/09/21 --target 520
  python3 harvest.py --out-dir <目录> --start 2026/09/14 --end 2026/09/21 --counts-only
"""
import argparse
import csv
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter, OrderedDict
from datetime import date

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
UA = {"User-Agent": "SCI-writing-VIP/1.0 (academic literature screening; contact: local user)"}

# ---------------------------------------------------------------- 检索块
QUERY_BLOCKS = OrderedDict([
    ("B1_生信核心", '("bioinformatics"[tiab] OR "computational biology"[tiab] OR "in silico"[tiab] '
                'OR "systems biology"[tiab] OR "network pharmacology"[tiab] OR "molecular docking"[tiab] '
                'OR "molecular dynamics simulation"[tiab])'),
    ("B2_组学测序", '("transcriptomic*"[tiab] OR "transcriptome"[tiab] OR "RNA-seq"[tiab] OR "RNA sequencing"[tiab] '
                'OR "scRNA-seq"[tiab] OR "single-cell RNA"[tiab] OR "single-cell transcriptom*"[tiab] '
                'OR "spatial transcriptom*"[tiab] OR "proteomic*"[tiab] OR "metabolomic*"[tiab] '
                'OR "epigenom*"[tiab] OR "multi-omics"[tiab] OR "multiomics"[tiab] OR "whole-exome"[tiab] '
                'OR "whole-genome sequencing"[tiab] OR "metagenom*"[tiab] OR "microbiome"[tiab])'),
    ("B3_算法建模", '("machine learning"[tiab] OR "deep learning"[tiab] OR "artificial intelligence"[tiab] '
                'OR "random forest"[tiab] OR "LASSO"[tiab] OR "WGCNA"[tiab] OR "nomogram"[tiab] '
                'OR "neural network"[tiab] OR "foundation model"[tiab] OR "large language model"[tiab] '
                'OR "Mendelian randomization"[tiab] OR "radiomics"[tiab])'),
    ("B4_公共数据", '("GEO database"[tiab] OR "Gene Expression Omnibus"[tiab] OR "TCGA"[tiab] OR "GTEx"[tiab] '
                'OR "UK Biobank"[tiab] OR "ArrayExpress"[tiab] OR "ICGC"[tiab] OR "CPTAC"[tiab] '
                'OR "cBioPortal"[tiab] OR "GEPIA"[tiab] OR "TIMER"[tiab] OR "CCLE"[tiab] OR "GDSC"[tiab] '
                'OR "DepMap"[tiab] OR "Single Cell Portal"[tiab] OR "CELLxGENE"[tiab] '
                'OR "publicly available dataset*"[tiab] OR "public database*"[tiab] OR "open dataset*"[tiab])'),
    ("B5_纯生信标志物", '("differentially expressed genes"[tiab] OR "hub genes"[tiab] OR "immune infiltration"[tiab] '
                 'OR "prognostic signature"[tiab] OR "risk score model"[tiab] OR "diagnostic model"[tiab] '
                 'OR "biomarker signature"[tiab] OR "co-expression network"[tiab] OR "pathway enrichment"[tiab] '
                 'OR "protein-protein interaction network"[tiab] OR "tumor microenvironment"[tiab] '
                 'OR "drug target prediction"[tiab] OR "virtual screening"[tiab])'),
    # ---- 2026-10-01（先生指定「不局限生信，整个生物医药都可以」）新增 5 块 ----
    # 背景：先生原话「写作的日常训练可以不必局限在生信领域，整个生物医药领域都可以」。
    # 原先 B1–B5 全部是生信/组学/算法/公共数据语义 ⇒ 湿实验、药理、临床、免疫类文章
    # **根本不进入候选池**，相关性门槛再宽松也无用。以下 5 块补齐非生信侧。
    ("B6_药理与药物化学", '("drug repurposing"[tiab] OR "pharmacokinetic*"[tiab] OR "pharmacodynamic*"[tiab] '
                     'OR "IC50"[tiab] OR "structure-activity relationship"[tiab] OR "drug design"[tiab] '
                     'OR "pharmacophore"[tiab] OR "bioavailability"[tiab] OR "dose-response"[tiab] '
                     'OR "drug safety"[tiab] OR "adverse drug"[tiab] OR "toxicity evaluation"[tiab])'),
    ("B7_临床研究与真实世界", '("randomized controlled trial"[tiab] OR "double-blind"[tiab] OR "placebo"[tiab] '
                     'OR "prospective cohort"[tiab] OR "retrospective cohort"[tiab] OR "case-control study"[tiab] '
                     'OR "clinical trial"[tiab] OR "real-world data"[tiab] OR "observational study"[tiab] '
                     'OR "diagnostic accuracy"[tiab] OR "sensitivity and specificity"[tiab])'),
    ("B8_动物模型与疾病模型", '("mouse model"[tiab] OR "murine model"[tiab] OR "rat model"[tiab] '
                     'OR "animal model*"[tiab] OR "xenograft"[tiab] OR "knockout mouse"[tiab] '
                     'OR "transgenic mouse"[tiab] OR "disease model"[tiab] OR "in vivo"[tiab])'),
    ("B9_免疫机制与炎症", '("T-cell activation"[tiab] OR "cytokine release"[tiab] OR "macrophage polarization"[tiab] '
                     'OR "T helper cell"[tiab] OR "autoantibod*"[tiab] OR "vaccine efficacy"[tiab] '
                     'OR "antigen presentation"[tiab] OR "inflammasome"[tiab] OR "complement activation"[tiab] '
                     'OR "innate immune"[tiab] OR "adaptive immune"[tiab])'),
    ("B10_分子机制与信号通路", '("signaling pathway"[tiab] OR "molecular mechanism"[tiab] '
                      'OR "gene expression regulation"[tiab] OR "transcription factor"[tiab] '
                      'OR "ubiquitin*"[tiab] OR "autophagy"[tiab] OR "apoptosis"[tiab] '
                      'OR "post-translational modification"[tiab] OR "protein stability"[tiab])'),
])

# ---------------------------------------------------------------- 标签词典
TAGS = {
    "单细胞/空转": r"single-?cell|scRNA|snRNA|spatial transcriptom|trajectory|pseudotime|cell[- ]cell communication",
    "机器学习/深度学习": r"machine learning|deep learning|neural network|random forest|XGBoost|SVM|LASSO|nomogram|transformer|foundation model|large language model|LLM|scGPT|GPT",
    "孟德尔随机化/因果推断": r"mendelian randomi|instrumental variable|two-?sample MR|causal inference",
    "多组学整合": r"multi-?omics|integrat\w+ omics|proteogenomic|genomic.{0,20}transcriptom",
    "转录组/表达谱": r"transcriptom|RNA-?seq|microarray|differentially expressed|expression profil",
    "蛋白组/代谢组": r"proteom|metabolom|mass spectrometry|lipidom",
    "表观遗传/甲基化": r"epigenom|methylat|ChIP-?seq|ATAC-?seq|histone modification|m6A",
    "微生物组/宏基因组": r"microbiom|metagenom|16S rRNA|gut flora|microbiota",
    "网络药理学/分子对接": r"network pharmacolog|molecular docking|molecular dynamics|ADMET|virtual screening|pharmacophore",
    "GWAS/基因组变异": r"GWAS|genome-?wide association|whole-?exome|whole-?genome|SNP|copy number variation|mutational landscape|genomic landscape",
    "肿瘤微环境/免疫浸润": r"tumor microenvironment|immune infiltration|CIBERSORT|ESTIMATE|immunotherapy response|immune checkpoint|TMB|MSI",
    "预后模型/风险评分": r"prognostic (model|signature|score|index)|risk (score|model)|nomogram|survival model|predictive model",
    "生物标志物/诊断": r"biomarker|diagnostic (model|signature|panel)|early detection|liquid biopsy|circulating",
    "药物发现/靶点": r"drug (target|discovery|repurpos)|target identification|druggable|drug design",
    "影像组学/病理AI": r"radiomic|digital pathology|histopatholog\w+ image|whole slide image|imaging biomarker",
    "CRISPR/基因编辑": r"CRISPR|gene editing|knockout screen|base editing",
    "衰老/退行性": r"aging|senescence|Alzheimer|Parkinson|neurodegenerat|osteoporosis|sarcopenia",
    "代谢/内分泌": r"diabet|obesity|NAFLD|metabolic syndrome|insulin resistance|lipid metabolism|hyperlipidem|thyroid",
    "心血管": r"cardiovascular|myocardial|heart failure|atheroscler|hypertension|stroke|ischemi",
    "感染/免疫炎症": r"sepsis|infection|antimicrobial resistance|influenza|COVID|tuberculosis|autoimmun|rheumatoid|inflammatory bowel|colitis|psoriasis|inflammation",
    "肝肾/泌尿": r"hepatocellular|liver (injury|fibrosis|cirrhosis)|kidney (injury|disease)|nephropath|renal|bladder",
    "神经精神": r"depression|schizophren|epilep|anxiety|autism|brain|neuro",
    "呼吸/肺部": r"lung (cancer|injury|fibrosis)|COPD|asthma|pulmonary|ARDS",
    "中药/天然产物": r"traditional chinese medicine|herbal|natural product|flavonoid|polyphenol|ginsenoside|berberine|phytochem",
    "纳米/递送": r"nanoparticle|nanomedicine|drug delivery|liposome|exosome|biomaterial|hydrogel",
    "疫苗/抗体": r"vaccine|antibody|monoclonal|CAR-?T|bispecific",
    # ---- 2026-10-01 新增 4 条：与新增检索块 B6–B10 一一对应 ----
    # 背景：检索块只决定"候选池"，相关性门槛判的是 TAGS。
    # 若不补这 4 条，B6–B10 找回来的药代动力学 / 临床试验 / 动物模型 / 分子机制文章
    # **命中检索块却卡在 `if not tags` 被整批剔除**——等于新块白加。
    # 这是与 [ERR-2026W40-40] 同型的缺陷：**检索口径与筛选口径必须成对审计**。
    "药代/药效评价": r"pharmacokinetic|pharmacodynamic|ADMET|dose-?response|IC50|bioavailability|therapeutic (effect|efficacy)|dose-?dependen",
    "临床研究与RCT": r"randomized controlled trial|randomi[sz]ed|double-?blind|placebo|cohort study|case-?control|clinical trial|real-?world|observational study",
    "动物模型/在体": r"mouse model|murine|rat model|animal model|in vivo|knockout mouse|transgenic mouse|xenograft|knock-in mouse",
    "分子机制/信号通路": r"signaling pathway|signal transduction|molecular mechanism|transcription factor|ubiquitin|autophagy|apoptosis|post-?translational|protein stability|phosphorylat",
}

# 2026-10-01 新增：**生信核心标签子集**（用于审计「池里还剩多少生信」）。
# ⚠️ 口径踩坑（实测 3 天窗口 / target 400，三种口径差一个数量级）：
#   (a) `mode=='纯生信' or public_data=='Y'`      → 14.8%  ← **严重低估**
#       理由：mode 判定要求文章**一个湿实验动词都不能有**，而先生真正要仿写的
#       「生信稿」大量是干湿结合（既用 GEO/TCGA 又写 "we cultured cells"），被判成"湿实验为主"。
#   (b) 含边界标签的全集（+肿瘤微环境/免疫浸润、生物标志物/诊断）→ 92.6% ← **严重灌水**
#       理由：「生物标志物/诊断」等湿实验也大面积使用，不能当作生信专属。
#   (c) **生信核心 13 标签（本集合，已剔除 2 个边界标签）→ 82.2%** ← 采信口径
# 故本集合**刻意排除**「肿瘤微环境/免疫浸润」「生物标志物/诊断」这两个宽标签。
BIOINFO_TAGS = {
    "单细胞/空转", "机器学习/深度学习", "孟德尔随机化/因果推断", "多组学整合",
    "转录组/表达谱", "蛋白组/代谢组", "表观遗传/甲基化", "微生物组/宏基因组",
    "网络药理学/分子对接", "GWAS/基因组变异",
    "预后模型/风险评分", "影像组学/病理AI", "CRISPR/基因编辑",
}
CANCER = {
    "乳腺癌": r"breast (cancer|carcinoma)|BRCA|triple-?negative",
    "肺癌": r"lung (adenocarcinoma|cancer|carcinoma)|NSCLC|SCLC",
    "结直肠癌": r"colorectal|colon cancer|rectal cancer|CRC",
    "肝癌": r"hepatocellular carcinoma|HCC|liver cancer",
    "胃癌": r"gastric (cancer|carcinoma)|stomach cancer",
    "胶质瘤": r"glioma|glioblastoma|GBM",
    "前列腺癌": r"prostate cancer",
    "卵巢癌": r"ovarian cancer",
    "胰腺癌": r"pancreatic (cancer|ductal)",
    "甲状腺癌": r"thyroid (cancer|carcinoma|papillary)",
    "血液肿瘤": r"leukemia|lymphoma|myeloma|AML|CLL",
    "黑色素瘤": r"melanoma",
    "食管癌": r"esophageal (cancer|carcinoma)",
    "膀胱/肾癌": r"bladder cancer|renal cell carcinoma|RCC",
    "宫颈/子宫内膜癌": r"cervical cancer|endometrial",
    "骨肉瘤": r"osteosarcoma|sarcoma",
    "头颈癌": r"head and neck (cancer|squamous)",
    "泛癌": r"pan-?can\w+|across \d+ cancer types|multiple cancer types",
}
PUBLIC_DATA = (r"TCGA|GEO|Gene Expression Omnibus|GTEx|UK Biobank|ArrayExpress|ICGC|CPTAC|cBioPortal|"
               r"GEPIA|TIMER|CCLE|GDSC|DepMap|CELLxGENE|Single Cell Portal|GTEx|dbGaP|FinnGen|"
               r"ProteomeXchange|PRIDE|MetaboLights|ENCODE|Human Cell Atlas|1000 Genomes|GWAS Catalog|"
               r"public(ly)? available (dataset|data)|public database|open (dataset|data)|in-?house cohort")
WETLAB = (r"we (performed|conducted|established|cultured|transfected|treated|constructed|generated) "
          r"|mice were|mouse model|rats were|xenograft|tumor-?bearing mice|western blot|qRT-?PCR|"
          r"immunohistochem|ELISA|flow cytom|CCK-?8|colony formation|wound healing assay|transwell|"
          r"cell viability assay|patient samples were collected|we recruited|were enrolled in this study|"
          r"knockdown|overexpress|siRNA|shRNA|lentivir|organoid|zebrafish|cell line|in vitro experiment")
ALGO = (r"we (develop|propose|present|constructed|built|design)\w*|novel (algorithm|framework|tool|pipeline|model)|"
        r"open[- ]source|source code|GitHub|R package|Python package|web server|webenchmark|benchmark\w*|"
        r"computational (framework|pipeline|tool)|deep learning (model|framework)|machine learning (model|framework)")


def http_get(url, tries=3):
    last = None
    for i in range(tries):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=45).read()
        except Exception as e:  # 网络抖动重试
            last = e
            time.sleep(1.5 * (i + 1))
    raise last


def esearch(term, retmax, sort="relevance"):
    u = (f"{EUTILS}/esearch.fcgi?db=pubmed&retmode=json&retmax={retmax}&sort={sort}"
         f"&term={urllib.parse.quote(term)}")
    d = json.loads(http_get(u).decode("utf-8", "ignore"))
    r = d["esearchresult"]
    return int(r.get("count", 0)), r.get("idlist", [])


def esummary(pmids):
    out = {}
    for i in range(0, len(pmids), 200):
        chunk = pmids[i:i + 200]
        u = f"{EUTILS}/esummary.fcgi?db=pubmed&retmode=json&id={','.join(chunk)}"
        d = json.loads(http_get(u).decode("utf-8", "ignore"))
        for k, v in d.get("result", {}).items():
            if k == "uids":
                continue
            out[k] = v
        time.sleep(0.4)
    return out


def efetch_xml(pmids):
    """返回 {pmid: {...}}，含摘要、MeSH、出版类型、期刊全称、ISSN。"""
    out = {}
    for i in range(0, len(pmids), 150):
        chunk = pmids[i:i + 150]
        u = f"{EUTILS}/efetch.fcgi?db=pubmed&retmode=xml&rettype=abstract&id={','.join(chunk)}"
        try:
            root = ET.fromstring(http_get(u))
        except Exception:
            time.sleep(2)
            continue
        for art in root.findall(".//PubmedArticle"):
            cit = art.find("MedlineCitation")
            if cit is None:
                continue
            pmid = (cit.findtext("PMID") or "").strip()
            a = cit.find("Article")
            if a is None:
                continue
            # 摘要（结构化：拼接 Label）
            ab_parts = []
            for ab in a.findall(".//Abstract/AbstractText"):
                lab = ab.get("Label")
                txt = "".join(ab.itertext()).strip()
                ab_parts.append(f"{lab}: {txt}" if lab else txt)
            abstract = " ".join(ab_parts)
            # 期刊
            j = a.find("Journal")
            iso = full = issn = ""
            if j is not None:
                iso = (j.findtext("ISOAbbreviation") or "").strip()
                full = (j.findtext("Title") or "").strip()
                issn = (j.findtext("ISSN") or "").strip()
            # 出版类型
            ptypes = [p.text or "" for p in a.findall(".//PublicationType")]
            # MeSH
            mesh = []
            for m in cit.findall(".//MeshHeading/DescriptorName"):
                if m.text:
                    mesh.append(m.text)
            # DOI / PMCID —— 必须限定在 PubmedData 下
            # 说明：切勿用 ".//ArticleIdList/ArticleId"，该 XPath 会递归命中
            # ReferenceList/*/ArticleIdList（参考文献自身的 DOI/PMCID），
            # 且循环覆盖导致「最后一条胜出」，产出与外源文献错位的假 ID。
            doi = pmcid = ""
            for aid in art.findall("./PubmedData/ArticleIdList/ArticleId"):
                t = (aid.get("IdType") or "").lower()
                if t == "doi":
                    doi = (doi or (aid.text or "").strip())
                elif t == "pmc":
                    pmcid = (pmcid or (aid.text or "").strip())
            out[pmid] = {"abstract": abstract, "journal_iso": iso, "journal_full": full,
                         "issn": issn, "pubtypes": ptypes, "mesh": mesh,
                         "doi": doi, "pmcid": pmcid}
        time.sleep(0.4)
    return out


EXCLUDE_PT = {"Editorial", "Comment", "Published Erratum", "Retraction of Publication",
              "Retracted Publication", "News", "Biography", "Historical Article",
              "Congress", "Interview", "Personal Narrative", "Autobiography",
              "Newspaper Article", "Published Erratum", "Expression of Concern"}

# ⚠️ 2026-09-28（W40 建池）新增：**预印本排除**
# 背景：PubMed 自 2020 起收录 bioRxiv / medRxiv / Research Square 预印本，
# 其 pubtypes 形如 `Journal Article;Preprint`——含 "Journal Article" 字样，
# 故 **不会被 EXCLUDE_PT 拦下**，会静默进入语料。
# 后果（W40 首次实测）：11 篇预印本对应的 3 个"期刊"（bioRxiv / medRxiv / Res Sq）
# **不存在 JIF，也无法从 OpenAlex 取到 2yrMCC** → 池中出现 11 条 PENDING，
# 直接违反周池硬要求「IF 分层无 UNBINNED」。
# 处置：与 W39 口径对齐（W39 池中预印本 = 0 篇），在初筛阶段显式剔除，
# 而且**单列剔除原因**（不并入"非研究性文献"，避免掩盖真实构成）。
PREPRINT_PT = {"Preprint"}


def tag_it(text):
    tl = text.lower()
    tags = [k for k, pat in TAGS.items() if re.search(pat, tl, re.I)]
    cancers = [k for k, pat in CANCER.items() if re.search(pat, tl, re.I)]
    has_pub = bool(re.search(PUBLIC_DATA, text, re.I))
    has_wet = bool(re.search(WETLAB, text, re.I))
    has_algo = bool(re.search(ALGO, text, re.I))
    if has_pub and not has_wet:
        mode = "纯生信"
    elif has_pub and has_wet:
        mode = "干湿结合"
    elif has_wet and not has_pub:
        mode = "湿实验为主"
    else:
        mode = "计算/未见数据来源"
    return tags, cancers, has_pub, has_wet, has_algo, mode


def _load_cache(path):
    if os.path.exists(path):
        try:
            return json.load(open(path, encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_cache(path, obj):
    d = os.path.dirname(os.path.abspath(path))
    os.makedirs(d, exist_ok=True)
    json.dump(obj, open(path, "w", encoding="utf-8"), ensure_ascii=False)


def get_summary(pmids, cache_path):
    """带缓存的 esummary。缓存让第二遍（补 IF 后重排）无需再请求 NCBI。"""
    cache = _load_cache(cache_path)
    todo = [p for p in pmids if p not in cache]
    print(f"[esummary] 命中缓存 {len(pmids)-len(todo)} / 需抓取 {len(todo)}")
    if todo:
        cache.update(esummary(todo))
        _save_cache(cache_path, cache)
    return cache


def get_detail(pmids, cache_path):
    cache = _load_cache(cache_path)
    todo = [p for p in pmids if p not in cache]
    print(f"[efetch] 命中缓存 {len(pmids)-len(todo)} / 需抓取 {len(todo)}")
    if todo:
        cache.update(efetch_xml(todo))
        _save_cache(cache_path, cache)
    return cache


def load_if_table(path):
    t = {}
    if path and os.path.exists(path):
        with open(path, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                iso = (r.get("journal_iso") or "").strip()
                if iso:
                    t[iso.lower()] = r
    return t


def to_bin(v):
    try:
        x = float(v)
    except (TypeError, ValueError):
        return "UNBINNED"
    if x < 1:
        return "<1"
    if x < 3:
        return "1-3"
    if x < 5:
        return "3-5"
    if x < 10:
        return "5-10"
    return ">10"


def score_row(r):
    s = 0
    s += 3 * len(r["tags"])
    s += 2 * len(r["cancers"])
    # 2026-10-01 调整：先生要求「不局限生信，整个生物医药都可以」，
    # 原权重 {纯生信:4, 干湿结合:2} 会让湿实验文章在 top520 里系统性靠后。
    # 新权重：干湿结合最高（真实写作里既有数据又有结论，最利于学表述），
    # 纯生信与湿实验为主同档（先生本人做生信，但训练不该只剩一类）。
    # 四类占比须在 meta 的 mode_distribution 中如实上报，发现失衡即告警。
    s += {"纯生信": 3, "干湿结合": 4, "湿实验为主": 3, "计算/未见数据来源": 1}.get(r["mode"], 0)
    s += 2 if r["has_algo"] else 0
    s += min(len(r["abstract"]) // 400, 3)
    s += {"<1": 0, "1-3": 2, "3-5": 4, "5-10": 6, ">10": 8}.get(r["if_bin"], 1)
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--start", required=True, help="YYYY/MM/DD（EDAT 起）")
    ap.add_argument("--end", required=True, help="YYYY/MM/DD（EDAT 止）")
    ap.add_argument("--target", type=int, default=520)
    ap.add_argument("--max-per-block", type=int, default=2500)
    ap.add_argument("--min-bioinfo-ratio", type=float, default=0.25,
                    help="生信基本盘保底比例（默认 0.25）：命中生信核心标签的篇数低于此比例时，"
                         "从落选候选中按 score 补生信文章进来。放开到整个生物医药后防检索漂移；"
                         "实测常规窗口该比例约 82%，故只在异常窗口兜底。设 0 关闭。")
    ap.add_argument("--min-abstract", type=int, default=200)
    ap.add_argument("--if-table", default="")
    ap.add_argument("--cache-dir", default="", help="元数据/摘要缓存目录（默认 <out-dir>/_cache）")
    ap.add_argument("--counts-only", action="store_true")
    ap.add_argument("--no-if", action="store_true", help="跳过 IF 补录（离线模式）")
    a = ap.parse_args()

    os.makedirs(a.out_dir, exist_ok=True)
    window = f'("{a.start}"[EDAT] : "{a.end}"[EDAT])'

    # --- 1. 检索 ---
    block_counts, pmid_block = OrderedDict(), {}
    all_pmids = []
    for name, blk in QUERY_BLOCKS.items():
        term = f"({blk}) AND {window} AND english[lang]"
        cnt, ids = esearch(term, a.max_per_block)
        block_counts[name] = {"hits": cnt, "retrieved": len(ids)}
        print(f"[esearch] {name}: 命中 {cnt}，取回 {len(ids)}")
        for p in ids:
            pmid_block.setdefault(p, []).append(name)
            all_pmids.append(p)
        time.sleep(0.4)
    uniq = list(dict.fromkeys(all_pmids))
    print(f"[esearch] 去重后 PMID：{len(uniq)}")

    if a.counts_only:
        json.dump({"window": window, "blocks": block_counts, "unique_pmids": len(uniq)},
                  open(os.path.join(a.out_dir, "search_counts.json"), "w"), ensure_ascii=False, indent=2)
        return

    # --- 2/3. 元数据 ---
    cache_dir = a.cache_dir or os.path.join(a.out_dir, "_cache")
    print("[esummary] 拉取元数据 ...")
    summ = get_summary(uniq, os.path.join(cache_dir, "summary.json"))

    # --- 4. 摘要 ---
    print("[efetch] 拉取结构化摘要 ...")
    det = get_detail(uniq, os.path.join(cache_dir, "detail.json"))
    print(f"[efetch] 获得摘要 {len(det)} 篇")

    # --- 5. 初筛 ---
    rows, dropped = [], Counter()
    for pmid in uniq:
        s, d = summ.get(pmid), det.get(pmid)
        if not s or not d:
            dropped["元数据缺失"] += 1
            continue
        pts = set(d["pubtypes"]) | set(s.get("pubtype") or [])
        if pts & EXCLUDE_PT:
            dropped["非研究性文献"] += 1
            continue
        if pts & PREPRINT_PT:
            dropped["预印本（无 JIF，非同行评审发表稿）"] += 1
            continue
        if len(d["abstract"]) < a.min_abstract:
            dropped["摘要过短/无摘要"] += 1
            continue
        text = (s.get("title", "") + " " + d["abstract"] + " " + " ".join(d["mesh"]))
        tags, cancers, has_pub, has_wet, has_algo, mode = tag_it(text)
        if not tags:
            # 2026-10-01 改名：原文案「无生信/组学信号」**与事实不符**——
            # TAGS 词典早已覆盖心血管/神经/中药/纳米/疫苗等非生信领域，
            # 真正把范围锁死在生信的是 QUERY_BLOCKS（候选池），不是这一行。
            # 但它仍会误杀纯临床观察、纯药效学、纯生化这类"无领域标签"的生物医学文章，
            # 故保留剔除，但**剔除原因必须如实描述**，否则复盘时会误判为"生信门槛"。
            dropped["未识别到生物医药领域信号"] += 1
            continue
        rows.append({
            "pmid": pmid, "title": re.sub(r"<[^>]+>", "", s.get("title", "")).strip(),
            "journal_iso": d["journal_iso"], "journal_full": d["journal_full"],
            "issn": d["issn"], "pubdate": s.get("pubdate", ""), "epubdate": s.get("epubdate", ""),
            "doi": d["doi"], "pmcid": d["pmcid"], "oa": "OA" if d["pmcid"] else "非OA",
            "pubtypes": ";".join(sorted(pts)), "mesh": ";".join(d["mesh"][:12]),
            "tags": ";".join(tags), "cancers": ";".join(cancers),
            "mode": mode, "public_data": "Y" if has_pub else "N",
            "has_algo": "Y" if has_algo else "N",
            "matched_blocks": ";".join(pmid_block.get(pmid, [])),
            "abstract": d["abstract"],
        })
    print(f"[初筛] 通过 {len(rows)}；剔除 {dict(dropped)}")

    # --- 9a. IF 分层（先补 IF 表，再排序） ---
    if not a.no_if and not a.if_table:
        print("[journal_if] 未提供指标表，IF 将全部标 UNBINNED")
    iftab = load_if_table(a.if_table)
    for r in rows:
        rec = iftab.get(r["journal_iso"].lower(), {})
        r["if_latest"] = rec.get("if_latest", "")
        r["if_year_label"] = rec.get("if_year_label", "")
        r["if_source_url"] = rec.get("if_source_url", "")
        r["if_bin"] = to_bin(r["if_latest"])

    # --- 7/8. 排序 + 精选 ---
    for r in rows:
        r["score"] = score_row(r)
    rows.sort(key=lambda r: (-r["score"], r["journal_iso"]))
    picked = rows[:a.target] if len(rows) > a.target else rows
    print(f"[精选] 候选 {len(rows)} → 入选 {len(picked)}（目标 {a.target}）")

    # 2026-10-01 新增：**生信基本盘保底补齐**
    # 背景：先生指定「不局限生信，整个生物医药都可以」⇒ 已新增 B6–B10 五块把范围放开。
    # 实采 3 天窗口（2026/09/28–30, target 400）时，用**过窄口径**（mode=='纯生信' 或 public_data=='Y'）
    # 曾测出生信仅 14.8%——后证明那是口径错误（干湿结合的生信稿被算成湿实验），真实占比 82.2%。
    # 保底机制因此**只作兜底**（默认 0.25，常规窗口约 82% 几乎不触发）：
    # 它的作用不是"强行拉高生信占比"，而是**万一某日检索漂移把生信挤干时能自动补回**，
    # 而不是静默让先生的日课练不到生信稿。(--min-bioinfo-ratio 0 可关闭)
    # 未入选的候选按 score 取最高的生信文章补进来——**补的是"文章"，不是"标签"**，
    # 因此不存在"贴标签凑数"的风险；补超额的部分不裁掉其它类，只放宽入选数上限。
    balance_report = {"补齐生信篇数": 0, "补齐前生信": 0, "配比目标": a.min_bioinfo_ratio}
    if a.min_bioinfo_ratio > 0:
        def _is_bioinfo(r):
            # 判定口径 = 命中 BIOINFO_TAGS 任一**核心**标签（见集合上方注释）。
            # 不用 mode=='纯生信'（要求零湿实验动词，会把先生主业常见的"干湿结合生信稿"
            # 误判成湿实验，实测低估到 14.8%）；
            # 也不用全集标签（会把湿实验的 biomarker 研究算成生信，实测灌水到 92.6%）。
            return bool(BIOINFO_TAGS & set(r.get("tags", "").split(";")))

        balance_report["补齐前生信"] = sum(1 for r in picked if _is_bioinfo(r))
        want = int(len(picked) * a.min_bioinfo_ratio)
        if balance_report["补齐前生信"] < want:
            have = {r["pmid"] for r in picked}
            need = want - balance_report["补齐前生信"]
            cand = [r for r in rows if r["pmid"] not in have and _is_bioinfo(r)][:need]
            picked = picked + cand
            balance_report["补齐生信篇数"] = len(cand)
            balance_report["补齐后生信"] = balance_report["补齐前生信"] + len(cand)
            rows.sort(key=lambda r: (-r["score"], r["journal_iso"]))
    print(f"[保底] 生信 {balance_report.get('补齐前生信', 0)} → "
          f"{balance_report.get('补齐后生信', balance_report.get('补齐前生信', 0))} 篇"
          f"（占比目标 {a.min_bioinfo_ratio:.0%}；补齐 {balance_report['补齐生信篇数']} 篇）")

    # --- 10. 输出 ---
    cols = ["pmid", "title", "journal_iso", "journal_full", "issn", "if_latest", "if_year_label",
            "if_bin", "pubdate", "epubdate", "doi", "pmcid", "oa", "pubtypes", "tags", "cancers",
            "mode", "public_data", "has_algo", "matched_blocks", "score", "if_source_url", "mesh",
            "abstract"]
    with open(os.path.join(a.out_dir, "papers_master.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in picked:
            w.writerow({k: r.get(k, "") for k in cols})

    bins = OrderedDict((k, 0) for k in ["<1", "1-3", "3-5", "5-10", ">10", "UNBINNED"])
    for r in picked:
        bins[r["if_bin"]] += 1
    modes = Counter(r["mode"] for r in picked)
    tagc = Counter(t for r in picked for t in r["tags"].split(";") if t)
    canc = Counter(c for r in picked for c in r["cancers"].split(";") if c)
    jc = Counter(r["journal_iso"] for r in picked)
    oa = Counter(r["oa"] for r in picked)

    # 2026-10-01 新增：统计各检索块对**入选文章**的实际贡献（不是 esearch 命中数——
    # 命中数只说明"找得到"，贡献数才说明"真的进池了"，两者可以差很远）。
    block_contrib = {}
    for r in picked:
        bs = [x for x in (r.get("matched_blocks") or "").split(";") if x]
        for b in (bs or ["<未标记所属块>"]):
            block_contrib[b] = block_contrib.get(b, 0) + 1

    summary = {
        "生成日期": date.today().isoformat(),
        "检索时间窗(EDAT)": window,
        "检索块命中": block_counts,
        "去重PMID": len(uniq),
        "初筛通过": len(rows),
        "入选篇数": len(picked),
        "IF区间分布": bins,
        "研究模式分布": dict(modes),
        "OA状态": dict(oa),
        "Top主题标签": tagc.most_common(30),
        "Top疾病/癌种": canc.most_common(25),
        "Top期刊": jc.most_common(25),
        # 2026-10-01 新增：先生要求「不局限生信」，故必须能**审计实际配比**，
        # 否则改了检索块与权重也不知道池里到底还剩多少生信。
        # ⚠️ 口径（实测踩坑，三种口径差一个数量级，勿改回）：
        #   ① mode=='纯生信' or public_data=='Y'   → 14.8%（低估：干湿结合的生信稿被算成湿实验）
        #   ② 生信核心 13 标签（BIOINFO_TAGS）     → 82.2%（**采信**）
        #   ③ BIOINFO_TAGS + 2 个边界标签          → 92.6%（灌水：湿实验的 biomarker 研究被算生信）
        "生信信号占比": {
            "口径": "命中生信核心 13 标签（BIOINFO_TAGS；不含「肿瘤微环境/免疫浸润」「生物标志物/诊断」两个边界标签）",
            "生信篇数": sum(1 for r in picked if BIOINFO_TAGS & set(r.get("tags", "").split(";"))),
            "入选篇数": len(picked),
            "生信占比": f"{sum(1 for r in picked if BIOINFO_TAGS & set(r.get('tags','').split(';')))/max(len(picked),1)*100:.1f}%",
            "失衡告警": "生信占比 <25% 或 >90% 即告警（放开领域后既不把生信挤干，也不退回纯生信）",
        },
        "生信保底补齐": balance_report,
        "检索块贡献(入选文章)": block_contrib,
    }
    json.dump(summary, open(os.path.join(a.out_dir, "bins_summary.json"), "w"),
              ensure_ascii=False, indent=2)
    json.dump({"tags": tagc.most_common(40), "cancers": canc.most_common(30),
               "journals": jc.most_common(40), "modes": dict(modes)},
              open(os.path.join(a.out_dir, "topic_clusters.json"), "w"), ensure_ascii=False, indent=2)

    with open(os.path.join(a.out_dir, "search_log.md"), "w", encoding="utf-8") as f:
        f.write(f"# 检索日志（自动生成 {date.today().isoformat()}）\n\n")
        f.write(f"- 时间窗（EDAT）：{a.start} ~ {a.end}\n- 入选：{len(picked)} 篇 / 候选 {len(rows)} 篇\n")
        f.write(f"- 去重 PMID：{len(uniq)}\n\n## 检索块\n\n| 检索块 | 命中 | 取回 |\n|---|---|---|\n")
        for k, v in block_counts.items():
            f.write(f"| {k} | {v['hits']} | {v['retrieved']} |\n")
        f.write(f"\n## 剔除统计\n\n| 原因 | 篇数 |\n|---|---|\n")
        for k, v in dropped.items():
            f.write(f"| {k} | {v} |\n")
        f.write("\n## 检索式原文\n\n```\n")
        for k, v in QUERY_BLOCKS.items():
            f.write(f"# {k}\n({v}) AND {window} AND english[lang]\n\n")
        f.write("```\n")

    print("\n=== IF 区间分布 ===")
    for k, v in bins.items():
        print(f"  {k:<9} {v}")
    print("=== 研究模式 ===")
    for k, v in modes.most_common():
        print(f"  {k:<12} {v}")
    print("\n=== Top 主题 ===")
    for k, v in tagc.most_common(12):
        print(f"  {k:<22} {v}")
    print(f"\n[输出] {a.out_dir}/papers_master.csv 等 4 个文件")


if __name__ == "__main__":
    sys.exit(main())
