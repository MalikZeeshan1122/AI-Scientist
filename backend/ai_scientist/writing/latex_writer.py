from __future__ import annotations

from ..models import Draft

_PREAMBLE = r"""\documentclass[11pt]{article}
\usepackage[margin=1in]{geometry}
\usepackage{hyperref}
\usepackage{amsmath, amssymb}
\usepackage{graphicx}
\usepackage{booktabs}
"""


def _escape(s: str) -> str:
    repl = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    out = []
    for ch in s:
        out.append(repl.get(ch, ch))
    return "".join(out)


def render_latex(draft: Draft) -> str:
    body = [
        _PREAMBLE,
        f"\\title{{{_escape(draft.title)}}}",
        "\\author{AI Scientist}",
        "\\date{\\today}",
        "\\begin{document}",
        "\\maketitle",
        "\\begin{abstract}",
        _escape(draft.abstract),
        "\\end{abstract}",
    ]
    for sec in draft.sections:
        body.append(f"\\section{{{_escape(sec.name)}}}")
        body.append(_escape(sec.content))
    if draft.references:
        body.append("\\section*{References}")
        body.append("\\begin{enumerate}")
        for ref in draft.references:
            body.append(f"  \\item {_escape(ref)}")
        body.append("\\end{enumerate}")
    body.append("\\end{document}")
    return "\n\n".join(body) + "\n"
