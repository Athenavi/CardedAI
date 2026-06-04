"""
存储相关的工具函数
"""
from decimal import Decimal

from src.utils.storage.s3_storage import s3_storage


def convert_storage_size(total_bytes):
    """
    将字节数转换为GB、MB或KB的字符串表示。

    :param total_bytes: 存储大小的字节数
    :return: 存储大小的字符串表示，单位为GB、MB或KB
    """
    gb_factor = Decimal('1073741824')  # 1024 * 1024 * 1024
    mb_factor = Decimal('1048576')  # 1024 * 1024
    kb_factor = Decimal('1024')  # 1024

    # 统一转换为 Decimal
    total_bytes = Decimal(str(total_bytes))

    if total_bytes >= gb_factor:
        size_in_gb = total_bytes / gb_factor
        return f"{int(size_in_gb)} GB"
    elif total_bytes >= mb_factor:
        size_in_mb = total_bytes / mb_factor
        return f"{int(size_in_mb)} MB"
    else:
        size_in_kb = total_bytes / kb_factor
        return f"{int(size_in_kb)} KB"


def async_file_cleanup(db_session, cleanup_data):
    """后台线程执行的清理任务"""
    try:
        for file_info in cleanup_data:
            storage_path = file_info['storage_path']
            # 只进行文件清理，不在后台进行数据库操作
            try:
                if storage_path.startswith('s3://'):
                    # 从S3删除文件
                    success = s3_storage.delete_file(storage_path)
                    if success:
                        print(f"成功从S3删除文件: {storage_path}")
                    else:
                        print(f"从S3删除文件失败: {storage_path}")

            except Exception as e:
                print(f"文件删除失败: {storage_path} - {str(e)}")

    except Exception as e:
        print(f"后台清理任务失败: {str(e)}")
