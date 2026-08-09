from memoryrush.cli import main


def test_health_command_runs() -> None:
    assert main(["health"]) == 0
