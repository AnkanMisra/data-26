import os
from fpdf import FPDF
import glob
import re

OUTPUT_FILENAME = "Submission_BridgeTheGap.pdf"


class PDF(FPDF):
    def header(self):
        # UIDAI Blue Line
        self.set_draw_color(26, 35, 126)  # #1a237e
        self.set_line_width(1)
        self.line(10, 10, 200, 10)

        self.set_font("helvetica", "B", 9)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, "UIDAI Data Hackathon 2026 | Technical Submission", align="R")
        self.ln(15)

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")

        # Bottom Blue Line
        self.set_draw_color(26, 35, 126)
        self.line(10, 285, 200, 285)

    def cover_page(self):
        self.add_page()

        # Logo placeholder or graphic element
        self.set_fill_color(240, 248, 255)  # AliceBlue
        self.rect(0, 0, 210, 297, "F")

        self.ln(80)

        # Title
        self.set_font("helvetica", "B", 24)
        self.set_text_color(26, 35, 126)  # UIDAI Blue
        self.multi_cell(
            0, 10, "Bridge the Gap:\nA Dynamic Resource Allocation Framework", align="C"
        )
        self.ln(10)

        # Subtitle
        self.set_font("helvetica", "", 14)
        self.set_text_color(50, 50, 50)
        self.cell(
            0,
            10,
            "Solving 'Lifecycle Latency' via Data-Driven Intelligence",
            align="C",
            new_x="LMARGIN",
            new_y="NEXT",
        )
        self.ln(40)

        # Box for Team Info
        self.set_draw_color(100, 100, 100)
        self.set_line_width(0.5)
        self.set_fill_color(255, 255, 255)
        self.rect(60, 180, 90, 40, "FD")

        self.set_y(185)
        self.set_font("helvetica", "B", 10)
        self.set_text_color(0, 0, 0)
        self.cell(0, 6, "SUBMITTED BY:", align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_font("helvetica", "", 10)
        self.cell(0, 6, "[Your Team Name]", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(2)
        self.cell(0, 6, "DATE: 16 Jan 2026", align="C", new_x="LMARGIN", new_y="NEXT")

        self.add_page()  # Start content on new page

    def chapter_title(self, label):
        self.set_font("helvetica", "B", 16)
        self.set_text_color(26, 35, 126)  # UIDAI Blue
        self.cell(0, 10, label, new_x="LMARGIN", new_y="NEXT")
        # Underline
        self.set_draw_color(26, 35, 126)
        self.set_line_width(0.5)
        self.line(self.get_x(), self.get_y(), self.get_x() + 190, self.get_y())
        self.ln(6)

    def chapter_subtitle(self, label):
        self.set_font("helvetica", "B", 12)
        self.set_text_color(50, 50, 50)  # Dark Grey
        self.cell(0, 8, label.upper(), new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def chapter_subsubtitle(self, label):
        self.set_font("helvetica", "I", 11)
        self.set_text_color(70, 70, 70)
        self.cell(0, 6, label, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def body_text(self, txt):
        self.set_font("helvetica", "", 10)  # Slightly smaller, cleaner reading
        self.set_text_color(0, 0, 0)
        self.multi_cell(0, 5, txt)
        self.ln()

    def code_block(self, txt):
        self.set_font("courier", "", 8)
        self.set_fill_color(245, 245, 245)
        self.set_text_color(0, 0, 0)
        self.multi_cell(0, 4, txt, fill=True)
        self.ln()


def clean_text(text):
    # Aggressive latin-1 cleaning
    replacements = {
        "\u2013": "-",
        "\u2014": "--",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2026": "...",
        "\u2212": "-",
        "**": "",
        "*": "",  # Strip markdown bold/italic markers for plain text
    }
    for old, new in replacements.items():
        text = text.replace(old, new)

    # Final safety: encode to latin-1, replace errors
    return text.encode("latin-1", "replace").decode("latin-1")


def create_submission_pdf():
    print("Generating Professional PDF...")
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.cover_page()

    # 1. Parse FINAL_REPORT.md
    with open("FINAL_REPORT.md", "r", encoding="utf-8") as f:
        lines = f.readlines()

    in_code_block = False
    code_buffer = ""

    for line in lines:
        line = line.strip()

        # Handle Code Blocks
        if line.startswith("```"):
            if in_code_block:
                pdf.code_block(clean_text(code_buffer))
                code_buffer = ""
                in_code_block = False
            else:
                in_code_block = True
            continue

        if in_code_block:
            code_buffer += line + "\n"
            continue

        # Skip empty lines
        if not line:
            pdf.ln(2)
            continue

        # Headers
        if line.startswith("# "):
            pdf.add_page()  # Ensure chapters start on new page
            pdf.chapter_title(clean_text(line[2:]))
        elif line.startswith("## "):
            pdf.chapter_subtitle(clean_text(line[3:]))
        elif line.startswith("### "):
            pdf.chapter_subsubtitle(clean_text(line[4:]))

        # Images: ![Alt](path)
        elif line.startswith("!["):
            try:
                # Extract path
                match = re.search(r"\((.*?)\)", line)
                if match:
                    img_path = match.group(1)
                    if os.path.exists(img_path):
                        pdf.ln(5)
                        # Center image, roughly 100mm wide
                        pdf.image(img_path, w=150, x=30)
                        pdf.ln(5)
                    else:
                        pdf.body_text(f"[Image missing: {img_path}]")
            except Exception as e:
                print(f"Image error: {e}")

        # Tables (Simple detection)
        elif line.startswith("|"):
            pdf.set_font("courier", "", 8)
            pdf.cell(0, 4, clean_text(line), new_x="LMARGIN", new_y="NEXT")

        # Math Formula (Latex style in MD)
        elif "$$" in line:
            pdf.body_text(clean_text(line.replace("$$", "")))

        # Standard Text
        else:
            pdf.body_text(clean_text(line))

    # 2. Append Source Code
    pdf.add_page()
    pdf.chapter_title("Appendix: Source Code")

    source_files = glob.glob("src/*.py")
    for file_path in source_files:
        pdf.chapter_subtitle(f"File: {file_path}")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                code_content = f.read()
            pdf.code_block(clean_text(code_content))
        except Exception as e:
            pdf.body_text(f"Error reading file: {e}")

    pdf.output(OUTPUT_FILENAME)
    print(f"PDF successfully generated: {OUTPUT_FILENAME}")


if __name__ == "__main__":
    create_submission_pdf()
