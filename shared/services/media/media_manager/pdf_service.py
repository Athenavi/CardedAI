"""
PDF 文件处理服务
提供 PDF 上传、预览生成和元数据提取功能
"""
from typing import Dict, Any

# PDF 配置常量
ALLOWED_PDF_MIME_TYPES = {'application/pdf'}
MAX_PDF_FILE_SIZE = 50 * 1024 * 1024  # 50MB
DEFAULT_EMBED_WIDTH = "100%"
DEFAULT_EMBED_HEIGHT = "600px"
MAX_TEXT_EXTRACT_PAGES = 10


class PDFService:
    """PDF 文件处理服务"""
    
    # 允许的 MIME 类型
    ALLOWED_MIME_TYPES = {
        'application/pdf',
    }
    
    # 最大文件大小 (50MB)
    MAX_FILE_SIZE = 50 * 1024 * 1024
    
    @classmethod
    def validate_upload(cls, file_obj) -> tuple[bool, str]:
        """验证上传的 PDF 文件"""
        content_type = file_obj.content_type
        if content_type not in ALLOWED_PDF_MIME_TYPES:
            return False, f"不支持的文件类型: {content_type}。只允许 PDF 文件"

        if file_obj.size > MAX_PDF_FILE_SIZE:
            return False, f"文件大小超过限制 ({MAX_PDF_FILE_SIZE / 1024 / 1024:.0f}MB)"
        
        return True, "验证通过"
    
    @classmethod
    def extract_metadata(cls, pdf_path: str) -> Dict[str, Any]:
        """提取 PDF 元数据"""
        metadata = {
            'page_count': 0, 'title': None, 'author': None, 'subject': None,
            'creator': None, 'producer': None, 'creation_date': None, 'modification_date': None,
        }
        
        try:
            # 尝试使用 PyPDF2
            try:
                import PyPDF2
                with open(pdf_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    metadata['page_count'] = len(reader.pages)
                    if reader.metadata:
                        info = reader.metadata
                        metadata.update({
                            'title': info.get('/Title'), 'author': info.get('/Author'),
                            'subject': info.get('/Subject'), 'creator': info.get('/Creator'),
                            'producer': info.get('/Producer'),
                            'creation_date': str(info.get('/CreationDate', '')),
                            'modification_date': str(info.get('/ModDate', ''))
                        })
                return metadata
            except ImportError:
                pass
            
            # 尝试使用 pdfplumber
            try:
                import pdfplumber
                with pdfplumber.open(pdf_path) as pdf:
                    metadata['page_count'] = len(pdf.pages)
                    if pdf.metadata:
                        meta = pdf.metadata
                        metadata.update({
                            'title': meta.get('Title'), 'author': meta.get('Author'),
                            'subject': meta.get('Subject'), 'creator': meta.get('Creator'),
                            'producer': meta.get('Producer')
                        })
                return metadata
            except ImportError:
                pass

            metadata['page_count'] = -1
            return metadata
        except Exception as e:
            metadata['error'] = str(e)
            return metadata
    
    @classmethod
    def generate_thumbnail(cls, pdf_path: str, output_path: str, page_number: int = 0) -> bool:
        """生成 PDF 封面缩略图（第一页）"""
        try:
            try:
                from pdf2image import convert_from_path
                images = convert_from_path(pdf_path, first_page=page_number + 1, last_page=page_number + 1)
                if images:
                    images[0].save(output_path, 'JPEG', quality=85)
                    return True
            except ImportError:
                pass
            
            try:
                import fitz
                doc = fitz.open(pdf_path)
                page = doc.load_page(page_number)
                pix = page.get_pixmap()
                pix.save(output_path)
                doc.close()
                return True
            except ImportError:
                pass
            
            return False
        except Exception:
            return False
    
    @classmethod
    def get_embed_code(cls, pdf_url: str, width: str = DEFAULT_EMBED_WIDTH, height: str = DEFAULT_EMBED_HEIGHT) -> str:
        """生成 PDF 嵌入代码"""
        return f'<iframe src="{pdf_url}" width="{width}" height="{height}" style="border: none;" frameborder="0"><p>您的浏览器不支持 PDF 预览。<a href="{pdf_url}">点击下载 PDF</a></p></iframe>'.strip()
    
    @classmethod
    def extract_text(cls, pdf_path: str, max_pages: int = MAX_TEXT_EXTRACT_PAGES) -> str:
        """提取 PDF 文本内容（用于搜索）"""
        text_content = []
        
        try:
            try:
                import PyPDF2
                with open(pdf_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    for i, page in enumerate(reader.pages):
                        if i >= max_pages:
                            break
                        text = page.extract_text()
                        if text:
                            text_content.append(text)
                return '\n'.join(text_content)
            except ImportError:
                pass
            
            try:
                import pdfplumber
                with pdfplumber.open(pdf_path) as pdf:
                    for i, page in enumerate(pdf.pages):
                        if i >= max_pages:
                            break
                        text = page.extract_text()
                        if text:
                            text_content.append(text)
                return '\n'.join(text_content)
            except ImportError:
                pass
            
            return ''
        except Exception:
            return ''
