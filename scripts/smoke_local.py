"""Real local-model integration check using synthetic reading, never user documents."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import timedelta
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from memoryrush.bank import MemoryBank, current_strength, data_directory, now_utc
from memoryrush.chat import answer
from memoryrush.pipeline import process_text
from memoryrush.providers import LlamaCppProvider


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume-directory", type=Path)
    args = parser.parse_args()
    directory = args.resume_directory or data_directory() / "verification" / uuid4().hex[:12]
    bank = MemoryBank(directory / "test.sqlite3")
    provider = LlamaCppProvider()
    complete = provider.complete_json

    def traced(prompt, max_tokens=4096, schema=None):
        result = complete(prompt, max_tokens, schema)
        trace = {"prompt": prompt, "response": result}
        (directory / f"call-{uuid4().hex[:10]}.json").write_text(
            json.dumps(trace, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return result

    provider.complete_json = traced
    text = """# 阅读记忆的工作方式（功能测试示例）

记忆的基础分衡量一条信息是否值得保留。重要性、未来用途和个人兴趣可以参与评分。相关性则衡量这条记忆能否帮助回答当前问题，不能用基础分替代相关性。

记忆强度随未使用的时间增长而衰减。半衰期表示强度下降到一半所需的时间。真正用于回答的记忆会被强化；仅出现在候选列表中的记忆不应因此增强。

回答引用记忆时应附上原文证据。来源不明的内容不能仅因为模型给了高分就被当成可靠记忆。这些规则是软件设计示例，不是已经验证的心理学规律。
"""
    print(f"Verification data: {directory}", flush=True)
    if not args.resume_directory:
        artifact = process_text("local-smoke.md", text, provider, memory_budget=4)
        assert artifact.validation.valid, artifact.validation
        bank.import_artifact(artifact)
    assert bank.memories(True), "Real LLM admitted no memories."
    print(f"Real LLM extraction + scoring: {len(bank.memories(True))} active memories", flush=True)
    bank = MemoryBank(directory / "test.sqlite3")
    first = bank.memories(True)[0]
    start = now_utc()
    assert current_strength(
        first, start + timedelta(days=first["half_life_days"])
    ) < current_strength(first, start)
    session = bank.new_session()
    turn1 = answer(bank, provider, session, "记忆强度随时间如何变化？半衰期是什么意思？")
    assert turn1["used_memory_ids"], turn1
    print("First grounded answer:", turn1["answer"], flush=True)
    bank = MemoryBank(directory / "test.sqlite3")
    turn2 = answer(bank, provider, session, "那它和基础分有什么区别？")
    assert turn2["used_memory_ids"], turn2
    print("Follow-up after reopening database:", turn2["answer"], flush=True)
    turn3 = answer(bank, provider, session, "请给我北海道今天的实时天气与温度。")
    assert turn3["insufficient_evidence"] and not turn3["used_memory_ids"]
    receipt = {
        "provider": provider.name,
        "model": provider.model_name,
        "artifact": bank.artifacts()[0],
        "turns": [turn1, turn2, turn3],
        "checks": [
            "real extraction",
            "separate model scoring",
            "restart persistence",
            "time decay",
            "automatic recall",
            "grounded citations",
            "follow-up history",
            "unrelated query abstention",
        ],
        "scope": "software integration only; no scientific performance claim",
    }
    (directory / "receipt.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"PASS: {directory / 'receipt.json'}", flush=True)


if __name__ == "__main__":
    main()
