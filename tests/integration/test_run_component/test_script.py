import pytest
import sys
from io import StringIO
from contextlib import redirect_stdout

### VIASH START # noqa: E266
meta = {
    "memory_gb": 6,
}
### VIASH END # noqa: E266


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
    temp_stdout = StringIO()
    print(f"meta: {meta}")
    assert (
        meta["memory_gb"] is not None
    ), "This test should be executed with some --memory set."
    with redirect_stdout(temp_stdout):
        result = pytest.main([__file__], plugins=["viashpy"])
    stdout_str = temp_stdout.getvalue()
    print(stdout_str)
    assert (
        "Different values were defined in the 'meta' dictionary that limit memory, choosing the one with the smallest unit"
        not in stdout_str
    )
    sys.exit(result)
