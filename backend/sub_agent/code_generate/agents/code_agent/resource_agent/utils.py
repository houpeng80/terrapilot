def build_skills(skills: dict[str, dict]) -> str:
    skill_items = "\n".join(
        f"    <skill>\n        <name>{skill["name"]}</name>\n        <description>{skill["description"]}</description>\n    </skill>"
        for name, skill in skills.items()
    )
    return skill_items