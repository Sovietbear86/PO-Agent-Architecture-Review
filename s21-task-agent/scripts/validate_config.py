from pathlib import Path
import yaml

required = [
    Path("config/agent.yaml"),
    Path("config/search_weights.yaml"),
    Path("config/quality_profiles.yaml"),
    Path("AGENT.md"),
]

for path in required:
    if not path.exists():
        raise SystemExit(f"Отсутствует обязательный файл: {path}")

for path in Path("config").glob("*.yaml"):
    with path.open("r", encoding="utf-8") as fh:
        yaml.safe_load(fh)

print("Конфигурация корректна.")
