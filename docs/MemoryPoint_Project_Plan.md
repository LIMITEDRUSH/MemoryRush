# MemoryPoint 项目计划

## 1. 项目名称

**MemoryPoint: Salient Reading Memory Extraction and Dynamic Recall for Personal AI Assistants**

中文定位：

**一个模拟人类阅读记忆形成机制的个人 AI 阅读助手。**

它不是普通 PDF Chatbot，也不是普通 RAG 知识库。它的核心目标是：

> 用户把文章发给系统后，AI 给出文章总结和记忆点判断；用户可以在总结或原文段落上标注 highlight，系统再把这些显式反馈写入长期记忆。之后用户既可以继续阅读新文章，也可以和 AI 对话，让 AI 基于读过的文章、用户标注过的重点和长期记忆进行回答。

## 2. 项目动机

普通 RAG 系统更像搜索引擎：

```text
用户提问
→ 检索相关 chunk
→ 交给 LLM 回答
```

但人类阅读不是这样。人读完一篇文章后，通常不会记住全部细节，而是留下几个深刻记忆点：

- 一个新概念
- 一个反直觉观点
- 一个重要方法
- 一个和旧知识冲突的结论
- 一个未来可能用到的框架
- 一个能和过去阅读内容连接起来的想法

MemoryPoint 的目标是让 AI 做类似事情，同时让用户参与记忆形成：

```text
用户发送文章
→ AI 生成文章总结
→ AI 判断候选记忆点
→ 用户对总结段落 / 原文段落 highlight
→ 系统结合 AI 判断和用户标注给记忆点打分
→ 存入长期记忆库
→ 和旧记忆建立关联
→ 后续阅读时自动联想
→ 被反复召回的记忆增强
→ 长期未使用的记忆衰减
```

## 3. 与普通 RAG 的区别

| 普通 RAG | MemoryPoint |
|---|---|
| 保存所有 chunk | 选择性提取高价值记忆点 |
| 被动检索 | 阅读后主动形成记忆 |
| 主要靠语义相似度 | 综合显著性、重要性、相关性、使用频率 |
| 更像搜索 | 更像长期学习 |
| 处理“原文哪里提到过” | 处理“我真正记住了什么” |
| 静态知识库 | 动态记忆系统 |
| 不会遗忘 | 可强化、可衰减 |

MemoryPoint 不替代 RAG，而是在 RAG 上增加一层长期记忆机制：

```text
Raw Document Store
+ Chunk-based RAG
+ Salient Memory Point Layer
+ Dynamic Reinforcement and Decay
+ Cross-document Recall
```

## 4. 核心功能

### 4.1 文章输入与阅读交互

用户交互方式应围绕“阅读一篇文章”展开，而不是只做上传文件后的问答。

核心流程：

```text
用户上传 / 粘贴 / 发送文章
→ 系统解析文章
→ 显示原文或段落化阅读视图
→ AI 生成结构化总结
→ AI 标出候选记忆点
→ 用户在总结段落或原文段落上 highlight
→ 用户可确认、编辑、删除 AI 记忆点
→ 系统更新长期记忆
→ 用户可继续对话
```

支持输入：

- 直接粘贴文章文本
- 上传 PDF
- 上传 DOCX
- 上传 Markdown / TXT
- 输入网页 URL

阅读界面需要支持：

- 原文段落展示
- AI 总结展示
- 候选记忆点展示
- 段落级 highlight
- highlight 类型选择，例如：
  - important
  - surprising
  - useful
  - disagree
  - remember this
- 用户对 AI 记忆点 Accept / Edit / Reject

### 4.2 文档读取

支持读取：

- PDF
- DOCX
- Markdown
- TXT
- 网页 URL
- 后续可扩展到 PPT、HTML、图片 OCR

文档解析后保存：

- 原文
- chunk
- 页码
- section
- source path / URL
- created time

### 4.3 文章总结

系统需要先为用户生成一份自然、连贯、易于阅读的文章总结，而不是直接将内容提取为记忆点并存入记忆库。总结应尽量像普通的文章摘要一样，以完整段落呈现文章的主题、核心观点、主要论证和结论，帮助用户快速理解文章内容。

总结可以根据文章长度分为多个段落。每个段落都应支持用户主动选择并标记为 highlight，用户可以通过点击段落旁的 highlight 按钮完成标注，也可以使用快捷键直接标记当前段落。被标记的段落应显示明显的视觉状态，并记录对应的文章、段落、来源位置、highlight 类型和用户备注。

用户可以对总结中的任意段落进行以下操作：

- Highlight 当前段落
- 取消 Highlight
- 选择 Highlight 类型，例如 important、surprising、useful、disagree、remember this
- 添加个人备注
- 查看该总结段落对应的原文证据
- 使用快捷键快速 Highlight 当前选中的段落

总结中的 Highlight 不应直接等同于最终记忆点，而应作为用户反馈信号，用于提高相关内容的个人相关性和记忆评分。系统可以结合文章内容、AI 对重要性的判断以及用户的 Highlight 行为，进一步生成候选 memory points，并由用户确认、编辑或删除。

示例：

```text
This article argues that RAG hallucination is often caused by retrieval failures rather than generation failures. [Highlight]

The author explains that retrieval quality determines whether the model receives enough relevant evidence. Reranking can improve context precision by filtering out noisy or less relevant chunks. [Highlight]

The article also points out that larger context windows do not completely replace retrieval, because adding more context does not guarantee that the model will receive the right evidence. [Highlight]
```

在交互上，用户可以点击任意段落旁的 Highlight 按钮，也可以先选中段落后使用快捷键完成标注。系统应支持配置快捷键，例如使用 `H` 标记或取消当前段落的 Highlight，使用数字键选择 Highlight 类型。
### 4.4 候选记忆点提取

系统从文章中提取候选 memory points。每个 memory point 不是普通摘要，而是“值得长期记住的想法”。

示例：

```json
{
  "memory_id": "mp_001",
  "content": "RAG 的幻觉问题很多时候来自检索失败，而不只是生成失败。",
  "source": "rag_failure_paper.pdf",
  "page": 6,
  "type": "conceptual_insight",
  "evidence": "原文证据片段",
  "tags": ["RAG", "hallucination", "retrieval"],
  "created_at": "2026-08-09"
}
```

### 4.5 用户 Highlight 反馈

用户可以对 AI 总结中的段落或原文段落进行 highlight。这个动作应该成为 memory scoring 的重要信号。

highlight 记录示例：

```json
{
  "highlight_id": "hl_001",
  "document_id": "doc_001",
  "paragraph_id": "p_014",
  "text": "RAG hallucination often comes from retrieval failure rather than generation failure.",
  "label": "important",
  "user_note": "This is useful for my MemoryPoint project.",
  "created_at": "2026-08-09T21:20:00"
}
```

Highlight 对系统的作用：

- 提高对应段落生成 memory point 的概率
- 提高相关 memory point 的 `personal_relevance`
- 提高 `user_feedback_score`
- 作为未来个性化 ranking 的训练标签
- 帮助系统学习用户真正觉得什么值得记住

Highlight 类型建议：

| 类型 | 含义 | 对分数影响 |
|---|---|---:|
| important | 用户认为重要 | 强提升 |
| surprising | 反直觉 / 新鲜 | 提升 surprise |
| useful | 未来可能用到 | 提升 usefulness |
| disagree | 用户不同意 | 建立 conflict / critique 关系 |
| remember_this | 明确要求记住 | 强提升并降低 decay |
| unclear | 用户觉得不理解 | 可触发解释 / 对话 |

### 4.6 记忆点评分

每个 memory point 需要一个初始分数 `base_score`。

建议评分维度：

| 维度 | 含义 |
|---|---|
| Importance | 是否是文章核心观点 |
| Novelty | 是否新颖，不是常识废话 |
| Personal Relevance | 是否和用户长期兴趣或 highlight 相关 |
| Future Usefulness | 未来是否可能用于写作、学习、项目、决策 |
| Surprise | 是否反直觉、容易留下印象 |
| Cross-document Connectivity | 是否能连接到过去读过的内容 |
| Evidence Strength | 是否有清晰原文证据支持 |
| User Highlight | 用户是否主动标注该段落 |

初始评分公式：

```text
base_score =
+ 0.18 * importance
+ 0.12 * novelty
+ 0.18 * personal_relevance
+ 0.14 * future_usefulness
+ 0.10 * surprise
+ 0.12 * cross_document_connectivity
+ 0.06 * evidence_strength
+ 0.10 * user_highlight_signal
```

### 4.7 动态强化和衰减

MemoryPoint 的关键创新之一是：记忆不是静态的。

如果一个记忆点反复被回想起，它的重要性应该上升。  
如果一个记忆点长期没有被使用，它的重要性应该下降。

动态记忆强度公式：

```text
memory_strength =
base_score * exp(-decay_rate * days_since_last_recall)
+ alpha * log(1 + recall_count)
+ beta * recent_recall_bonus
+ gamma * user_feedback_score
```

变量解释：

| 变量 | 含义 |
|---|---|
| base_score | 初始记忆重要性 |
| decay_rate | 遗忘速度 |
| days_since_last_recall | 距离上次召回的天数 |
| recall_count | 总召回次数 |
| recent_recall_bonus | 最近反复出现的额外强化 |
| user_feedback_score | 用户收藏、编辑、确认、忽略等反馈 |

不同记忆类型可以有不同衰减速度：

| 记忆类型 | 衰减速度 |
|---|---|
| 核心概念 | 慢 |
| 事实细节 | 中等 |
| 临时任务 | 快 |
| 用户收藏 | 很慢 |
| 被用户标记无用 | 快速降权 |
| 被多篇文章支持 | 慢 |

### 4.5 召回事件日志

系统需要记录每次记忆被召回的原因。

召回事件示例：

```json
{
  "memory_id": "mp_001",
  "event_type": "used_in_answer",
  "query": "How does reranking reduce hallucination in RAG?",
  "timestamp": "2026-08-09T20:30:00",
  "reinforcement": 0.8
}
```

召回事件权重：

| 事件 | 强化程度 |
|---|---:|
| 用户主动搜索到 | +1.0 |
| 被系统用于回答问题 | +0.8 |
| 新文章触发联想 | +0.6 |
| 用户点击或收藏 | +1.5 |
| 用户编辑记忆 | +1.2 |
| 只出现在候选列表 | +0.2 |
| 用户标记无用 | -2.0 |

### 4.8 对话模式

除了阅读界面，系统还需要支持对话。

对话能力包括：

- 问当前文章
- 问历史读过的文章
- 问某个主题下记住了什么
- 要求解释某个 highlighted 段落
- 要求比较新文章和旧记忆
- 要求列出支持 / 冲突 / 延伸关系

示例问题：

```text
这篇文章最值得记住的点是什么？
我之前读过哪些内容和这篇文章有关？
我 highlight 的这段话为什么重要？
关于 RAG hallucination，我目前的长期记忆里有哪些观点？
这篇文章有没有和我之前读过的观点冲突？
```

对话回答必须尽量包含：

- answer
- cited source
- memory points used
- highlighted passages used
- confidence / insufficient evidence

### 4.9 新文章触发旧记忆

当用户阅读新文章时，系统不只是总结新文章，还要回答：

```text
这篇文章让我想起了你之前读过的哪些内容？
它支持、反驳、补充或延伸了哪些旧记忆？
```

示例输出：

```text
This article connects to three previous memory points:

1. It extends your previous memory that RAG hallucination often comes from retrieval failure.
2. It supports an earlier article arguing that reranking improves context precision.
3. It partially conflicts with a previous claim that larger context windows reduce the need for retrieval.
```

### 4.10 Memory Bank 页面

用户可以查看所有长期记忆：

- 按 score 排序
- 按 topic 筛选
- 按 source 查看
- 按最近召回时间排序
- 编辑记忆内容
- 删除错误记忆
- 收藏重要记忆
- 查看证据来源
- 查看由哪些 highlight 产生
- 查看被哪些对话召回过

## 5. 技术架构

```text
Document Ingestion Layer
  PDF / DOCX / Markdown / URL parser

Chunk Layer
  semantic chunking
  metadata preservation

RAG Layer
  embedding
  vector database
  retrieval
  reranking

Memory Extraction Layer
  candidate memory extraction
  memory type classification
  source evidence binding

Memory Ranking Layer
  base score calculation
  ML ranking model
  user relevance model

Dynamic Memory Layer
  recall logger
  reinforcement engine
  decay scheduler
  current strength update

Recall Layer
  semantic similarity
  memory strength
  graph links
  recency and usage

Application Layer
  Streamlit dashboard
  reading page
  highlight interaction
  chat page
  memory review page
  recall mode
  evaluation page
```

## 6. 推荐技术栈

| 模块 | 推荐工具 |
|---|---|
| PDF 解析 | PyMuPDF, pdfplumber |
| DOCX 解析 | python-docx |
| 网页解析 | BeautifulSoup, trafilatura |
| Chunking | LangChain, LlamaIndex, custom splitter |
| Embedding | bge-small, e5-base, sentence-transformers |
| Vector DB | Chroma, FAISS, Qdrant |
| Reranker | bge-reranker, cross-encoder |
| LLM | Qwen, Llama, OpenAI API, Ollama |
| 长期存储 | SQLite |
| 图谱关系 | NetworkX, optional Neo4j |
| UI | Streamlit |
| Evaluation | scikit-learn, pandas, numpy, RAGAS optional |

前端 MVP 可以先用 Streamlit 实现：

- `Upload / Paste Article`
- `Reading View`
- `Summary View`
- `Highlight Panel`
- `Memory Points`
- `Chat`
- `Memory Bank`

## 7. Machine Learning 化方向

为了让项目更像 ML 项目，而不是单纯 LLM App，核心任务应定义为：

> Predict which sentences or passages from a document are most likely to become long-term memory points.

即：

```text
输入：sentence / paragraph / chunk
输出：memory_score 或 high / medium / low salience label
```

### 7.1 ML 任务形式

可以设计为：

1. **Classification**
   判断一个 chunk 是否值得记住。

2. **Regression**
   预测 memory score。

3. **Learning to Rank**
   对同一篇文章中的候选 memory points 排序。

4. **Personalized Ranking**
   根据用户兴趣调整排序。

### 7.2 Baseline 模型

- TF-IDF + Logistic Regression
- TF-IDF + Random Forest
- Sentence-BERT embeddings + Logistic Regression
- Sentence-BERT embeddings + MLP

### 7.3 进阶模型

- BERT encoder + classification head
- ELECTRA encoder + ranking head
- Contrastive learning
- Learning-to-rank loss

### 7.4 数据构造

可以采用三种方式：

1. **人工标注小数据集**
   每篇文章标注 3-5 个最值得记住的 memory points。

2. **LLM-assisted weak labels**
   LLM 先生成候选 memory points，人工审核一部分。

3. **摘要数据集作为 proxy**
   被摘要选中的句子可视为高 salience，未选中的句子视为低 salience。

可用公开方向：

- arXiv / PubMed summarization
- CNN/DailyMail summarization
- sentence memorability datasets
- 自己收集的 AI / ML 文章

### 7.5 ML 特征

| 特征 | 解释 |
|---|---|
| semantic embedding | 文本语义表示 |
| document centrality | 是否接近文章核心主题 |
| novelty score | 和已有记忆是否不同 |
| personal relevance | 和用户兴趣是否相关 |
| highlight signal | 用户是否标注过该段落 |
| surprise score | 是否反常识 |
| evidence strength | 是否有明确证据 |
| cross-document connectivity | 是否连接到旧记忆 |
| position feature | 是否出现在标题、摘要、结论附近 |

## 8. 检索和召回排序

最终召回不应该只看 embedding similarity。

推荐公式：

```text
final_retrieval_score =
0.40 * semantic_similarity
+ 0.25 * memory_strength
+ 0.15 * personal_relevance
+ 0.10 * cross_document_connectivity
+ 0.05 * recency
+ 0.05 * source_quality
```

这样系统会更像人类记忆：

- 相关的容易被想起
- 重要的容易被想起
- 最近反复想起的更容易被想起
- 和多个旧概念连接的更容易被想起

## 9. MVP 开发计划

### Phase 1: 基础文档读取和 RAG

目标：先做出可运行系统。

功能：

- 上传 PDF / Markdown / TXT
- 文档解析
- chunking
- embedding
- Chroma / FAISS 存储
- 基础问答
- 返回 source 和 page

### Phase 2: Memory Point Extraction

目标：读完文章后自动提取记忆点。

功能：

- 文章总结
- 候选 memory points
- memory type
- source evidence
- tags
- base_score
- 用户 Accept / Edit / Reject
- 总结段落 / 原文段落 highlight
- highlight label 和 user note

### Phase 3: Dynamic Memory

目标：实现强化和衰减。

功能：

- recall_count
- last_recalled_at
- current_strength
- decay scheduler
- recall logger
- 用户反馈影响分数

### Phase 4: Recall Mode

目标：新文章触发旧记忆，并支持对话。

功能：

- 上传新文章
- 提取新 memory points
- 检索相关旧 memory points
- 输出支持、冲突、延伸关系
- 展示 evidence
- 支持对当前文章和历史记忆对话
- 回答时引用 source、memory point 和 highlight

### Phase 5: ML Ranking and Evaluation

目标：把项目提升为 ML 项目。

功能：

- 人工标注小数据集
- TF-IDF baseline
- Sentence-BERT baseline
- BERT / ELECTRA ranking model
- Precision@K
- NDCG@K
- ablation study

## 10. 实验设计

### 10.1 Baselines

需要和以下系统比较：

1. **Standard RAG**
   只用 chunk retrieval。

2. **Summary-based Memory**
   每篇文章只存摘要。

3. **Static Memory Points**
   有 memory points，但没有强化和衰减。

4. **MemoryPoint**
   memory points + scoring + reinforcement + decay。

### 10.2 测试任务

- 给定新文章，找相关旧记忆
- 回答跨文档问题
- 总结某个主题下读过的核心观点
- 检测新文章和旧观点是支持、冲突还是延伸
- 找出用户最近反复关注的主题

### 10.3 指标

| 指标 | 用途 |
|---|---|
| Precision@K | top-k 召回结果是否相关 |
| Recall@K | 是否找回所有相关记忆 |
| NDCG@K | 排序质量 |
| Citation correctness | 引用来源是否正确 |
| Noise ratio | 召回结果中无关内容比例 |
| User preference | 用户更喜欢哪个系统 |
| Memory usefulness rating | 记忆点是否真的有用 |

## 11. 论文方向

可以写成一篇 6-8 页 technical report 或 workshop-style paper。

推荐标题：

```text
MemoryPoint: Salient Reading Memory Extraction and Dynamic Recall for Personal AI Assistants
```

### Research Questions

```text
RQ1: Can an AI system identify the most memorable points from long-form documents?

RQ2: Does memory-point-based retrieval improve cross-document recall compared with standard chunk-based RAG?

RQ3: Can reinforcement and decay improve personalized memory retrieval over time?
```

### 论文结构

```text
Abstract

1. Introduction
2. Related Work
3. Method
4. Experiments
5. Results
6. Analysis
7. Limitations
8. Conclusion
```

### Related Work

需要覆盖：

- RAG
- Long-term memory agents
- Generative Agents
- ReadAgent
- GraphRAG
- MemGPT / Letta
- text salience
- summarization
- sentence memorability

### 投稿目标

现实目标：

- GitHub technical report
- arXiv preprint
- undergraduate research journal
- ACL / EMNLP / CHI / IUI workshop
- NeurIPS / ICML workshop on agents or memory

不要一开始以顶会主会为目标。申请阶段更重要的是：

```text
GitHub + demo + evaluation + technical report
```

## 12. GitHub 开源策略

建议开源，但只开源干净展示版。

### 可以开源

- 源代码
- README
- 架构图
- demo screenshots
- sample documents
- synthetic memory data
- scoring formula
- decay / reinforcement logic
- evaluation results
- `.env.example`
- requirements

### 不要开源

- 真实个人文档
- 真实 memory database
- 真实阅读日志
- API keys
- 实习相关任何资料
- 公司数据
- 公司 query
- 公司标注规范
- 课程付费资料
- 未授权 PDF
- 申请材料

### 推荐 `.gitignore`

```text
.env
*.db
*.sqlite
chroma_db/
qdrant_storage/
uploads/
private_docs/
memory_logs/
outputs/
__pycache__/
.DS_Store
```

## 13. 简历表达

项目标题：

```text
MemoryPoint: Human-like Reading Memory Extraction and Conversational Recall System
```

简历 bullets：

```text
- Built a personal AI reading memory system that extracts, ranks, and stores salient memory points from long-form documents instead of passively saving all text chunks.

- Designed a memory scoring framework based on importance, novelty, personal relevance, future usefulness, surprise, evidence strength, and cross-document connectivity.

- Implemented a dynamic memory reinforcement and decay mechanism, increasing memory strength when a memory point was repeatedly recalled and reducing its priority after long periods of inactivity.

- Developed an interactive reading interface where users can highlight summary or source paragraphs, turning explicit reading feedback into memory ranking and personalization signals.

- Built a conversational recall interface that answers questions using source-grounded document chunks, user-highlighted passages, and dynamically updated long-term memory points.

- Evaluated memory retrieval against standard chunk-based RAG and summary-based baselines using Precision@K, Recall@K, NDCG@K, citation correctness, and user preference ratings.
```

## 14. SOP 表达

可以在申请文书中这样描述：

```text
Inspired by the way humans retain only a few salient ideas after reading, I developed MemoryPoint, a personal AI reading memory system that extracts and ranks long-term memory points from documents. Users can send articles to the system, receive structured summaries, highlight important paragraphs, and then continue a conversation grounded in both the original sources and their accumulated reading memories. Unlike standard RAG systems that retrieve text chunks only when asked, MemoryPoint forms structured memories after reading, strengthens memories through repeated recall, and decays unused memories over time. Through this project, I explored how retrieval, ranking, user feedback, long-term memory, and human-inspired AI system design can be combined to build more personalized and reliable AI assistants.
```

## 15. 项目风险

### 技术风险

- 记忆点提取可能变成普通摘要
- LLM 打分可能不稳定
- 用户反馈数据不足
- 评估标准难设计
- 个性化效果难量化

### 开源风险

- 隐私泄露
- API key 泄露
- 版权问题
- 公司实习信息泄露
- repo 太乱反而减分

### 申请风险

- 如果只做 RAG demo，ML 含量不足
- 如果没有 evaluation，项目说服力不够
- 如果没有 README 和 screenshots，招生官很难快速理解

## 16. 成功标准

最低成功标准：

- 可以上传文档
- 可以粘贴文章文本
- 可以生成文章总结
- 可以提取 memory points
- 可以给 memory points 打分
- 可以对总结或原文段落 highlight
- 可以保存 memory bank
- 可以对当前文章和历史记忆对话
- 可以根据新文章召回旧记忆
- 可以看到强化和衰减后的动态分数

申请加分标准：

- 有 GitHub repo
- 有干净 README
- 有 Streamlit demo
- 有架构图
- 有 evaluation
- 有 technical report
- 有 ML baseline
- 有和普通 RAG 的对比实验

优秀标准：

- 有人工标注 memory point dataset
- 有 BERT / ELECTRA / Sentence-BERT ranking model
- 有 NDCG@K / Precision@K / Recall@K 结果
- 有 reinforcement / decay ablation
- 有一篇 6-8 页英文 report

## 17. 一句话项目定位

```text
MemoryPoint is a human-inspired AI reading memory system that learns not only to retrieve documents, but to decide what is worth remembering, how strongly it should be remembered, and when it should be recalled.
```

中文版本：

```text
MemoryPoint 不是让 AI 保存所有文本，而是让 AI 像人一样判断哪些阅读内容值得被长期记住，并通过反复召回强化记忆、长期不用则逐渐遗忘。
```

## 18. 完整研究版本升级方案

如果目标是把 MemoryPoint 做成完整项目，它不能停留在“AI 阅读助手”或“PDF RAG demo”。更强的定位应当是：

```text
MemoryPoint: Personalized Long-Term Reading Memory Retrieval with Salience Ranking and Dynamic Recall
```

也就是：一个面向长期阅读记忆的个性化检索与排序系统，包含产品 demo、标注数据集、ML ranking baseline、动态记忆机制和系统性评估。

### 18.1 核心研究问题

```text
RQ1: Can memory-point retrieval outperform standard chunk-based RAG for long-term reading recall?

RQ2: Can user highlights and recall history improve personalized memory ranking?

RQ3: Does reinforcement and decay improve retrieval quality over static memory storage?
```

### 18.2 完整版本必须具备的交付物

- 可运行 Web demo。
- 干净 GitHub repo。
- 100 篇文档左右的 reading-memory 标注数据集。
- TF-IDF、Sentence-BERT、MLP、LLM scorer 和 hybrid MemoryRanker baseline。
- Standard RAG、summary-only memory、static memory points 和 MemoryPoint ablation 对比。
- Precision@K、Recall@K、NDCG@K、MRR、citation correctness、unsupported answer rate 等指标。
- 6-8 页 technical report。
- screenshots / demo video。
- 可复现实验脚本。
- 项目总结中可使用的量化提升结果。

### 18.3 数据集设计

构建一个小但严肃的数据集，而不是只靠 prompt 演示。

建议规模：

```text
100 documents
每篇 800-3000 words
领域：AI / ML / cognition / HCI / productivity
```

每篇文档标注：

- 3-5 个 high-salience memory points。
- 5-10 个 medium-salience passages。
- low-salience negative samples。
- source evidence span。
- topic tags。
- memory type。
- highlight label。

数据格式示例：

```json
{
  "document_id": "doc_001",
  "passage_id": "p_014",
  "text": "...",
  "salience_label": "high",
  "memory_point": "...",
  "evidence_span": "...",
  "tags": ["RAG", "retrieval", "hallucination"],
  "memory_type": "conceptual_insight",
  "highlight_label": "important"
}
```

项目总结可以写成：

```text
Created a 100-document annotated reading-memory dataset with passage-level salience labels, source-grounded memory points, and user-highlight signals.
```

### 18.4 模型和排序方案

至少对比以下方法：

| Method | Purpose |
|---|---|
| TF-IDF + Logistic Regression | classical baseline |
| Sentence-BERT + Logistic Regression | embedding baseline |
| Sentence-BERT + MLP | neural baseline |
| LLM scorer | prompt-based baseline |
| Hybrid MemoryRanker | final system |

Hybrid MemoryRanker 推荐特征：

```text
score =
0.25 * semantic_similarity
+ 0.20 * salience_score
+ 0.15 * user_highlight_signal
+ 0.15 * memory_strength
+ 0.10 * novelty
+ 0.10 * cross_document_connectivity
+ 0.05 * recency
```

### 18.5 Evaluation 设计

对比系统：

| System | Description |
|---|---|
| Standard RAG | only chunk retrieval |
| Summary Memory | retrieve from summaries |
| Static MemoryPoint | memory points without dynamic scoring |
| MemoryPoint - Highlight | no user highlight signal |
| MemoryPoint - Decay | no reinforcement/decay |
| Full MemoryPoint | complete system |

评估指标：

```text
Precision@5
Recall@5
NDCG@5
MRR
Citation correctness
Unsupported answer rate
User preference score
```

目标不是虚构数字，而是用实验回答一个明确问题：

```text
Full MemoryPoint 是否能在长期阅读召回任务上明显优于 standard chunk-based RAG？
```

### 18.6 产品 demo 范围

完整版本不需要先做复杂登录、多用户、浏览器插件或过度视觉包装。产品 demo 应优先服务核心实验。

必须有 4 个页面：

1. **Reading Page**
   上传文章、看原文、看 summary、highlight 段落。

2. **Memory Review Page**
   查看候选 memory points，accept/edit/reject。

3. **Memory Bank**
   查看长期记忆、score、strength、source、recall history。

4. **Recall Chat**
   对当前文章和历史记忆提问，回答带 citation。

### 18.7 开发路线

#### Phase 1: Repo 基础与文档解析

- Python 项目结构。
- requirements / `.env.example` / sample data。
- PDF / TXT / Markdown / pasted text ingestion。
- paragraph、chunk、metadata 保存。

#### Phase 2: Baseline RAG

- chunking。
- embedding。
- vector DB。
- standard RAG 问答。
- source citation。

#### Phase 3: Memory Point MVP

- article summary。
- candidate memory point extraction。
- evidence span binding。
- SQLite memory storage。

#### Phase 4: Reading UI

- Streamlit reading page。
- summary view。
- source paragraph view。
- highlight labels。
- memory point review。
- memory bank。

#### Phase 5: Dataset

- 收集约 100 篇文档。
- 建立 annotation schema。
- 标注 high / medium / low salience passages。
- 生成 train / dev / test split。

#### Phase 6: ML Ranking

- TF-IDF baseline。
- Sentence-BERT baseline。
- MLP baseline。
- LLM scorer。
- Hybrid MemoryRanker。

#### Phase 7: Dynamic Memory

- recall event log。
- recall_count。
- last_recalled_at。
- reinforcement。
- decay。
- memory strength visualization。

#### Phase 8: Recall Mode

- 新文章触发旧记忆。
- support / conflict / complement / extension relation。
- current article + historical memory chat。
- source-grounded answer。

#### Phase 9: Evaluation

- retrieval benchmark。
- ranking benchmark。
- ablation study。
- citation correctness。
- unsupported answer rate。
- result tables。

#### Phase 10: Report and Portfolio Polish

- 6-8 页 technical report。
- README results table。
- screenshots。
- demo video。
- reproducible scripts。
- final project summary。

### 18.8 最终项目表达

完成后可以写成：

```text
Developed MemoryPoint, a personalized reading-memory retrieval system that extracts and ranks source-grounded memory points from long-form documents using salience prediction, user highlight signals, and dynamic reinforcement/decay.

Built a 100-document annotated dataset with passage-level salience labels and evidence-linked memory points; trained TF-IDF, Sentence-BERT, MLP, and hybrid ranking baselines.

Evaluated MemoryPoint against standard RAG, summary-only memory, and static memory-point baselines using Precision@K, Recall@K, NDCG@K, MRR, and citation correctness.

Improved cross-document recall quality by X% NDCG@5 over standard chunk-based RAG while reducing unsupported answer rate by Y%.
```

最后一行的 X 和 Y 必须来自真实实验结果，不能提前编造。

## 19. 完成周期预估

以下估算基于一个人独立完成，并且优先做研究级核心功能，而不是扩展大量非必要产品功能。

| 目标版本 | 范围 | 预计时间 |
|---|---|---:|
| Basic MVP | 文档解析、基础 RAG、memory point 提取、简单 UI | 2-3 周 |
| Strong Project Version | MVP + memory bank + recall chat + dynamic scoring + 清晰 README | 5-7 周 |
| Evaluation Version | 数据集 + ML baselines + ablation + technical report + demo video | 9-12 周 |
| Complete Version | polished demo + reproducible experiments + report + quantified gains | 12-16 周 |

按投入时间换算：

| 每周投入 | 完整版本预计周期 |
|---|---:|
| 15-20 小时 / 周 | 3-4 个月 |
| 25-30 小时 / 周 | 10-12 周 |
| 40 小时 / 周 | 7-9 周 |

主要耗时点：

- 数据标注：2-4 周。
- RAG + memory pipeline：2-3 周。
- Streamlit demo：1-2 周。
- ML baselines：2-3 周。
- evaluation + ablation：2-3 周。
- technical report + GitHub polish：1-2 周。

最大风险不是 coding，而是 scope creep。为了按期完成，第一版必须严格聚焦：

```text
long-term reading recall
+ memory point ranking
+ user highlight signal
+ dynamic reinforcement/decay
+ evaluation against RAG baselines
```

暂时不优先做：

- 多用户系统。
- 浏览器插件。
- 移动端。
- 复杂权限管理。
- 大规模生产部署。
- 过度 UI 动效。
- 太多文件格式支持。
