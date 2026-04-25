import json


def generate_possibilities(template: str) -> list[str]:
    results = []

    def recurse(built: str, i: int):
        if i == len(template):
            results.append(built)
            return

        if template[i] == "x":
            recurse(built + "0", i + 1)
            recurse(built + "1", i + 1)
        else:
            recurse(built + template[i], i + 1)

    recurse("", 0)
    return results


instruction_templates: list[dict[str, str]] = []
with open("gameboy_instrs.json") as f:
    instruction_templates = json.load(f)

for template in instruction_templates:
    possibilities = generate_possibilities(template["bit_desc"])
    opcodes = [
        "0x" + hex(int("0b" + possibility, 2)).upper()[2:]
        for possibility in possibilities
    ]
    print(f"            case {" | ".join(opcodes)}:  pass # {template["name"].upper()}")
