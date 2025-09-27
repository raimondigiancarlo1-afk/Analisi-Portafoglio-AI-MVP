
from pathlib import Path

def render_text_report(summary:dict)->str:
    lines = []
    lines.append("# Report Analisi Portafoglio (MVP)")
    lines.append("")
    for k,v in summary.items():
        lines.append(f"- **{k}**: {v}")
    return "\n".join(lines)

def save_markdown_report(path:Path, md:str):
    path.write_text(md, encoding="utf-8")
    return str(path)
