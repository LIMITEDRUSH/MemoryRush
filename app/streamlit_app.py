"""Minimal Streamlit shell for Phase 0."""

from __future__ import annotations

from pathlib import Path

import streamlit as st


def list_sample_docs(sample_dir: Path) -> list[Path]:
    if not sample_dir.exists():
        return []
    return sorted(
        p for p in sample_dir.iterdir() if p.is_file() and p.suffix.lower() in {".txt", ".md"}
    )


def main() -> None:
    st.set_page_config(page_title="MemoryRush", page_icon="MR", layout="wide")

    st.title("MemoryRush")
    st.caption("Local-first reading memory retrieval system.")

    sample_dir = Path("data/sample_docs")
    sample_docs = list_sample_docs(sample_dir)

    st.subheader("Phase 0 Setup")
    st.write("The project skeleton is ready. Next step: TXT / Markdown parsing.")

    st.subheader("Sample Documents")
    if sample_docs:
        for doc in sample_docs:
            st.write(f"- `{doc.as_posix()}`")
    else:
        st.info("No sample documents found yet.")


if __name__ == "__main__":
    main()
