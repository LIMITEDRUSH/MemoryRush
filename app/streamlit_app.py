"""Conversation-first local reading workspace."""

from __future__ import annotations

import html
import sys
from pathlib import Path
from urllib.parse import urlsplit

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from app.model_settings import get_provider, provider_settings, settings_dialog
from app.panels import memory_bank, render_artifact, safe_label
from memoryrush.bank import MemoryBank, current_strength
from memoryrush.chat import answer
from memoryrush.conversation import read_in_conversation
from memoryrush.parsing import parse_document


def styles():
    st.markdown(
        """<style>
    :root {--mr-ink:#252525;--mr-muted:#737373;--mr-line:#E8E8E8;--mr-rail:#F7F7F8;--mr-focus:#71717A;}
    .stApp {background:#FFFFFF;color:var(--mr-ink);font-family:'Segoe UI','Microsoft YaHei',sans-serif;}
    [data-testid="stHeader"] {background:rgba(255,255,255,.94);height:3rem;}
    [data-testid="stSidebar"] {background:var(--mr-rail);border-right:1px solid #ECECED;min-width:248px!important;max-width:248px!important;}
    [data-testid="stSidebarUserContent"] {padding:1rem .85rem!important;}
    .stMainBlockContainer {max-width:940px;padding:3.5rem 2rem 7rem;}
    .stMainBlockContainer:has(.st-key-context_panel) {max-width:1260px;}
    h1,h2,h3,h4 {font-family:'Segoe UI','Microsoft YaHei',sans-serif;letter-spacing:-.035em;color:var(--mr-ink);}
    h1 {font-size:1.9rem!important;font-weight:600!important;}
    h3 {font-size:1.15rem!important;} h4 {font-size:.95rem!important;font-weight:550!important;}
    code {font-family:'Cascadia Code',Consolas,monospace;}
    [data-testid="stCaptionContainer"] p {color:var(--mr-muted)!important;font-size:.78rem;}
    [data-testid="stText"] {font-size:.95rem;line-height:1.85;white-space:pre-wrap;}
    [data-testid="stChatMessage"] {background:transparent;padding:1.2rem 0;border-radius:0;}
    [data-testid="stChatMessageContent"] {min-width:0;}
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {flex-direction:row-reverse;}
    [data-testid="stChatMessageAvatarUser"] {display:none;}
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageContent"] {flex-grow:0;width:fit-content;max-width:85%;margin:0!important;background:#F4F4F5;border-radius:20px;padding:.7rem 1rem;}
    [data-testid="stChatInput"] {background:#FFFFFF;border:1px solid #DEDEDF;border-radius:24px;box-shadow:0 3px 14px #00000006;padding:.35rem .4rem;}
    [data-testid="stChatInput"]:focus-within {border-color:var(--mr-focus);box-shadow:0 0 0 1px var(--mr-focus);}
    [data-testid="stChatInput"] > div {border:0;background:transparent;box-shadow:none;}
    [data-testid="stChatInput"] textarea {line-height:1.7;min-height:55px!important;}
    [data-testid="stChatInputSubmitButton"] {background:#27272A;color:white;border-radius:50%;}
    [data-testid="stChatInputSubmitButton"]:disabled {background:#E4E4E7;color:#9A9A9F;}
    [data-testid="stBottom"] {background:linear-gradient(transparent,#FFFFFF 20%);}
    [data-testid="stBottomBlockContainer"] {max-width:940px;padding:1rem 2rem 1.2rem;}
    [data-testid="stExpander"] {border-color:var(--mr-line);border-radius:10px;}
    [data-testid="stChatMessage"] [data-testid="stExpander"] details {border:0;}
    [data-testid="stChatMessage"] [data-testid="stExpander"] summary {padding:.35rem 0;color:var(--mr-muted);}
    [data-testid="stSidebar"] button {border:0;background:transparent;box-shadow:none;justify-content:flex-start;text-align:left;padding:.5rem .7rem;border-radius:8px;min-height:38px;}
    [data-testid="stSidebar"] button:hover {background:#ECECED;}
    [data-testid="stSidebar"] button p {font-size:.86rem;}
    [data-testid="stSidebar"] button [data-testid="stMarkdownContainer"] {text-align:left;flex:1;}
    [data-testid="stSidebar"] [data-testid="stTextInput"] input {background:#EEEFF1;font-size:.82rem;}
    .st-key-new_chat button {background:#ECECEE!important;}
    .st-key-history_rail {height:calc(100dvh - 395px)!important;min-height:130px;}
    .st-key-history_rail button p {overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
    .st-key-history_rail button[kind="secondary"] {background:#E9E9EC!important;}
    .st-key-context_panel {border-left:1px solid var(--mr-line);padding-left:1.2rem;}
    .st-key-workspace_header {margin-bottom:1.5rem;}
    .st-key-workspace_header button {border:0;background:transparent;color:#626266;font-size:.8rem;}
    .st-key-workspace_header button:hover {background:#F3F3F4;}
    .st-key-home_composer [data-testid="stChatInput"] textarea {min-height:86px!important;}
    .st-key-home_actions {padding-top:.35rem;}
    .st-key-home_actions button {border-color:#E7E7E9;border-radius:18px;color:#626266;font-size:.8rem;min-height:32px;}
    .mr-brand {font-family:Bahnschrift,'Segoe UI',sans-serif;font-size:1.07rem;letter-spacing:-.035em;font-weight:600;padding:.1rem .7rem 1.15rem;}
    .mr-brand span {display:inline-block;width:21px;height:21px;border:1.5px solid #39393C;border-radius:6px;margin-right:9px;vertical-align:-4px;transform:rotate(-8deg);}
    .mr-empty {padding:clamp(3rem,15vh,9rem) 0 1.5rem;text-align:center;}
    .mr-empty h1 {margin-bottom:.45rem;}
    .mr-empty p {color:var(--mr-muted);font-size:.9rem;line-height:1.7;margin-bottom:1rem;}
    .mr-local {font-size:.75rem;color:var(--mr-muted);padding:.4rem .7rem;}
    .mr-file {display:inline-block;background:white;border:1px solid var(--mr-line);border-radius:10px;padding:.5rem .7rem;font-size:.8rem;margin-bottom:.5rem;overflow-wrap:anywhere;}
    .mr-trail {color:var(--mr-muted);font-size:.75rem;margin:.7rem 0;}
    .mr-status {font-size:.74rem;color:#737373;margin-top:-1rem;margin-bottom:.65rem;overflow-wrap:anywhere;}
    button[kind="primary"] {background:#27272A;border-color:#27272A;color:#fff;}
    :focus-visible {outline:2px solid var(--mr-focus)!important;outline-offset:3px;}
    /* The composer owns the visible focus ring; avoid a second rectangular one. */
    [data-testid="stChatInput"] textarea:focus-visible {outline:none!important;}
    @media(max-width:700px) {
      .stMainBlockContainer {padding:3.4rem 1rem 7rem;}
      [data-testid="stBottomBlockContainer"] {padding:.5rem .75rem .75rem;}
      .st-key-context_panel {border-left:0;border-top:1px solid var(--mr-line);padding:1rem 0;}
      .mr-empty {padding-top:3.5rem;}
      .mr-empty h1 {font-size:1.6rem!important;}
      .st-key-workspace_header {margin-bottom:1rem;}
    }
    @media(prefers-reduced-motion:reduce) {* {animation:none!important;transition:none!important;}}
    </style>""",
        unsafe_allow_html=True,
    )


@st.dialog("记忆库", width="large")
def bank_dialog(bank):
    memory_bank(bank)


@st.dialog("已读文章", width="large")
def readings_dialog(bank, run_id=None):
    artifacts = bank.artifacts()
    if not artifacts:
        st.info("还没有文章。直接从对话输入框添加 TXT / Markdown，或点击“粘贴文章”。")
        return
    index = next((i for i, artifact in enumerate(artifacts) if artifact["run_id"] == run_id), 0)
    selection = st.selectbox(
        "文章记录",
        range(len(artifacts)),
        index=index,
        format_func=lambda i: artifacts[i]["document"]["title"],
    )
    render_artifact(artifacts[selection])


def ensure_session(bank):
    session_id = st.session_state.get("active_session")
    if not session_id:
        session_id = bank.new_session()
        st.session_state["active_session"] = session_id
    return session_id


def run_reading(bank, provider, source_name, text, *, question="", highlights=()):
    _, _, _, budget = provider_settings(bank)
    with st.status("正在阅读文章…", expanded=True) as status:
        turn = read_in_conversation(
            bank,
            provider,
            ensure_session(bank),
            source_name,
            text,
            question=question,
            memory_budget=budget,
            highlighted_ids=tuple(highlights),
            on_progress=lambda message: status.update(label=message),
        )
        status.update(label="文章与阅读结果已保存到当前对话", state="complete", expanded=False)
    return turn


@st.dialog("粘贴文章到当前对话", width="large")
def paste_dialog(bank, provider):
    source_name = st.text_input("文章名称", value="我的阅读.md")
    text = st.text_area("文章正文", height=220, placeholder="粘贴正文，空行分段。")
    question = st.text_input(
        "想先问的问题（可选）", placeholder="例如：这篇文章最重要的观点是什么？"
    )
    highlights = []
    if text.strip():
        try:
            document = parse_document(source_name, text)
            paragraphs = {p.paragraph_id: p.text for p in document.paragraphs}
            with st.expander("标记特别想记住的段落"):
                highlights = st.multiselect(
                    "重点段落",
                    list(paragraphs),
                    format_func=lambda pid: f"{pid} · {paragraphs[pid][:90]}",
                )
        except ValueError as exc:
            st.warning(str(exc))
    if st.button("发送到对话", type="primary", disabled=not text.strip()):
        try:
            run_reading(bank, provider, source_name, text, question=question, highlights=highlights)
            st.rerun()
        except (ValueError, RuntimeError, OSError) as exc:
            st.error(f"文章处理未完成：{exc}")


def sidebar(bank, provider, model):
    with st.sidebar:
        st.markdown('<div class="mr-brand"><span></span>MemoryRush</div>', unsafe_allow_html=True)
        if st.button(
            "新对话", key="new_chat", icon=":material/edit_square:", use_container_width=True
        ):
            st.session_state["active_session"] = None
            st.session_state.pop("failed_text", None)
            st.rerun()
        if st.button(
            "粘贴文章",
            icon=":material/note_add:",
            use_container_width=True,
            disabled=provider is None,
        ):
            paste_dialog(bank, provider)
        if st.button("已读文章", icon=":material/library_books:", use_container_width=True):
            readings_dialog(bank)
        if st.button("记忆库", icon=":material/neurology:", use_container_width=True):
            bank_dialog(bank)
        search = st.text_input("搜索对话", placeholder="搜索历史对话", label_visibility="collapsed")
        st.caption("最近对话")
        sessions = [s for s in bank.sessions() if search.casefold() in s["title"].casefold()]
        with st.container(height=340, border=False, key="history_rail"):
            if not sessions:
                st.caption("发送第一条消息后，会自动保存在这里。")
            for session in sessions:
                active = session["session_id"] == st.session_state.get("active_session")
                if st.button(
                    safe_label(session["title"][:28]),
                    key=f"session_{session['session_id']}",
                    help=session["title"],
                    type="secondary" if active else "tertiary",
                    use_container_width=True,
                ):
                    st.session_state["active_session"] = session["session_id"]
                    st.session_state.pop("failed_text", None)
                    st.rerun()
        if st.button("设置", icon=":material/settings:", use_container_width=True):
            settings_dialog(bank)
        name, _, _, _ = provider_settings(bank)
        status = "外部 API · 上下文会发送至服务商" if name == "api" else "本地接口 · 不直连外部 API"
        if name == "preview":
            status = "离线预览 · 不调用模型"
        st.markdown(
            f'<div class="mr-local">{html.escape(status)}<br>历史记录保存在本机</div>',
            unsafe_allow_html=True,
        )


def render_turn(turn, bank):
    with st.chat_message("user"):
        reading = turn.get("reading")
        if reading:
            st.markdown(
                f'<div class="mr-file">▤ {html.escape(reading["source_name"])}</div>',
                unsafe_allow_html=True,
            )
        st.text(turn["query"])
    with st.chat_message("assistant", avatar=":material/auto_stories:"):
        if reading:
            mode = (
                "预览，未启用自动召回"
                if reading["preview"]
                else f"{reading['active_count']} 条记忆可用于对话"
            )
            st.caption(f"已读 · {reading['title']} · {mode}")
            if reading.get("validation_errors"):
                st.warning(
                    f"有 {reading['validation_errors']} 项原文校验问题，请在阅读记录中核对。"
                )
        for paragraph in turn["paragraphs"]:
            st.text(paragraph["text"])
            citations = paragraph["citations"]
            if citations:
                with st.expander(f"原文依据 · {len(citations)} 条"):
                    for citation in citations:
                        st.caption(citation["memory_id"])
                        st.text(citation["quote"])
        if turn.get("answer_error"):
            st.warning("文章和记忆已保存，但附带问题暂未完成。可以继续发送问题，无需重复上传。")
            with st.expander("查看问题原因"):
                st.text(turn["answer_error"])
        retrieval = turn.get("retrieval", [])
        if retrieval:
            selected = sum(row["selected"] for row in retrieval)
            used = len(turn["used_memory_ids"])
            st.markdown(
                f'<div class="mr-trail">记忆轨迹 · 检查 {len(retrieval)} 条 · 召回 {selected} 条 · 引用 {used} 条</div>',
                unsafe_allow_html=True,
            )
            with st.expander("查看这次召回"):
                for row in retrieval:
                    if row["selected"]:
                        st.text(row["content"])
                        st.caption(
                            f"相关性 {row['relevance']:.2f} · 当前强度 {row['strength']:.2f} · {row['source_title']}"
                        )
        if reading and st.button(
            "查看阅读记录", key=f"article_{turn['turn_id']}", icon=":material/article:"
        ):
            readings_dialog(bank, reading["run_id"])


def context_panel(bank, turns):
    with st.container(key="context_panel"):
        st.markdown("#### 阅读与记忆")
        st.caption("按需查看，不打断当前对话。")
        tabs = st.tabs(["本次召回", "记忆"])
        with tabs[0]:
            recent = turns[-1] if turns else None
            if not recent or not recent.get("retrieval"):
                st.caption("本轮没有召回记录；提问后会显示实际召回的记忆及相关性。")
            else:
                if not any(row["selected"] for row in recent["retrieval"]):
                    st.caption("本轮没有选中足够相关的记忆。")
                for row in recent["retrieval"]:
                    if not row["selected"]:
                        continue
                    with st.expander(safe_label(row["content"][:60])):
                        st.text(row["content"])
                        st.caption(f"相关性 {row['relevance']:.2f} · 强度 {row['strength']:.2f}")
                        st.text(row["relevance_reason"])
                        st.caption(row["source_title"])
        with tabs[1]:
            memories = sorted(bank.memories(True), key=current_strength, reverse=True)
            st.caption(f"{len(memories)} 条已启用 · 按当前强度排序")
            for m in memories[:8]:
                with st.expander(safe_label(m["content"][:50])):
                    st.text(m["content"])
                    st.caption(f"基础分 {m['base_score']:.2f} → 当前 {current_strength(m):.2f}")
                    st.caption(f"半衰期 {m['half_life_days']:.1f} 天 · 强化 {m['recall_count']} 次")
            if st.button("管理全部记忆", use_container_width=True):
                bank_dialog(bank)


def main():
    st.set_page_config(
        page_title="MemoryRush", page_icon="📖", layout="wide", initial_sidebar_state="expanded"
    )
    styles()
    bank = MemoryBank()
    if "active_session" not in st.session_state:
        sessions = bank.sessions()
        st.session_state["active_session"] = sessions[0]["session_id"] if sessions else None
    name, model, endpoint, _ = provider_settings(bank)
    provider_error = None
    try:
        provider = get_provider(bank)
    except (ValueError, TypeError) as exc:
        provider, provider_error = None, str(exc)
    sidebar(bank, provider, model)
    session_id = st.session_state.get("active_session")
    sessions = {s["session_id"]: s for s in bank.sessions()}
    if session_id and session_id not in sessions:
        session_id = st.session_state["active_session"] = None
    title = sessions[session_id]["title"] if session_id else "新对话"
    with st.container(horizontal=True, vertical_alignment="center", key="workspace_header"):
        st.markdown(f"#### {safe_label(title)}")
        if st.button(safe_label(model[:32]) + " ▾", help="选择本地模型或配置其他模型 API"):
            settings_dialog(bank)
        with st.popover("召回范围", icon=":material/filter_alt:"):
            documents = {m["document_id"]: m["source_title"] for m in bank.memories(True)}
            scope = st.selectbox(
                "使用哪些记忆",
                [None] + list(documents),
                format_func=lambda d: documents.get(d, "全部已读文章"),
                key=f"scope_{session_id}",
            )
        if st.button("记忆面板", icon=":material/view_sidebar:"):
            st.session_state["show_context"] = not st.session_state.get("show_context", False)
    status_text = (
        f"API · {urlsplit(endpoint).hostname or '未配置'} · 发送上下文至服务商"
        if name == "api"
        else "本地模型 · 自动召回已启用的记忆"
    )
    if name == "preview":
        status_text = "离线预览 · 不调用模型，不启用自动召回"
    st.markdown(f'<div class="mr-status">{html.escape(status_text)}</div>', unsafe_allow_html=True)
    if provider_error:
        st.warning(provider_error)
        if st.button("配置模型"):
            settings_dialog(bank)
    turns = bank.turns(session_id) if session_id else []
    conversation_column, inspector_column = (
        st.columns([2.3, 1], gap="large")
        if st.session_state.get("show_context")
        else (st.container(), None)
    )
    with conversation_column:
        if not turns:
            st.markdown(
                """<div class="mr-empty"><h1>从一段阅读，开始对话。</h1>
            <p>添加文章，或继续上次的思考。</p></div>""",
                unsafe_allow_html=True,
            )
        for turn in turns:
            render_turn(turn, bank)
    if inspector_column:
        with inspector_column:
            context_panel(bank, turns)
    if st.session_state.get("failed_text"):
        st.warning("上一条消息未完成。输入内容保留在下方，可复制后重新发送。")
        with st.expander("未完成的输入", expanded=False):
            st.code(st.session_state["failed_text"], language=None)

    def composer():
        return st.chat_input(
            "提问，或用 + 添加 TXT / Markdown 文章",
            key=f"composer_{session_id or 'new'}",
            accept_file=True,
            file_type=["txt", "md", "markdown"],
            disabled=provider is None,
        )

    if turns:
        payload = composer()  # Native bottom-pinned composer for an ongoing chat.
    else:
        with conversation_column, st.container(key="home_composer"):
            payload = composer()  # Inline on the blank entry screen, like a chat workspace.
            with st.container(horizontal=True, horizontal_alignment="center", key="home_actions"):
                if st.button(
                    "粘贴正文", icon=":material/content_paste:", disabled=provider is None
                ):
                    paste_dialog(bank, provider)
                if st.button("打开已读文章", icon=":material/folder_open:"):
                    readings_dialog(bank)
    if payload is not None:
        text = payload if isinstance(payload, str) else payload.text
        files = [] if isinstance(payload, str) else payload.files
        try:
            if files:
                file = files[0]
                body = file.getvalue().decode("utf-8-sig")
                with conversation_column:
                    with st.chat_message("user"):
                        st.text(f"▤ {file.name}")
                        if text:
                            st.text(text)
                    run_reading(bank, provider, file.name, body, question=text)
            elif text.strip():
                with conversation_column:
                    with st.chat_message("user"):
                        st.text(text)
                    with st.status("正在召回相关记忆并组织回答…", expanded=False) as status:
                        answer(bank, provider, ensure_session(bank), text, document_id=scope)
                        status.update(label="回答与引用已保存", state="complete")
            st.session_state.pop("failed_text", None)
            st.rerun()
        except UnicodeDecodeError:
            st.error("文件不是 UTF-8 文本，请转换编码后重新附加。")
        except (ValueError, RuntimeError, OSError) as exc:
            st.session_state["failed_text"] = text or (files[0].name if files else "")
            st.error(f"本次处理未完成：{exc}")


if __name__ == "__main__":
    main()
