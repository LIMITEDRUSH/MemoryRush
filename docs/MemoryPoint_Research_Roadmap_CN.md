# MemoryPoint 中文研究路线图

这份文档把 MemoryPoint 从“普通 RAG 应用”重新设计成一个完整的检索与排序项目。目标不是功能堆叠，而是让项目同时证明工程实现、数据构建、模型训练、检索评估和产品表达能力。

## 项目定位

```text
MemoryPoint: Personalized Long-Term Reading Memory Retrieval with Salience Ranking and Dynamic Recall
```

中文定位：

```text
MemoryPoint 是一个面向长期阅读记忆的个性化检索与排序系统。
它从长文档中提取值得长期记住的 memory points，结合用户 highlight、显著性预测、动态强化和衰减机制，在后续阅读和对话中实现跨文档召回。
```

不要把它包装成“AI 阅读助手”或“PDF Chatbot”。更强的表达是：

- 个性化长期阅读记忆系统
- passage salience ranking
- memory-point retrieval
- dynamic reinforcement and decay
- source-grounded conversational recall
- evaluation against RAG baselines

## 核心研究问题

```text
RQ1: memory-point retrieval 是否能在长期阅读召回任务中优于 standard chunk-based RAG？

RQ2: 用户 highlight 和历史 recall 行为是否能提升个性化 memory ranking？

RQ3: reinforcement / decay 是否能优于静态 memory storage？
```

这三个问题决定了项目的技术含金量。最终项目必须用实验结果回答它们，而不是只用概念描述。

## 完整版本交付物

完整版本至少需要交付：

- 一个可运行的 Web demo。
- 一个干净、可复现的 GitHub repo。
- 一个约 100 篇文档的 reading-memory 标注数据集。
- TF-IDF、Sentence-BERT、MLP、LLM scorer 和 Hybrid MemoryRanker baseline。
- Standard RAG、summary-only memory、static memory points 和 MemoryPoint 消融实验。
- Precision@K、Recall@K、NDCG@K、MRR、citation correctness、unsupported answer rate 等指标。
- 一篇 6-8 页 technical report。
- screenshots 和 2 分钟左右 demo video。
- 项目总结中可以使用的真实量化结果。

## 数据集设计

数据集是这个项目从“应用项目”升级为“研究项目”的关键。

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

标注格式示例：

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

项目总结中可以写：

```text
Created a 100-document annotated reading-memory dataset with passage-level salience labels, source-grounded memory points, and user-highlight signals.
```

## 模型与排序方案

至少对比 5 类方法：

| Method | 作用 |
|---|---|
| TF-IDF + Logistic Regression | 传统机器学习 baseline |
| Sentence-BERT + Logistic Regression | embedding baseline |
| Sentence-BERT + MLP | neural baseline |
| LLM scorer | prompt-based baseline |
| Hybrid MemoryRanker | 最终系统 |

Hybrid MemoryRanker 推荐公式：

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

这里的重点是：最终系统不能只靠 LLM prompt。它应该把文本特征、embedding 特征、用户反馈、动态记忆强度和跨文档连接特征组合起来。

## 实验设计

对比系统：

| System | Description |
|---|---|
| Standard RAG | 只用 chunk retrieval |
| Summary Memory | 只检索文章摘要 |
| Static MemoryPoint | 有 memory points，但没有动态分数 |
| MemoryPoint - Highlight | 移除用户 highlight signal |
| MemoryPoint - Decay | 移除 reinforcement / decay |
| Full MemoryPoint | 完整系统 |

核心指标：

```text
Precision@5
Recall@5
NDCG@5
MRR
Citation correctness
Unsupported answer rate
User preference score
```

目标结论应该类似：

```text
Full MemoryPoint 在长期阅读召回任务上，相比 standard chunk-based RAG 获得更高的 NDCG@5，并降低 unsupported answer rate。
```

注意：最后的提升百分比必须来自真实实验，不能提前编造。

## 产品 Demo 范围

产品 demo 要服务核心实验，不要过早做复杂产品功能。

必须有 4 个页面：

1. **Reading Page**
   上传文章，查看原文，查看 AI summary，对段落 highlight。

2. **Memory Review Page**
   查看候选 memory points，并支持 `accept`、`edit`、`reject`。

3. **Memory Bank**
   查看长期记忆，包括 score、strength、source、recall history。

4. **Recall Chat**
   基于当前文章和历史 memory 对话，回答必须带 citation。

暂时不优先做：

- 多用户登录
- 浏览器插件
- 移动端
- 大规模部署
- 复杂权限系统
- 过度 UI 动效
- 太多文件格式支持

## 开发路线

### Phase 1: Repo 基础与文档解析

- 建立 Python 项目结构。
- 添加 `requirements.txt`、`.env.example`、sample data。
- 支持 PDF、TXT、Markdown、pasted text。
- 保存 paragraph、chunk、metadata。

### Phase 2: Baseline RAG

- chunking。
- embedding。
- vector database。
- standard RAG answer。
- source citation。

### Phase 3: Memory Point MVP

- article summary。
- candidate memory point extraction。
- evidence span binding。
- SQLite memory storage。

### Phase 4: Reading UI

- Streamlit reading page。
- summary view。
- source paragraph view。
- highlight labels。
- memory point review。
- memory bank。

### Phase 5: Dataset

- 收集约 100 篇文档。
- 定义 annotation schema。
- 标注 high / medium / low salience passages。
- 划分 train / dev / test。

### Phase 6: ML Ranking

- TF-IDF baseline。
- Sentence-BERT baseline。
- MLP baseline。
- LLM scorer。
- Hybrid MemoryRanker。

### Phase 7: Dynamic Memory

- recall event log。
- recall count。
- last recalled timestamp。
- reinforcement。
- decay。
- memory strength visualization。

### Phase 8: Recall Mode

- 新文章触发旧记忆。
- 判断 support / conflict / complement / extension。
- 基于当前文章和历史 memory 做 source-grounded chat。

### Phase 9: Evaluation

- retrieval benchmark。
- ranking benchmark。
- ablation study。
- citation correctness。
- unsupported answer rate。
- results tables。

### Phase 10: Report and Portfolio Polish

- 6-8 页 technical report。
- README results table。
- screenshots。
- demo video。
- reproducible scripts。
- final project summary。

## 完成周期预估

| 目标版本 | 范围 | 预计时间 |
|---|---|---:|
| Basic MVP | ingestion、RAG、memory extraction、简单 UI | 2-3 周 |
| Strong Project Version | MVP + memory bank + recall chat + dynamic scoring + 清晰 README | 5-7 周 |
| Evaluation Version | dataset + ML baselines + ablations + report + demo video | 9-12 周 |
| Complete Version | polished demo + reproducible experiments + report + quantified gains | 12-16 周 |

按每周投入估算：

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

## Scope Control

为了按期完成，第一版必须严格聚焦：

```text
long-term reading recall
+ memory point ranking
+ user highlight signal
+ dynamic reinforcement/decay
+ evaluation against RAG baselines
```

不要让项目变成“大而全 AI 助手”。如果做太多功能，会牺牲最重要的实验和结果。

## 最终项目表达

完成后可以写成：

```text
Developed MemoryPoint, a personalized reading-memory retrieval system that extracts and ranks source-grounded memory points from long-form documents using salience prediction, user highlight signals, and dynamic reinforcement/decay.

Built a 100-document annotated dataset with passage-level salience labels and evidence-linked memory points; trained TF-IDF, Sentence-BERT, MLP, and hybrid ranking baselines.

Evaluated MemoryPoint against standard RAG, summary-only memory, and static memory-point baselines using Precision@K, Recall@K, NDCG@K, MRR, and citation correctness.

Improved cross-document recall quality by X% NDCG@5 over standard chunk-based RAG while reducing unsupported answer rate by Y%.
```

最后一行的 X 和 Y 必须等实验完成后替换成真实结果。
