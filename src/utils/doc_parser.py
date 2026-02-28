import os


def extract_text(file_path: str) -> str:
    """
    从 .pdf / .docx / .doc 文件中提取纯文本。
    返回提取到的字符串，失败时抛出异常。
    """
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        return _extract_pdf(file_path)
    elif ext == ".docx":
        return _extract_docx(file_path)
    elif ext == ".doc":
        return _extract_doc(file_path)
    elif ext == ".txt":
        return _extract_txt(file_path)
    else:
        raise ValueError(f"不支持的文件格式：{ext}，仅支持 .pdf / .docx / .doc / .txt")


def _extract_pdf(path: str) -> str:
    try:
        import pdfplumber
    except ImportError:
        raise ImportError("解析 PDF 需要安装 pdfplumber：pip install pdfplumber")

    texts = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                texts.append(t)
    return "\n".join(texts)


def _extract_docx(path: str) -> str:
    try:
        from docx import Document
    except ImportError:
        raise ImportError("解析 .docx 需要安装 python-docx：pip install python-docx")

    doc = Document(path)
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def _extract_txt(path: str) -> str:
    with open(path, encoding="utf-8", errors="ignore") as f:
        return f.read()


def _extract_doc(path: str) -> str:
    """
    .doc 格式优先尝试 textract，不可用时回退到 antiword（需系统安装）。
    """
    try:
        import textract
        return textract.process(path).decode("utf-8", errors="ignore")
    except ImportError:
        pass

    import subprocess
    try:
        result = subprocess.run(
            ["antiword", path],
            capture_output=True, text=True, check=True
        )
        return result.stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        raise RuntimeError(
            "解析 .doc 失败：请安装 textract（pip install textract）"
            " 或系统工具 antiword"
        )
