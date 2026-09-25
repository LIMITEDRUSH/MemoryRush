"""Secondary reading and memory inspectors, opened from the conversation workspace."""

from __future__ import annotations

import json
import re

import streamlit as st

from memoryrush.bank import current_strength
from memoryrush.scoring import WEIGHTS

LABELS = {
    "importance": "重要性",
    "novelty": "相对新颖性",
    "personal_relevance": "个人相关性",
    "usefulness": "未来用途",
    "surprise": "启发性",
    "connectivity": "旧记忆关联",
    "evidence_strength": "证据支持",
    "user_highlight": "你的标注",
}


def safe_label(text: str) -> str:
    return re.sub(r"([\\\[\]!*_<>`])", r"\\\1", text)


def render_artifact(artifact: dict):
    st.subheader(safe_label(artifact["document"]["title"]))
    st.text(artifact["output"]["summary"])
    st.caption(f"{artifact['provider_name']} / {artifact['model_name']} · {artifact['created_at']}")
    issues = artifact["validation"]["issues"]
    if issues:
        with st.expander(f"校验记录 · {len(issues)} 条"):
            for issue in issues:
                st.text(f"{issue['severity']} · {issue['path']} · {issue['message']}")
    with st.expander("原文与段落编号"):
        for paragraph in artifact["document"]["paragraphs"]:
            st.caption(paragraph["paragraph_id"])
            st.text(paragraph["text"])
    with st.expander("主动回忆：先想答案，再展开核对"):
        admitted = {d["memory_unit_index"] for d in artifact["admission"] if d["admitted"]}
        units = artifact["output"]["memory_units"]
        for question in artifact["output"]["recall_questions"]:
            index = question["memory_unit_index"]
            if index not in admitted or not 0 <= index < len(units):
                continue
            st.text(question["question"])
            with st.popover(f"核对原文 · 记忆 {index + 1}"):
                st.text(units[index]["content"])
                for evidence in units[index]["evidence"]:
                    st.text(evidence["quote"])
        st.caption("展开答案不自动强化；对话中真正引用且引文校验通过，才记录使用。")
    st.download_button(
        "导出这次处理记录",
        json.dumps(artifact, ensure_ascii=False, indent=2),
        file_name=f"{artifact['run_id']}.json",
        mime="application/json",
    )


def memory_bank(bank):
    st.subheader("记忆库")
    st.caption("基础分来自模型与标注；当前强度随时间衰减。固定只暂停衰减，不绕过相关性筛选。")
    state_names = {"active": "启用", "held": "待审", "forgotten": "停用"}
    filters = st.multiselect(
        "显示状态", list(state_names), default=["active", "held"], format_func=state_names.get
    )
    search = st.text_input("查找内容或来源")
    memories = [
        m
        for m in bank.memories()
        if m["state"] in filters
        and search.casefold() in (m["content"] + m["source_title"]).casefold()
    ]
    memories.sort(key=current_strength, reverse=True)
    if not memories:
        st.info("这里还没有匹配的记忆。从对话输入框附加文章，或点击“粘贴文章”。")
    for m in memories:
        mid, unit = m["memory_id"], m["unit"]
        with st.expander(safe_label(f"{state_names[m['state']]} · {m['content'][:80]}")):
            st.text(m["content"])
            st.caption(f"{mid} · {m['source_title']} · {m['origin']}")
            strength = current_strength(m)
            cols = st.columns(3)
            cols[0].metric("基础分", f"{m['base_score']:.3f}")
            cols[1].metric("当前强度", f"{strength:.3f}")
            cols[2].metric("衰减半衰期 / 天", f"{m['half_life_days']:.1f}")
            st.progress(min(1.0, max(0.0, strength)), text="当前可用记忆强度")
            st.caption(
                f"有效强化 {m['recall_count']} 次 · 最近强化 {m['last_recalled_at'] or '尚无'}"
            )
            reasons = unit.get("assessment", {}).get("reasons", {})
            st.dataframe(
                [
                    {
                        "维度": LABELS[key],
                        "分数": unit["scores"][key],
                        "权重": weight,
                        "模型理由": reasons.get(
                            key, "用户显式标注" if key == "user_highlight" else "未提供"
                        ),
                    }
                    for key, weight in WEIGHTS.items()
                ],
                hide_index=True,
                use_container_width=True,
            )
            st.caption(
                "新颖性只相对本次提供给模型的旧记忆；分数不是客观真值。无兴趣资料时个人相关性固定为 0.5。"
            )
            for evidence in unit["evidence"]:
                st.caption(f"原文证据 · {evidence['paragraph_id']}")
                st.text(evidence["quote"])
            with st.form(f"edit_{mid}"):
                new_state = st.selectbox(
                    "使用状态",
                    list(state_names),
                    index=list(state_names).index(m["state"]),
                    format_func=state_names.get,
                )
                pin = st.checkbox("固定记忆，暂停衰减", value=bool(m["pinned"]))
                if st.form_submit_button("保存记忆设置"):
                    try:
                        bank.set_state(mid, new_state)
                        if pin != bool(m["pinned"]):
                            bank.pin(mid, pin)
                        st.rerun()
                    except ValueError as exc:
                        st.error(str(exc))
            events = bank.events(mid)
            if events:
                st.dataframe(events, hide_index=True, use_container_width=True)
            with st.popover("评分原始记录"):
                st.json(unit.get("assessment", {}))
