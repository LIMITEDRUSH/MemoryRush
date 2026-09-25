from memoryrush.cli import main


def test_health_command_runs() -> None:
    assert main(["health"]) == 0


def test_process_command_runs_with_preview(tmp_path) -> None:
    source = tmp_path / "reading.md"
    source.write_text(
        "# Reading\n\nEvidence-linked memories can be checked against their source.",
        encoding="utf-8",
    )
    output_dir = tmp_path / "artifacts"

    result = main(
        [
            "process",
            str(source),
            "--provider",
            "preview",
            "--budget",
            "1",
            "--output-dir",
            str(output_dir),
        ]
    )

    assert result == 0
    assert len(list(output_dir.glob("run_*.json"))) == 1
