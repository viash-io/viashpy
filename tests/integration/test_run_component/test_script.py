import pytest

def test_run_component(run_component):
    run_component(["--output", "bar.txt"])
    with open("bar.txt", 'r') as open_output_file:
        contents = open_output_file.read()
        assert contents == "foo!"

if __name__ == '__main__':
    pytest.main([__file__], plugins=["viashpy"])