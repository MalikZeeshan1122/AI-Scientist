from __future__ import annotations

from ..models import Draft


def render_markdown(draft: Draft) -> str:
    parts = [f"# {draft.title}", "", "## Abstract", draft.abstract, ""]
    for sec in draft.sections:
        parts.append(f"## {sec.name}")
        parts.append(sec.content)
        parts.append("")
    if draft.references:
        parts.append("## References")
        for i, ref in enumerate(draft.references, 1):
            parts.append(f"{i}. {ref}")
    return "\n".join(parts).rstrip() + "\n"
