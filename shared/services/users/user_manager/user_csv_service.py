"""
用户CSV导入/导出服务
"""
import csv
import io
import re
from datetime import datetime
from typing import List, Dict, Any, Optional

# 常量定义
EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
DEFAULT_FIELDS = [
    'id', 'username', 'email', 'first_name', 'last_name',
    'role', 'is_active', 'date_joined', 'last_login'
]
DEFAULT_COLUMN_MAPPING = {
    'username': 'username',
    'email': 'email',
    'password': 'password',
    'first_name': 'first_name',
    'last_name': 'last_name',
    'role': 'role',
}


class UserCSVService:
    """用户CSV导入/导出服务"""
    
    def __init__(self):
        self.default_fields = DEFAULT_FIELDS
    
    def export_users_to_csv(
        self,
        users: List[Dict[str, Any]],
        fields: Optional[List[str]] = None,
        encoding: str = 'utf-8-sig'  # UTF-8 with BOM for Excel
    ) -> str:
        """
        导出用户列表为CSV格式
        
        Args:
            users: 用户数据列表
            fields: 要导出的字段,默认全部
            encoding: 编码格式
            
        Returns:
            CSV字符串
        """
        if not fields:
            fields = self.default_fields
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fields, extrasaction='ignore')
        
        # 写入表头
        writer.writeheader()
        
        # 写入数据
        for user in users:
            row = {}
            for field in fields:
                value = user.get(field, '')
                
                # 处理布尔值
                if isinstance(value, bool):
                    value = 'Yes' if value else 'No'
                # 处理日期时间
                elif isinstance(value, datetime):
                    value = value.strftime('%Y-%m-%d %H:%M:%S')
                # 处理None
                elif value is None:
                    value = ''
                
                row[field] = value
            
            writer.writerow(row)
        
        return output.getvalue()
    
    def parse_csv_import(
        self,
        csv_content: str,
        column_mapping: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        解析CSV导入文件
        
        Args:
            csv_content: CSV内容
            column_mapping: 列映射 {csv_column: db_field}
            
        Returns:
            解析结果 {'users': [...], 'errors': [...]}
        """
        users = []
        errors = []
        
        try:
            csv_file = io.StringIO(csv_content)
            reader = csv.DictReader(csv_file)

            # 使用默认映射或自定义映射
            mapping = column_mapping or DEFAULT_COLUMN_MAPPING
            
            # 验证必需的列
            required_columns = ['username', 'email']
            for col in required_columns:
                if col not in reader.fieldnames and col not in mapping.values():
                    errors.append(f"缺少必需列: {col}")
                    return {'users': [], 'errors': errors}
            
            # 解析每一行
            for row_num, row in enumerate(reader, start=2):
                try:
                    user_data = {}
                    
                    # 应用列映射
                    for csv_col, db_field in mapping.items():
                        if csv_col in row:
                            user_data[db_field] = row[csv_col].strip()
                    
                    # 验证必填字段
                    if not user_data.get('username'):
                        errors.append(f"第{row_num}行: 用户名为空")
                        continue
                    
                    if not user_data.get('email'):
                        errors.append(f"第{row_num}行: 邮箱为空")
                        continue
                    
                    # 验证邮箱格式
                    if not EMAIL_PATTERN.match(user_data['email']):
                        errors.append(f"第{row_num}行: 邮箱格式不正确 - {user_data['email']}")
                        continue
                    
                    # 设置默认值
                    user_data.setdefault('role', 'subscriber')
                    user_data.setdefault('is_active', True)
                    
                    users.append(user_data)
                    
                except Exception as e:
                    errors.append(f"第{row_num}行: 解析错误 - {str(e)}")
            
            return {
                'users': users,
                'errors': errors,
                'total_rows': len(users) + len(errors),
                'valid_count': len(users),
                'error_count': len(errors)
            }
            
        except Exception as e:
            errors.append(f"CSV解析失败: {str(e)}")
            return {'users': [], 'errors': errors}
    
    def generate_sample_csv(self) -> str:
        """生成示例CSV文件 - 最小化模板"""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # 表头 - 只包含必需和最常用的字段
        writer.writerow(['username', 'email', 'password', 'roles', 'bio'])
        
        # 示例数据 - 展示不同场景
        writer.writerow(['zhangsan', 'zhangsan@example.com', '123456', '管理员', '这是一个测试用户'])
        writer.writerow(['lisi', 'lisi@example.com', '123456', '', ''])  # 无角色，无简介
        writer.writerow(['wangwu', 'wangwu@example.com', '123456', '编辑,VIP用户', '多个角色用逗号分隔'])
        
        return output.getvalue()


# 单例实例
user_csv_service = UserCSVService()
