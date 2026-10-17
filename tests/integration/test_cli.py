import io
import json

import pytest

from tokenpropulsion.cli import main


def test_stdout_stats(capsys):
    assert main(["Hello.   ", "--stats"]) == 0
    out, err = capsys.readouterr()
    assert out == "Hello."
    assert json.loads(err)["counts_exact"] is False
    assert "Hello" not in err


def test_files_json_analyze_stdin(tmp_path, capsys, monkeypatch):
    source, dest = tmp_path / "input.txt", tmp_path / "out.txt"
    source.write_text("Hello.   ", encoding="utf-8")
    assert main(["-f", str(source), "-o", str(dest)]) == 0
    assert dest.read_text() == "Hello."
    assert main(["analyze", "-f", str(source)]) == 0
    assert json.loads(capsys.readouterr().out)["original_text"] == "Hello.   "
    assert main(["Hello.   ", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["optimized_text"] == "Hello."
    monkeypatch.setattr("sys.stdin", io.StringIO("Piped.   "))
    assert main([]) == 0
    assert capsys.readouterr().out == "Piped."


def test_benchmark_cli(capsys):
    assert main(["benchmark", "--dataset", "benchmarks/datasets/sample.jsonl"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["failure_cases"] == []
    assert report["mode"] == "offline"


@pytest.mark.parametrize("args", [["benchmark"], ["x", "-f", "file"], ["--level", "bad"]])
def test_argument_errors(args):
    with pytest.raises(SystemExit) as caught:
        main(args)
    assert caught.value.code == 2


def test_io_error_and_help(tmp_path, capsys):
    assert main(["-f", str(tmp_path / "absent")]) == 2
    assert "inaccessible" in capsys.readouterr().err
    source = tmp_path / "huge"
    source.write_text("a" * 1000001)
    assert main(["-f", str(source)]) == 2
    with pytest.raises(SystemExit) as caught:
        main(["--help"])
    assert caught.value.code == 0


def test_broken_pipe(monkeypatch):
    class Broken:
        def write(self, text):
            raise BrokenPipeError

    monkeypatch.setattr("sys.stdout", Broken())
    assert main(["Hello."]) == 1


def test_protected_crlf_file_round_trip(tmp_path, capsys):
    source, destination = tmp_path / "code.txt", tmp_path / "output.txt"
    text = b"```python\r\nx =  1  \r\n```\r\n"
    source.write_bytes(text)
    assert main(["-f", str(source), "-o", str(destination)]) == 0
    assert destination.read_bytes() == text
    assert main(["-f", str(source)]) == 0
    assert capsys.readouterr().out == text.decode()


def test_binary_stdin(monkeypatch, capsys):
    class Input:
        buffer = io.BytesIO(b"Hello.   ")

    monkeypatch.setattr("sys.stdin", Input())
    assert main([]) == 0
    assert capsys.readouterr().out == "Hello."
