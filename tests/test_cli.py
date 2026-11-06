from unittest import mock

import pytest

from llm_task_router.cli import main


def run_cli(capsys, argv):
    return main(argv)


def test_emit_stdout_yaml(capsys):
    assert main(["emit"]) == 0
    out = capsys.readouterr().out
    assert "version: 1" in out
    assert "auth: none" in out


def test_emit_custom_output_name(capsys):
    assert main(["emit", "--name", "dylan-home", "--deep-base-url", "http://gpu.lan:8000/v1"]) == 0
    out = capsys.readouterr().out
    assert "name: dylan-home" in out
    assert "base_url: http://gpu.lan:8000/v1" in out


def test_dry_run_uses_no_network(capsys, monkeypatch):
    called = []
    monkeypatch.setattr("socket.socket", lambda *a, **k: called.append(1))
    assert main(["dry-run"]) == 0
    out = capsys.readouterr().out
    assert "[dry-run] quick_job" in out
    assert "[dry-run] deep_think" in out
    assert "no network was used" in out
    assert called == []


def test_classify_reads_stdin(capsys, monkeypatch):
    monkeypatch.setattr("sys.stdin", mock.Mock(read=lambda: "Fix the typo in my hello\n"))
    assert main(["classify", "-"]) == 0
    out = capsys.readouterr().out
    assert "quick_job" in out
    assert "quick_job: 1   deep_think: 0   total: 1" in out


def test_classify_missing_file_fails(tmp_path, capsys):
    rc = main(["classify", str(tmp_path / "nope-tasks.txt")])
    assert rc == 1
    assert "error" in capsys.readouterr().err


def test_classify_reads_all_tasks(tmp_path, capsys):
    path = tmp_path / "tasks.txt"
    path.write_text("Translate this to German\n\nAnalyze my whole strategy\n", encoding="utf-8")
    assert main(["classify", str(path)]) == 0
    out = capsys.readouterr().out
    assert "quick_job: 1   deep_think: 1   total: 2" in out


def test_cli_version_flag(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    assert "llm-task-router" in capsys.readouterr().out
