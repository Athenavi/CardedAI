"""
API响应模型
"""
import json
import datetime
import decimal
from typing import Any, Optional

from fastapi.responses import JSONResponse
from pydantic import BaseModel, model_validator


class PaginationInfo(BaseModel):
    """
    分页信息模型
    """
    current_page: int
    per_page: int
    total: int
    total_pages: int
    has_next: bool
    has_prev: bool


class ApiResponse(BaseModel):
    """
    API通用响应模型

    success (bool): 请求是否成功
    data (Optional[Any]): 成功时返回的数据
    message (Optional[str]): 成功时返回的消息
    error (Optional[str]): 失败时返回的错误信息
    pagination (Optional[PaginationInfo]): 分页信息
    """
    success: bool
    data: Optional[Any] = None
    message: Optional[str] = None
    error: Optional[str] = None
    pagination: Optional[PaginationInfo] = None

    # ------------------------------------------------------------------
    # 序列化安全网：递归清理 data 中的不可序列化类型
    # ------------------------------------------------------------------

    @staticmethod
    def _make_serializable(obj: Any) -> Any:
        """递归转换不可序列化的类型为安全的 JSON 表示。"""
        if obj is None or isinstance(obj, (bool, int, float, str)):
            return obj
        if isinstance(obj, (datetime.datetime, datetime.date, datetime.time)):
            return obj.isoformat()
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        if isinstance(obj, (bytes, bytearray)):
            try:
                return obj.decode('utf-8')
            except (UnicodeDecodeError, AttributeError):
                return str(obj)
        if isinstance(obj, dict):
            return {str(k): ApiResponse._make_serializable(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [ApiResponse._make_serializable(item) for item in obj]
        if isinstance(obj, set):
            return [ApiResponse._make_serializable(item) for item in sorted(obj, key=str)]
        if callable(obj):
            return str(obj)
        if isinstance(obj, BaseModel):
            try:
                return obj.model_dump(mode='json')
            except Exception:
                return str(obj)
        try:
            json.dumps(obj)
            return obj
        except (TypeError, ValueError):
            return str(obj)

    @model_validator(mode='after')
    def _sanitize_data_field(self):
        """在模型构建后清理 data 字段，确保所有值都是 JSON 可序列化的。"""
        if self.data is not None:
            self.data = self._make_serializable(self.data)
        return self

    # ------------------------------------------------------------------
    # 工厂方法
    #
    # 注意：方法名不能与 Pydantic 字段名相同（success / error），
    # 否则 classmethod 作为 data descriptor 会遮蔽字段值，
    # 导致 Pydantic v2 序列化时出现
    # "Unable to serialize unknown type: <class 'method'>"
    # ------------------------------------------------------------------

    @classmethod
    def ok(
        cls,
        data: Any = None,
        message: Optional[str] = None,
        pagination: Optional[PaginationInfo] = None,
    ) -> "ApiResponse":
        """创建成功响应"""
        return cls(success=True, data=data, message=message, pagination=pagination)

    @classmethod
    def fail(
        cls,
        message: str,
        code: int = 400,
        data: Any = None,
    ) -> JSONResponse:
        """创建错误响应（带 HTTP 状态码）"""
        return JSONResponse(
            content=cls(success=False, error=message, data=data).model_dump(mode='json'),
            status_code=code if code >= 400 else 400,
        )

    # 保留旧名称别名以兼容现有代码
    success_response = ok
    error_response = fail
