"""Reproduce the academic PDF from its canonical Markdown source.

Requires docs/whitepaper/requirements-render.txt. No network calls are performed.
"""

import hashlib
import html
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
)
from reportlab.platypus.tableofcontents import TableOfContents

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs/whitepaper/TokenPropulsion-Whitepaper-v1.0.0rc1.md"
OUTPUT = SOURCE.with_suffix(".pdf")


def fonts() -> None:
    choices = [
        (Path("C:/Windows/Fonts/arial.ttf"), Path("C:/Windows/Fonts/arialbd.ttf")),
        (
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        ),
    ]
    for normal, bold in choices:
        if normal.is_file() and bold.is_file():
            pdfmetrics.registerFont(TTFont("Paper", str(normal)))
            pdfmetrics.registerFont(TTFont("PaperBold", str(bold)))
            pdfmetrics.registerFontFamily("Paper", normal="Paper", bold="PaperBold")
            return
    raise RuntimeError("Install Arial or DejaVu Sans fonts before rendering")


def inline(text: str) -> str:
    escaped = html.escape(text, quote=False)
    escaped = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", escaped)
    escaped = re.sub(r"`([^`]+)`", r"<font name='Courier'>\1</font>", escaped)
    return re.sub(r"(https?://[^\s]+)", r'<link href="\1" color="#176493">\1</link>', escaped)


class PaperDocument(BaseDocTemplate):
    def afterFlowable(self, flowable: object) -> None:  # noqa: N802 -- ReportLab hook
        if isinstance(flowable, Paragraph) and flowable.style.name == "Section":
            title = flowable.getPlainText()
            key = hashlib.sha256(title.encode()).hexdigest()[:16]
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(title, key, 0, False)
            self.notify("TOCEntry", (0, title, self.page, key))


def main() -> None:
    fonts()
    text = SOURCE.read_text(encoding="utf-8")
    count_body = text.split("<!-- WORD_COUNT_START -->")[1].split("<!-- WORD_COUNT_END -->")[0]
    if len(re.findall(r"\S+", count_body)) != 10_000:
        raise ValueError("Canonical body must contain exactly 10000 counted words")
    body = ParagraphStyle(
        "Body",
        fontName="Paper",
        fontSize=10.2,
        leading=15.1,
        spaceAfter=8.5,
        textColor=colors.HexColor("#223044"),
        alignment=TA_LEFT,
        allowWidows=0,
        allowOrphans=0,
    )
    section = ParagraphStyle(
        "Section",
        parent=body,
        fontName="PaperBold",
        fontSize=16,
        leading=20,
        spaceBefore=19,
        spaceAfter=12,
        keepWithNext=True,
    )
    title = ParagraphStyle(
        "CoverTitle", parent=section, fontSize=29, leading=35, spaceBefore=0, spaceAfter=18
    )
    subtitle = ParagraphStyle("Subtitle", parent=body, fontSize=14, leading=21, spaceAfter=14)
    small = ParagraphStyle(
        "Small", parent=body, fontSize=9, leading=13, textColor=colors.HexColor("#546375")
    )
    reference = ParagraphStyle("Reference", parent=small, spaceAfter=12, splitLongWords=True)
    toc_style = ParagraphStyle("TocRow", parent=small, leading=15, spaceAfter=5)
    width, height = A4

    def furniture(canvas: object, doc: object) -> None:
        canvas.saveState()
        if doc.page > 1:
            canvas.setStrokeColor(colors.HexColor("#B8D9E8"))
            canvas.line(54, height - 39, width - 54, height - 39)
            canvas.setFont("PaperBold", 7.4)
            canvas.setFillColor(colors.HexColor("#345265"))
            canvas.drawString(54, height - 29, "TOKENPROPULSION / ENGINEERING WHITEPAPER")
            canvas.setFont("Paper", 7.2)
            canvas.drawRightString(width - 54, height - 29, "1.0.0rc1")
        canvas.setFont("Paper", 7.4)
        canvas.setFillColor(colors.HexColor("#657388"))
        canvas.drawString(54, 30, "Independent community project | 17 October 2026")
        canvas.drawRightString(width - 54, 30, str(doc.page))
        canvas.restoreState()

    doc = PaperDocument(
        str(OUTPUT),
        pagesize=A4,
        leftMargin=54,
        rightMargin=54,
        topMargin=57,
        bottomMargin=53,
        title="TokenPropulsion Engineering Whitepaper",
        author="Ciprian Ștefan Pleșca",
        subject="Auditable prompt formatting; evidence-bounded optimization",
    )
    frame = Frame(
        54,
        53,
        width - 108,
        height - 110,
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0,
    )
    doc.addPageTemplates(PageTemplate(id="Paper", frames=[frame], onPage=furniture))
    story = [
        Spacer(1, 12),
        Paragraph("TokenPropulsion", title),
        Paragraph("Auditable Prompt Formatting and Evidence-Bounded Optimization", subtitle),
        Spacer(1, 10),
        Image(
            str(ROOT / "assets/tokenpropulsion-hero-preview.jpg"),
            width=width - 108,
            height=(width - 108) * 9 / 16,
        ),
        Spacer(1, 24),
        Paragraph("Ciprian Ștefan Pleșca", subtitle),
        Paragraph("Version 1.0.0rc1 | 17 October 2026 | MIT", body),
        Paragraph("Independent engineering whitepaper. Not peer reviewed.", body),
        Paragraph(
            "Exactly 10,000 whitespace-delimited words in the counted body, including "
            "headings and citations; front matter and references excluded.",
            small,
        ),
        Spacer(1, 8),
        Paragraph(
            "Local engineering evidence does not establish universal semantic equivalence "
            "or live xAI compatibility. This project is independent of xAI, SpaceX, "
            "and Elon Musk.",
            small,
        ),
        PageBreak(),
        Paragraph("Contents", title),
    ]
    toc = TableOfContents()
    toc.levelStyles = [toc_style]
    story.extend([toc, PageBreak()])
    content = text.split("<!-- WORD_COUNT_START -->", 1)[1].replace("<!-- WORD_COUNT_END -->", "")
    for block in re.split(r"\n\s*\n", content.strip()):
        block = block.strip()
        if not block:
            continue
        if block.startswith("## "):
            heading = block[3:].strip()
            if heading == "References":
                story.append(PageBreak())
            story.append(Paragraph(inline(heading), section))
        else:
            paragraph = " ".join(block.splitlines())
            story.append(
                Paragraph(inline(paragraph), reference if paragraph.startswith("[") else body)
            )
    doc.multiBuild(story)
    print(f"Rendered {OUTPUT.name}")


if __name__ == "__main__":
    main()
