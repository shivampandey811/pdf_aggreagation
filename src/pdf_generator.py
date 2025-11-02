from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.enums import TA_LEFT
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class PDFGenerator:
    def __init__(self, page_size=letter, margin=0.5):
        self.page_size = page_size
        self.margin = margin * inch
        self.green_color = colors.HexColor("#008000")
        self.black_color = colors.HexColor("#000000")
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        self.styles.add(ParagraphStyle(
            name="StrikeThrough",
            parent=self.styles["Normal"],
            fontSize=10,
            textColor=self.black_color,
            fontName="Helvetica"
        ))

        self.styles.add(ParagraphStyle(
            name="AddedText",
            parent=self.styles["Normal"],
            fontSize=10,
            textColor=self.green_color,
            fontName="Helvetica-Bold"
        ))

        self.styles.add(ParagraphStyle(
            name="PartIField",
            parent=self.styles["Normal"],
            fontSize=10,
            alignment=TA_LEFT,
            fontName="Helvetica"
        ))

    def create_pdf(self, template_data: Dict, field_values: Dict,
                   amendments: Dict, output_path: str) -> bool:
        try:
            doc = SimpleDocTemplate(output_path,
                                    pagesize=letter,
                                    leftMargin=self.margin,
                                    rightMargin=self.margin,
                                    topMargin=self.margin,
                                    bottomMargin=self.margin,
                                    title="Charter Party - Final Filled")

            story = []

            # Title
            story.append(Paragraph(
                "<b>CHARTER PARTY – FILLED TEMPLATE (Final Version)</b>",
                self.styles["Heading1"]
            ))
            story.append(Spacer(1, 0.2 * inch))

            # Build Part I
            part_i_story = self._build_part_i(template_data, field_values)
            if part_i_story:
                story.extend(part_i_story)
            else:
                logger.warning("[PDF] _build_part_i returned empty story list")
            story.append(PageBreak())

            # Build Part II
            part_ii_story = self._build_part_ii(template_data, amendments)
            if part_ii_story:
                story.extend(part_ii_story)
            else:
                logger.warning("[PDF] _build_part_ii returned empty story list")

            doc.build(story)
            logger.info(f"PDF created successfully: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Error creating PDF: {e}")
            return False

    def _build_part_i(self, template_data: Dict, field_values: Dict) -> List:
        story = []
        story.append(Paragraph(
            "<b>Part I – Commercial Terms (Filled Values)</b>",
            self.styles["Heading2"]
        ))
        story.append(Spacer(1, 0.1 * inch))

        table_data = []

        for field_num in range(1, 20):
            label = field_values.get(field_num, {}).get("label", "").strip() or \
                template_data.get("part_i", {}).get(field_num, {}).get("label", "").strip()
            value = field_values.get(field_num, {}).get("value", "").strip()

            logger.debug(f"[PDF] Part I Field {field_num}: Label='{label}', Value='{value}'")
            print(f"[PDF] Part I Field {field_num}: Label='{label}', Value='{value}'")

            if label:
                display_value = value if value else "_____"
                table_data.append([
                    Paragraph(f"<b>{field_num}.</b>", self.styles["PartIField"]),
                    Paragraph(f"<b>{label}</b>", self.styles["PartIField"]),
                    Paragraph(display_value, self.styles["PartIField"]),
                ])
            else:
                logger.warning(f"[PDF] Skipped Part I Field {field_num} due to missing label.")

        if table_data:
            t = Table(table_data, colWidths=[0.5 * inch, 2.5 * inch, 3.5 * inch])
            t.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
            ]))
            story.append(t)
        else:
            logger.warning("[PDF] No Part I data to render")
            print("[PDF] No Part I data to render")

        return story

    def _build_part_ii(self, template_data: Dict, amendments: Dict) -> List:
        story = []
        story.append(Paragraph(
            "<b>Part II – Finalized Clauses (Amendments Incorporated)</b>",
            self.styles["Heading2"]
        ))
        story.append(Spacer(1, 0.1 * inch))

        clauses = template_data.get("part_ii", [])
        logger.debug(f"[PDF] Number of clauses in template: {len(clauses)}")
        print(f"[PDF] Number of clauses in template: {len(clauses)}")

        for idx, clause in enumerate(clauses):
            title = clause.get('title', '')
            logger.debug(f"[PDF] Clause {idx + 1}: Title='{title}'")
            print(f"[PDF] Clause {idx + 1}: Title='{title}'")
            story.append(Paragraph(f"<b>{title}</b>", self.styles["Heading3"]))

            content = clause.get("content", [])
            logger.debug(f"[PDF] Clause {idx + 1} content lines: {len(content)}")
            print(f"[PDF] Clause {idx + 1} content lines: {len(content)}")

            for i, item in enumerate(content):
                line_num = item.get("line", "")
                text = item.get("text", "").strip()
                logger.debug(f"[PDF] Clause {idx + 1}, line {i + 1}: line_num={line_num}, text='{text[:100]}'")
                print(f"[PDF] Clause {idx + 1}, line {i + 1}: line_num={line_num}, text='{text[:100]}'")

                if line_num:
                    formatted_text = f"<b>{line_num:2d}</b>&nbsp;&nbsp;{text}"
                    story.append(Paragraph(formatted_text, self.styles["PartIField"]))
                else:
                    story.append(Paragraph(text, self.styles["PartIField"]))

            story.append(Spacer(1, 0.05 * inch))

        if amendments.get("deleted"):
            story.append(Paragraph("<b>Deleted Content:</b>", self.styles["Heading3"]))
            for item in amendments["deleted"]:
                logger.debug(f"[PDF] Deleted amendment: {item.get('text','')}")
                print(f"[PDF] Deleted amendment: {item.get('text','')}")
                deleted_text = f"~~{item['text']}~~"
                story.append(Paragraph(deleted_text, self.styles["StrikeThrough"]))

        if amendments.get("added"):
            story.append(Spacer(1, 0.05 * inch))
            story.append(Paragraph("<b>Added Content:</b>", self.styles["Heading3"]))
            for item in amendments["added"]:
                logger.debug(f"[PDF] Added amendment: {item.get('text','')}")
                print(f"[PDF] Added amendment: {item.get('text','')}")
                story.append(Paragraph(item["text"], self.styles["AddedText"]))

        if amendments.get("new"):
            story.append(Spacer(1, 0.05 * inch))
            story.append(Paragraph("<b>New Lines:</b>", self.styles["Heading3"]))
            logger.debug(f"[PDF] Appending {len(amendments['new'])} new lines")
            print(f"[PDF] Appending {len(amendments['new'])} new lines")
            for item in amendments["new"]:
                text = item.get("text", "")
                logger.debug(f"[PDF] New line amendment: {text}")
                print(f"[PDF] New line amendment: {text}")
                story.append(Paragraph(text, self.styles["AddedText"]))

        return story
