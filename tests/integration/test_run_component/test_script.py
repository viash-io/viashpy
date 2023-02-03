import pytest
import sys


def test_run_component(run_component):
    captured_output = run_component(["--output", "bar.txt"])
    with open("bar.txt", "r") as open_output_file:
        contents = open_output_file.read()
        assert contents == "foo!"
    assert (
        captured_output is not None
    ), "Some output from stdout or stderr should have been captured"
    assert b"This is a logging statement" in captured_output

if __name__ == "__main__":
    sys.exit(pytest.main([__file__], plugins=["viashpy"]))
