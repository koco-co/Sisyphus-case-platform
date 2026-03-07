from pathlib import Path


def export_markdown(task_id: int, payload: dict) -> str:
    export_dir = Path('/tmp/sisyphus-exports')
    export_dir.mkdir(parents=True, exist_ok=True)
    output_path = export_dir / f'task-{task_id}.md'

    cases = payload.get('cases', [])
    lines = [f'# Task {task_id} Export', '']
    for index, case in enumerate(cases, start=1):
        lines.append(f'## {index}. {case.get("title", "Untitled Case")}')
        lines.append(f'- Module: {case.get("module", "General")}')
        lines.append('')

    output_path.write_text('\n'.join(lines), encoding='utf-8')
    return str(output_path)
