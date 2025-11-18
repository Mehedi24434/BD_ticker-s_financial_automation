import io
import re
import fitz  # PyMuPDF
from PIL import Image
import pytesseract
from pytesseract import image_to_osd

# -----------------------------
# Dictionaries
# -----------------------------
# Define P&L terms
pnl_terms = [
    "sales", "turnover", "revenue", "total revenue", "net revenue", "gross revenue",
    "cost of sales", "cost of goods sold", "cogs", "direct costs",
    "gross profit", "gross margin",  "consolidated",
    "operating expenses", "opex", "selling expenses", "general and administrative expenses", "oﬃce and administrative expenses",
    "sg&a", "research and development", "r&d", "depreciation", "amortization", "marketing and distribution expenses", "profit from operation"
    "operating profit", "operating income", "ebit", "earnings before interest and tax", "financial expenses",
    "other income", "other expenses", "non-operating income", "non-operating expenses", "non operating income",
    "finance income", "finance cost", "interest income", "interest expense", "proﬁt/(loss) before tax & wppf", "contribution to wppf and welfare fund",
    "profit before tax", "earnings before tax", "ebt", "net proﬁt before tax", "income tax expense", "net proﬁt/loss after tax",
    "income tax", "tax expense", "current tax", "deferred tax", "for the period from", "Consolidated Statement", 
    "net profit", "net income", "profit after tax", "earnings",
    "profit attributable to shareholders", "minority interest",
    "earnings per share", "eps", "diluted eps", "basic eps",
    "ebitda", "earnings before interest tax depreciation amortization", "Profit or",
    "Loss and",
    "Comprehensive income",
    "Consolidated account",
    "Consolidated income",
    "Statement of",
    "Other comprehensive",
    "Operating expenses",
    "Revenue expenses",
    "Earnings operations",
    "Statement of profit",
    "Profit or loss",
    "Other comprehensive income",
    "Consolidated profit or",
    "Profit and loss",
    "Earnings and expenses",
    "Statement of earnings",
    "Revenue and expenses"
]

# Header words (split into individual words)
pnl_header_words = [
    "statement", "of", "profit", "or", "loss",
    "and", "other", "comprehensive", "income",
    "consolidated", "account", "earnings", "operations",
    "revenue", "expenses"
]


# Precompile simple regexes for header words (word boundaries)
_header_word_rx = [re.compile(rf"\b{re.escape(w)}\b") for w in pnl_header_words]
# Precompile term regexes (case-insensitive, phrase allowed)
_term_rx = [re.compile(re.escape(t), re.IGNORECASE) for t in pnl_terms]


# -----------------------------
# Helpers
# -----------------------------

def detect_orientation(page, dpi=144):
    """Detect orientation of a PDF page using Tesseract OSD."""
    mat = fitz.Matrix(dpi/72, dpi/72)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    img_bytes = pix.tobytes("png")
    img = Image.open(io.BytesIO(img_bytes))
    osd = image_to_osd(img)
    for line in osd.splitlines():
        if line.startswith("Rotate:"):
            return int(line.split(":")[1].strip())
    return 0


def check_rotated_page(doc):
    """Return a new PDF with all pages normalized using OCR orientation detection."""
    new_doc = fitz.open()

    for page_number, page in enumerate(doc, start=1):
        angle = detect_orientation(page)
        # print(f"Page {page_number}: detected rotation = {angle}°")

        rect = page.rect
        new_page = new_doc.new_page(width=rect.width, height=rect.height)

        if angle in (90, 270, 180):
            print(f" -> Normalizing Page {page_number}")
            new_page.show_pdf_page(rect, doc, page_number - 1, rotate=-90)
        else:
            new_page.show_pdf_page(rect, doc, page_number - 1)

    return new_doc

def _page_text_plain(doc, idx: int) -> str:
    """Machine-readable text via PyMuPDF; returns lowercase text (may be empty)."""
    page = doc.load_page(idx)
    txt = page.get_text("text") or ""
    return txt.lower()

def _page_text_ocr(doc, idx: int, dpi: int = 144) -> str:
    """OCR just one page: render to image, run Tesseract; returns lowercase."""
    page = doc.load_page(idx)
    mat = fitz.Matrix(dpi/72, dpi/72)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    img_bytes = pix.tobytes("png")
    image = Image.open(io.BytesIO(img_bytes))
    txt = pytesseract.image_to_string(image) or ""
    return txt.lower()
    
def _page_upper_half_ocr(doc, idx: int, dpi: int = 360, lang: str = "eng",
                         tesseract_cfg: str = "--oem 3 --psm 6") -> str:
    """
    OCR the UPPER half of a page.
    Renders at high DPI, OCRs the cropped region, and returns text (lowercased).
    """
    page = doc.load_page(idx)
    r = page.rect

    # Upper half rectangle
    mid_y = r.y0 + (r.height / 2.0)
    upper_half = fitz.Rect(r.x0, r.y0, r.x1, mid_y)

    # Scale for higher DPI OCR
    mat = fitz.Matrix(dpi / 72.0, dpi / 72.0)

    # Render cropped region
    pix = page.get_pixmap(matrix=mat, clip=upper_half, alpha=False)
    img = Image.open(io.BytesIO(pix.tobytes("png"))).convert("L")  # grayscale
    
    # OCR
    text = pytesseract.image_to_string(img, lang=lang, config=tesseract_cfg) or ""
    return text.lower()
    
def _page_left_half_text_ocr(doc, idx: int, dpi: int = 360, lang: str = "eng",
                        tesseract_cfg: str = "--oem 3 --psm 6") -> str:
    """
    OCR the LEFT half of a page by splitting it into UPPER-LEFT and LOWER-LEFT regions.
    Renders each region at high DPI, OCRs them separately, and concatenates the text.
    """
    page = doc.load_page(idx)
    r = page.rect

    # Compute left-half bounds robustly using rect.x0/x1 (not assuming origin=0)
    mid_x = r.x0 + (r.width / 2.0)
    mid_y = r.y0 + (r.height / 2.0)

    # Left-half only
    left_upper = fitz.Rect(r.x0, r.y0, mid_x, mid_y)
    left_lower = fitz.Rect(r.x0, mid_y, mid_x, r.y1)

    # Scale for higher DPI OCR
    mat = fitz.Matrix(dpi / 72.0, dpi / 72.0)

    def ocr_region(clip_rect):
        pix = page.get_pixmap(matrix=mat, clip=clip_rect, alpha=False)
        img = Image.open(io.BytesIO(pix.tobytes("png"))).convert("L")  # grayscale helps OCR
        # Optional light binarization (uncomment if needed):
        # img = img.point(lambda x: 0 if x < 200 else 255, mode="1")
        text = pytesseract.image_to_string(img, lang=lang, config=tesseract_cfg) or ""
        return text.lower()

    txt_upper = ocr_region(left_upper)
    txt_lower = ocr_region(left_lower)

    return txt_upper + "\n" + txt_lower

def _score_header_words(text: str) -> int:
    """+1 per header word present at least once."""
    score = 0
    for rx in _header_word_rx:
        if rx.search(text):
            score += 1
    return score

def _score_terms(text: str) -> int:
    """+1 per term present at least once (phrase-aware)."""
    score = 0
    for rx in _term_rx:
        if rx.search(text):
            score += 1
    return score


# -----------------------------
# Main (chunked) pipeline
# -----------------------------
def find_best_pnl_page_chunked(
    pdf_path: str,
    header_top_k: int = 20,
    chunk_size: int = 100,
    ocr_threshold_chars: int = 40,
    rotation_option = False
):
    """
    Stage A (header ranking): scan the whole PDF in chunks of `chunk_size` pages,
    using ONLY text extraction (no OCR). Compute header-word scores per page and
    keep the global Top-K pages.

    Stage B (term ranking): for those Top-K pages, if plain text is too short,
    OCR ONLY those pages; then compute term scores and return the best page.
    """
    if rotation_option:
        doc1 = fitz.open(pdf_path)
        doc = check_rotated_page(doc1)
    else:
        doc = fitz.open(pdf_path)
    n_pages = len(doc)

    # If file is small, just use one chunk
    if n_pages <= 300:
        chunk_size = n_pages

    header_scores = []  # list of (page_num, header_score)

    # --- Stage A: header scoring in chunks (no OCR) ---
    for start in range(0, n_pages, chunk_size):
        end = min(start + chunk_size, n_pages)
        for idx in range(start, end):
            text = _page_text_plain(doc, idx)
            # Fallback: if too little plain text, OCR the upper half instead
            if len(text.strip()) < 100:
                text = _page_upper_half_ocr(doc, idx)
                

            hs = _score_header_words(text)
            header_scores.append((idx + 1, hs))  # 1-based page nums

    # Pick global Top-K by header score (stable order: earlier pages first on ties)
    header_scores.sort(key=lambda x: x[1], reverse=True)
    top_k = header_scores[:header_top_k] if header_scores else []

    if not top_k:
        doc.close()
        raise ValueError("No pages found or header scoring produced empty results.")

    # --- Stage B: among Top-K, compute term scores (OCR only if text too short) ---
    term_scores = []
    for page_num, _ in top_k:
        idx = page_num - 1
        text = _page_text_plain(doc, idx)
        if len(text.strip()) < ocr_threshold_chars:
            text = _page_text_ocr(doc, idx)  # targeted OCR
        ts = _score_terms(text)
        if ts < 3:
            text = _page_left_half_text_ocr(doc, idx)
            ts = _score_terms(text)
        term_scores.append((page_num, ts))

    doc.close()

    # Pick the best by term score; tie-breaker: lowest page number
    best_page, best_term_score = max(term_scores, key=lambda x: (x[1], -x[0]))

    # ---- Reporting ----
    print("Top pages by header score (page → header_score):")
    for p, hs in top_k:
        print(f"  Page {p} → {hs}")

    print("\nTerm scores among header Top-K (page → term_score):")
    for p, ts in term_scores:
        print(f"  Page {p} → {ts}")

    print(f"\n✅ Most likely P&L page: Page {best_page} (term score: {best_term_score})")
    return best_page






def save_best_pnl_page_as_searchable_pdf(pdf_path: str, output_path: str, rotation_option=False, dpi: int = 300, lang: str = "eng"):
    """
    Detect the most likely P&L page, OCR it if needed, and save as a searchable PDF.
    """
    import pytesseract

    # Step 1: Detect best page
    best_page = find_best_pnl_page_chunked(
        pdf_path,
        header_top_k=20,
        chunk_size=100,
        ocr_threshold_chars=40,
        rotation_option=rotation_option
    )

    # Step 2: Open PDF
    doc = fitz.open(pdf_path)
    if rotation_option:
        doc = check_rotated_page(doc)

    # Step 3: Render the page to high-resolution image
    page = doc[best_page - 1]
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

    # Step 4: OCR the page to get text
    ocr_text = pytesseract.image_to_pdf_or_hocr(img, extension='pdf', lang=lang)

    # Step 5: Save OCR result as searchable PDF
    with open(output_path, "wb") as f:
        f.write(ocr_text)

    doc.close()
    print(f"✅ P&L page saved as high-quality searchable PDF: {output_path}")
    return output_path



