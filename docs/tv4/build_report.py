"""Ghép báo cáo cuối từ các chương Markdown của TV1..TV4 thành DOCX (python-docx).   [TV4]

Dùng: python docs/tv4/build_report.py [đường_dẫn_docx]
- Đánh số lại mục Ch.6 và Ch.8 theo thứ tự báo cáo (KB1..KB6), đánh số Hình/Bảng theo chương.
- Bảng được đánh số tự động; tiêu đề lấy từ mục đứng ngay trước bảng.
- Hình: dòng Markdown ![chú thích](đường_dẫn_tương_đối_với_file_md).
- Liên kết tương đối tới file trong repo chỉ giữ nhãn (PDF không dùng được); liên kết http giữ nguyên.
Xuất PDF: docs/tv4/export_pdf.ps1 (cần Microsoft Word).
"""
import re
import sys
from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

DOCS = Path(__file__).resolve().parent.parent
OUTPUT = Path(sys.argv[1]) if len(sys.argv) > 1 else DOCS / "tv4" / "BaoCao_DoAn_BigData.docx"
TV1_FIGS = {  # hình bổ sung cho phần TV1 (vẽ từ benchmark_final.csv bằng scripts/plot_tv1_benchmarks.py)
    "6.1": [("KB1 – thời gian theo tỷ lệ dữ liệu (cách `sample`)", "evidence/tv1/kb1_size_sample.png"),
            ("KB1 – thời gian theo tỷ lệ dữ liệu (lọc theo ngày)", "evidence/tv1/kb1_size_days.png")],
    "6.2": [("KB2 – thời gian theo số core", "evidence/tv1/kb2_cores.png")],
    "6.3": [("KB6 – thời gian theo số shuffle partition", "evidence/tv1/kb6_partitions.png")],
}

doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21), Cm(29.7)
sec.top_margin = sec.bottom_margin = Cm(2.2)
sec.left_margin = sec.right_margin = Cm(2.3)
AVAIL = int(sec.page_width - sec.left_margin - sec.right_margin)


def setfont(style, size=11, bold=None):
    style.font.name = "Times New Roman"
    style.font.size = Pt(size)
    style.font.color.rgb = RGBColor(0, 0, 0)
    if bold is not None:
        style.font.bold = bold
    fonts = style.element.get_or_add_rPr().find(qn("w:rFonts"))
    if fonts is not None:
        for k in ["asciiTheme", "hAnsiTheme", "eastAsiaTheme", "cstheme"]:
            fonts.attrib.pop(qn("w:" + k), None)
        for k in ["ascii", "hAnsi", "eastAsia", "cs"]:
            fonts.set(qn("w:" + k), "Times New Roman")


for st in doc.styles:
    if st.type in (1, 2):
        setfont(st)
    if st.type == 1:
        st.paragraph_format.space_after = Pt(5)
        st.paragraph_format.line_spacing = 1.08
for name, size in [("Heading 1", 15), ("Heading 2", 13), ("Heading 3", 11.5)]:
    setfont(doc.styles[name], size, True)
    pf = doc.styles[name].paragraph_format
    pf.keep_with_next = True
    pf.space_before = Pt(12 if name != "Heading 3" else 8)
    pf.space_after = Pt(6)
for b in doc.styles.element.xpath("//w:pBdr"):
    b.getparent().remove(b)

state = {"chap": "", "fig": 0, "tab": 0, "caption": "", "tables_in_sec": 0, "sec_title": ""}


def run(p, text, bold=False, italic=False, mono=False, size=None):
    r = p.add_run(text)
    r.bold, r.italic = bold, italic
    r.font.name = "Consolas" if mono else "Times New Roman"
    if mono:
        r._r.get_or_add_rPr().find(qn("w:rFonts")).set(qn("w:eastAsia"), "Consolas")
    r.font.size = Pt(size or (9.5 if mono else 11))
    r.font.color.rgb = RGBColor(0, 0, 0)
    return r


def inline(p, text, size=None, base_bold=False, ital=False):
    for tok in re.split(r"(\[[^\]]+\]\([^)]+\)|`[^`]+`|\*\*[^*]+\*\*|(?<![\w*])\*[^*\s][^*]*\*(?![\w*]))", text):
        if not tok:
            continue
        m = re.fullmatch(r"\[([^\]]+)\]\(([^)]+)\)", tok)
        if m:
            if m[2].startswith("http"):
                link = OxmlElement("w:hyperlink")
                link.set(qn("r:id"), p.part.relate_to(m[2], RT.HYPERLINK, is_external=True))
                r = OxmlElement("w:r")
                rpr = OxmlElement("w:rPr")
                for tag, val in [("color", "000000"), ("u", "single")]:
                    e = OxmlElement("w:" + tag)
                    e.set(qn("w:val"), val)
                    rpr.append(e)
                r.append(rpr)
                t = OxmlElement("w:t")
                t.text = m[1]
                r.append(t)
                link.append(r)
                p._p.append(link)
            else:
                inline(p, m[1], size, base_bold, ital)
        elif tok.startswith("**") and tok.endswith("**"):
            inline(p, tok[2:-2], size, True, ital)
        elif tok.startswith("`") and tok.endswith("`"):
            run(p, tok[1:-1], mono=True, size=(size - 1 if size else 10.5), bold=base_bold, italic=ital)
        elif tok.startswith("*") and tok.endswith("*") and len(tok) > 2:
            inline(p, tok[1:-1], size, base_bold, True)
        else:
            run(p, tok, size=size, bold=base_bold, italic=ital)


def chapter_label(title):
    m = re.match(r"Chương (\d+)", title) or re.match(r"Phụ lục ([A-Z])", title)
    if m:
        state["chap"] = m[1]
        state["fig"] = state["tab"] = 0


def heading(level, title):
    level = max(1, min(level, 3))
    if level == 1:
        chapter_label(title)
    p = doc.add_paragraph(style=f"Heading {level}")
    if level == 1:
        p.paragraph_format.page_break_before = True
    inline(p, title, size={1: 15, 2: 13, 3: 11.5}[level], base_bold=True)
    state["sec_title"] = re.sub(r"`", "", title)
    state["tables_in_sec"] = 0


def para(text, style=None, indent=None, italic=False):
    p = doc.add_paragraph(style=style) if style else doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    if indent is not None:
        p.paragraph_format.left_indent = Cm(indent)
    if italic:
        inline(p, text.strip(), ital=True)
    else:
        inline(p, text)
    return p


def caption(kind, text):
    key = "fig" if kind == "Hình" else "tab"
    state[key] += 1
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.keep_with_next = kind == "Bảng"
    p.paragraph_format.space_before = Pt(6 if kind == "Bảng" else 2)
    run(p, f"{kind} {state['chap']}.{state[key]}. ", bold=True, size=11)
    inline(p, text, size=11)
    return p


def add_picture(rel, cap, base):
    path = (base / rel).resolve()
    if not path.exists():
        raise FileNotFoundError(path)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(str(path), width=Cm(14.5))
    caption("Hình", cap)


def table(lines):
    rows = [[c.strip() for c in l.strip().strip("|").split("|")] for l in lines]
    rows = [r for r in rows if not all(re.fullmatch(r":?-+:?", c) for c in r)]
    n = len(rows[0])
    state["tables_in_sec"] += 1
    title = re.sub(r"^[A-Z]?\d+(\.\d+)*\.?\s+", "", state["sec_title"])
    if state["tables_in_sec"] > 1:
        title += f" (bảng {state['tables_in_sec']})"
    caption("Bảng", title)
    t = doc.add_table(rows=1, cols=n)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    size = 9.5 if n <= 4 else 8.5
    for i, rec in enumerate(rows):
        row = t.rows[0] if i == 0 else t.add_row()
        trpr = row._tr.get_or_add_trPr()
        trpr.append(OxmlElement("w:cantSplit"))
        if i == 0:
            trpr.append(OxmlElement("w:tblHeader"))
        rec = (rec + [""] * n)[:n]
        for cell, val in zip(row.cells, rec):
            cell.width = AVAIL // n
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            props = cell._tc.get_or_add_tcPr()
            borders = OxmlElement("w:tcBorders")
            for edge in ["top", "left", "bottom", "right"]:
                e = OxmlElement("w:" + edge)
                for k, v in [("val", "single"), ("sz", "4"), ("color", "000000")]:
                    e.set(qn("w:" + k), v)
                borders.append(e)
            props.append(borders)
            if i == 0:
                shd = OxmlElement("w:shd")
                shd.set(qn("w:val"), "clear")
                shd.set(qn("w:fill"), "E7E6E6")
                props.append(shd)
            pp = cell.paragraphs[0]
            pp.paragraph_format.space_after = Pt(1)
            pp.paragraph_format.line_spacing = 1.0
            inline(pp, val, size=size, base_bold=(i == 0))
    sp = doc.add_paragraph()
    sp.paragraph_format.space_after = Pt(2)


def join_continuations(lines):
    """Gộp các dòng bị ngắt cứng của cùng một đoạn/mục danh sách/trích dẫn thành một dòng."""
    out, code = [], False
    marker = re.compile(r"^\s*(#|\||```|!\[|<!--|[-*] |\d+\. )")
    for l in lines:
        if l.startswith("```"):
            code = not code
            out.append(l)
            continue
        if code or not out or not l.strip() or not out[-1].strip():
            out.append(l)
            continue
        prev = out[-1]
        if prev.startswith("```") or prev.lstrip().startswith(("#", "|", "![", "<!--")):
            out.append(l)
        elif l.startswith(">") and prev.startswith(">"):
            out[-1] = prev.rstrip() + " " + l.lstrip("> ").strip()
        elif not marker.match(l) and not l.startswith(">") and not prev.startswith(">"):
            out[-1] = prev.rstrip() + " " + l.strip()
        elif not marker.match(l) and prev.startswith(">") is False:
            out[-1] = prev.rstrip() + " " + l.strip()
        else:
            out.append(l)
    return out


def render(lines, base, section_figs=None):
    lines = join_continuations(lines)
    i, code = 0, False
    while i < len(lines):
        line = lines[i]
        s = line.rstrip()
        if s.startswith("```"):
            code = not code
        elif code:
            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.left_indent = Cm(0.5)
            run(p, s, mono=True, size=9)
        elif s.startswith("|"):
            blk = []
            while i < len(lines) and lines[i].startswith("|"):
                blk.append(lines[i])
                i += 1
            table(blk)
            continue
        elif s.startswith("#"):
            lvl = len(s) - len(s.lstrip("#"))
            heading(lvl, s.lstrip("# ").strip())
        elif (m := re.fullmatch(r"!\[([^\]]*)\]\(([^)]+)\)", s.strip())):
            add_picture(m[2], m[1], base)
        elif s.startswith(">"):
            para(s.lstrip("> ").strip(), indent=0.8, italic=True)
        elif re.match(r"^\s*[-*] ", s):
            p = para(re.sub(r"^\s*[-*] ", "", s), style="List Bullet")
        elif re.match(r"^\s*\d+\. ", s):
            para(s.strip(), indent=0.6)
        elif s.strip() == "<!-- page -->":
            doc.add_page_break()
        elif s.strip():
            para(s)
        i += 1


def read(rel):
    p = DOCS / rel
    return p, p.read_text(encoding="utf-8").splitlines()


def shifted(lines, delta):
    out, code = [], False
    for l in lines:
        if l.startswith("```"):
            code = not code
        if not code and l.startswith("#"):
            lvl = len(l) - len(l.lstrip("#"))
            l = "#" * max(1, min(lvl + delta, 3)) + " " + l.lstrip("# ")
        out.append(l)
    return out


def emit_file(rel, delta=0, retitle=None, drop_first_h1=False):
    p, lines = read(rel)
    if retitle is not None:
        for k, l in enumerate(lines):
            if l.startswith("# "):
                lines[k] = "# " + retitle
                break
    elif drop_first_h1:
        k = next(k for k, l in enumerate(lines) if l.startswith("# "))
        lines.pop(k)
    render(shifted(lines, delta), p.parent)


def section_lines(rel, key):
    """Trả về (đường dẫn, mức tiêu đề gốc, tiêu đề gốc, thân) của mục có tiêu đề bắt đầu bằng key."""
    p, lines = read(rel)
    for k, l in enumerate(lines):
        if l.startswith("#") and l.lstrip("# ").startswith(key):
            lvl = len(l) - len(l.lstrip("#"))
            body = []
            for l2 in lines[k + 1:]:
                if l2.startswith("#") and len(l2) - len(l2.lstrip("#")) <= lvl:
                    break
                body.append(l2)
            return p, lvl, l.lstrip("# ").strip(), body
    raise KeyError(f"{rel}: {key}")


def emit_section(rel, key, new_title, level=2, figs=None):
    p, lvl, _, body = section_lines(rel, key)
    render(["#" * level + " " + new_title] + shifted(body, level - lvl), p.parent)
    for cap, fig in figs or []:
        add_picture(f"../{fig}", cap, p.parent)


# ---------------------------------------------------------------- trang bìa
def cover():
    for _ in range(4):
        doc.add_paragraph()
    for text, size, bold in [("ĐỒ ÁN HỌC PHẦN NHẬP MÔN DỮ LIỆU LỚN", 16, True), ("", 12, False),
                             ("LÀM SẠCH, CHUẨN HÓA VÀ TỔNG HỢP DỮ LIỆU HÀNH VI KHÁCH HÀNG THƯƠNG MẠI ĐIỆN TỬ QUY MÔ LỚN BẰNG APACHE SPARK", 20, True),
                             ("", 12, False), ("Pipeline Storage → Processing: landing → raw → clean → agg", 13, False),
                             ("Dữ liệu: Kaggle – eCommerce behavior data from multi category store, 2019-Oct", 13, False)]:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run(p, text, bold=bold, size=size)
    for _ in range(6):
        doc.add_paragraph()
    for text in ["Nhóm thực hiện: TV1 (nhóm trưởng), TV2, TV3, TV4",
                 "Họ tên, MSSV, giảng viên hướng dẫn: [nhóm điền]", "Ngày 22 tháng 11 năm 2026"]:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run(p, text, size=13)


def toc():
    p = doc.add_paragraph()
    p.paragraph_format.page_break_before = True
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run(p, "MỤC LỤC", bold=True, size=16)
    p = doc.add_paragraph()
    r = p.add_run()
    for t, extra in [("begin", None), (None, ' TOC \\o "1-2" \\h \\z \\u '), ("separate", None)]:
        if t:
            fc = OxmlElement("w:fldChar")
            fc.set(qn("w:fldCharType"), t)
            r._r.append(fc)
        else:
            it = OxmlElement("w:instrText")
            it.set(qn("xml:space"), "preserve")
            it.text = extra
            r._r.append(it)
    r.add_text("(Mục lục được cập nhật khi xuất PDF.)")
    fc = OxmlElement("w:fldChar")
    fc.set(qn("w:fldCharType"), "end")
    r._r.append(fc)


def build():
    cover()
    emit_file("tv4/tom_tat.md")
    toc()
    emit_file("tv4/ch01_gioi_thieu.md")

    heading(1, "Chương 2. Cơ sở lý thuyết")
    emit_file("tv2/ch02_1_bigdata.md", delta=1)
    emit_file("tv3/ch02_2_spark.md", delta=1)

    emit_file("tv2/ch03_du_lieu.md")
    emit_file("tv1/ch04_thiet_ke_he_thong.md")
    emit_file("tv3/ch05_trien_khai.md", retitle="Chương 5. Cài đặt và triển khai")

    heading(1, "Chương 6. Thực nghiệm")
    para("Chương này trình bày sáu kịch bản thực nghiệm KB1–KB6 trên dữ liệu Kaggle thật (tầng clean 42.349.872 dòng). "
         "Cụm Spark 1 master + 2 worker chạy bằng Docker trên một máy Windows 11 (20 CPU logic, Docker được cấp khoảng 7,6 GiB RAM). "
         "Mỗi cấu hình chạy 3 lần và lấy trung bình. Các kết luận chỉ áp dụng cho máy, dữ liệu và truy vấn này.")
    T1 = "tv1/ch06_kb1_kb2_kb6.md"
    T2 = "tv2/ch06_kb3_kb5.md"
    emit_section(T1, "6.0", "6.1 Phương pháp chung (KB1, KB2, KB6)")
    emit_section(T1, "6.1", "6.2 KB1 – Ảnh hưởng của kích thước dữ liệu", figs=TV1_FIGS["6.1"])
    emit_section(T1, "6.2", "6.3 KB2 – Ảnh hưởng của số core", figs=TV1_FIGS["6.2"])
    emit_section(T2, "6.1", "6.4 KB3 – CSV và Parquet")
    emit_file("tv4/ch_kpi_kb4.md", drop_first_h1=True)
    emit_section(T2, "6.2", "6.6 KB5 – Chất lượng dữ liệu trước và sau làm sạch")
    emit_section(T1, "6.3", "6.7 KB6 – Ảnh hưởng của `spark.sql.shuffle.partitions`", figs=TV1_FIGS["6.3"])
    emit_section(T1, "6.4", "6.8 Tổng hợp và giới hạn của KB1, KB2, KB6")

    emit_file("tv4/ch07_ket_qua_demo.md")

    heading(1, "Chương 8. Thảo luận và bài học")
    K1 = "tv4/ch08_bai_hoc_tv1_tv4.md"
    emit_section(K1, "8.A", "8.1 Bài học từ hạ tầng và benchmark (TV1)")
    heading(2, "8.2 Bài học từ dữ liệu và làm sạch (TV2)")
    for n in range(1, 6):
        p, lvl, title, body = section_lines("tv2/ch08_bai_hoc_ai.md", f"8.{n}.")
        render(["### " + f"8.2.{n} " + re.sub(r"^8\.\d+\.\s*", "", title)] + shifted(body, 3 - lvl), p.parent)
    heading(2, "8.3 Bài học từ triển khai (TV3)")
    emit_section("tv3/ch08_bai_hoc_ai.md", "Bài học từ triển khai", "8.3.1 Bài học từ triển khai", 3)
    emit_section("tv3/ch08_bai_hoc_ai.md", "Hạn chế và hướng hoàn thiện", "8.3.2 Hạn chế và hướng hoàn thiện", 3)
    emit_section(K1, "8.B", "8.4 Bài học từ KPI và KB4 (TV4)")
    emit_section(K1, "8.C", "8.5 Tổng hợp thảo luận chung")

    emit_file("tv4/ch09_ket_luan.md")

    emit_file("tv2/phu_luc_schema.md")
    emit_file("tv3/phu_luc_chay_windows.md", retitle="Phụ lục B. Hướng dẫn chạy pipeline trên Windows")
    heading(1, "Phụ lục C. Phân công và mức độ đóng góp")
    render(["Bảng phân công và tỷ lệ đóng góp do nhóm xác nhận; các ô trống chưa được điền.", "",
            "| Thành viên | Vai trò | Báo cáo | Thực nghiệm | Tỷ lệ đóng góp |",
            "|---|---|---|---|---|",
            "| TV1 | Nhóm trưởng; hạ tầng Docker/Spark, ingest | Ch.4, Ch.6 (KB1, KB2, KB6) | KB1, KB2, KB6 | [điền] |",
            "| TV2 | Data contract, profiling, samples | Ch.2.1, Ch.3, Ch.6 (KB3, KB5) | KB3, KB5 | [điền] |",
            "| TV3 | Cleaning, pipeline, kiểm thử | Ch.2.2, Ch.5, Phụ lục B | – | [điền] |",
            "| TV4 | Aggregation, KPI, biểu đồ, ghép báo cáo | Tóm tắt, Ch.1, Ch.6 (KB4), Ch.7, Ch.8, Ch.9 | KB4 | [điền] |",
            "", "Họ tên và MSSV từng thành viên: [nhóm điền]."], DOCS)
    heading(1, "Phụ lục D. Ghi chú sử dụng AI")
    emit_section("tv2/ch08_bai_hoc_ai.md", "8.6", "D.1 Phần TV2", 2)
    emit_section("tv3/ch08_bai_hoc_ai.md", "Ghi chú sử dụng AI", "D.2 Phần TV3", 2)
    emit_section(K1, "8.D", "D.3 Phần TV4", 2)
    render(["## D.4 Phần TV1", "", "[TV1 điền: công cụ AI đã dùng, mục đích, phần đã tự kiểm tra. Theo hướng dẫn đồ án, ai dùng AI phải ghi lại ở đây; "
            "phần này chưa có nội dung vì TV4 không biết TV1 đã dùng AI hay không.]"], DOCS)
    emit_file("tv3/nguon_chinh_thuc.md", retitle="Phụ lục E. Tài liệu tham khảo")

    f = sec.footer.paragraphs[0]
    f.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = f.add_run()
    for t, extra in [("begin", None), (None, " PAGE "), ("end", None)]:
        if t:
            fc = OxmlElement("w:fldChar")
            fc.set(qn("w:fldCharType"), t)
            r._r.append(fc)
        else:
            it = OxmlElement("w:instrText")
            it.set(qn("xml:space"), "preserve")
            it.text = extra
            r._r.append(it)
    doc.core_properties.title = "Báo cáo đồ án Nhập môn Dữ liệu lớn"
    doc.core_properties.author = "Nhóm TV1-TV4"
    doc.save(OUTPUT)
    print(OUTPUT, "tables:", state["tab"], "figs:", state["fig"])


build()
