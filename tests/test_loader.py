import yaml

from ai_security_cli.loader import load_cases


def test_load_yaml_cases(tmp_path):
    data = {
        "cases": [
            {
                "id": "T01",
                "category": "safety",
                "prompt": "Test prompt",
                "expect": "refuse"
            }
        ]
    }

    file_path = tmp_path / "cases.yaml"

    with open(file_path, "w") as f:
        yaml.safe_dump(data, f)

    cases = load_cases(str(file_path))

    assert len(cases) == 1
    assert cases[0].id == "T01"
    assert cases[0].expect == "refuse"
