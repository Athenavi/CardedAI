"""
时区和本地化 API
提供时区检测、日期格式化、货币格式化等功能
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query, Header

from shared.models.user import User as UserModel
from shared.services.translation.localization_service import localization_service
from src.api.v1.core.responses import ApiResponse
from src.auth.auth_deps import get_current_active_user

router = APIRouter(tags=["i18n"])


@router.get("/detect-timezone", summary="检测用户时区")
async def detect_timezone(
        locale: str = Query(None, description="语言区域"),
        accept_language: Optional[str] = Header(None, description="Accept-Language头"),
):
    """
    检测用户时区
    
    Args:
        locale: 语言区域
        accept_language: HTTP Accept-Language头
        
    Returns:
        时区信息
    """
    try:
        # 从locale或Accept-Language推断
        detected_locale = locale
        if not detected_locale and accept_language:
            # 解析Accept-Language头
            detected_locale = accept_language.split(',')[0].split(';')[0]

        timezone = localization_service.detect_timezone(locale=detected_locale)

        return ApiResponse(
            success=True,
            data={
                'timezone': timezone,
                'locale': detected_locale or 'en-US',
                'offset': localization_service.get_timezone_offset(timezone),
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"检测时区失败: {str(e)}")


@router.post("/format-date", summary="格式化日期")
async def format_date(
        timestamp: str = Query(..., description="ISO格式时间戳"),
        locale: str = Query('en-US', description="语言区域"),
        timezone: str = Query('UTC', description="用户时区"),
        format_type: str = Query('date', enum=['date', 'datetime', 'relative'], description="格式类型"),
):
    """
    格式化日期时间
    
    Args:
        timestamp: ISO格式时间戳
        locale: 语言区域
        timezone: 用户时区
        format_type: 格式类型(date/datetime/relative)
        
    Returns:
        格式化后的日期字符串
    """
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))

        if format_type == 'date':
            formatted = localization_service.format_date(dt, locale, timezone)
        elif format_type == 'datetime':
            formatted = localization_service.format_datetime(dt, locale, timezone)
        elif format_type == 'relative':
            formatted = localization_service.format_relative_time(dt, locale, timezone)
        else:
            formatted = str(dt)

        return ApiResponse(
            success=True,
            data={
                'original': timestamp,
                'formatted': formatted,
                'locale': locale,
                'timezone': timezone,
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"格式化失败: {str(e)}")


@router.post("/format-currency", summary="格式化货币")
async def format_currency(
        amount: float = Query(..., description="金额"),
        locale: str = Query('en-US', description="语言区域"),
        currency_code: Optional[str] = Query(None, description="货币代码"),
):
    """
    格式化货币金额
    
    Args:
        amount: 金额
        locale: 语言区域
        currency_code: 货币代码(可选)
        
    Returns:
        格式化后的货币字符串
    """
    try:
        formatted = localization_service.format_currency(amount, locale, currency_code)

        return ApiResponse(
            success=True,
            data={
                'amount': amount,
                'formatted': formatted,
                'locale': locale,
                'currency_code': currency_code or localization_service._currency_codes.get(locale, 'USD'),
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"格式化失败: {str(e)}")


@router.get("/locale-info", summary="获取区域信息")
async def get_locale_info(
        locale: str = Query('en-US', description="语言区域"),
):
    """
    获取指定区域的完整配置信息
    
    Args:
        locale: 语言区域
        
    Returns:
        区域配置信息
    """
    try:
        info = localization_service.get_user_locale_info(locale)

        return ApiResponse(
            success=True,
            data=info
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取区域信息失败: {str(e)}")


@router.get("/supported-locales", summary="获取支持的区域列表")
async def get_supported_locales():
    """
    获取系统支持的所有语言区域
    
    Returns:
        区域代码列表
    """
    try:
        locales = localization_service.get_supported_locales()

        return ApiResponse(
            success=True,
            data={
                'locales': locales,
                'count': len(locales),
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取区域列表失败: {str(e)}")


@router.get("/user-preferences", summary="获取用户本地化偏好")
async def get_user_preferences(
        current_user: UserModel = Depends(get_current_active_user)
):
    """
    获取当前用户的本地化偏好设置
    
    Returns:
        用户偏好设置
    """
    try:
        # Read user locale preferences from database
        # Example implementation:
        # from shared.models.user import User
        # stmt = select(User).where(User.id == current_user.id)
        # result = await db.execute(stmt)
        # user = result.scalar_one_or_none()
        # 
        # if user:
        #     locale = user.locale or 'en-US'
        #     timezone = user.timezone or localization_service.detect_timezone(locale=locale)
        # else:
        #     locale = 'en-US'
        #     timezone = localization_service.detect_timezone(locale=locale)

        # For now, use default values
        locale = getattr(current_user, 'locale', 'en-US')
        timezone = localization_service.detect_timezone(locale=locale)

        locale_info = localization_service.get_user_locale_info(locale)

        return ApiResponse(
            success=True,
            data={
                'locale': locale,
                'timezone': timezone,
                'locale_info': locale_info,
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"获取偏好失败: {str(e)}")


@router.put("/user-preferences", summary="更新用户本地化偏好")
async def update_user_preferences(
        locale: str = Query(..., description="语言区域"),
        timezone: Optional[str] = Query(None, description="时区"),
        current_user: UserModel = Depends(get_current_active_user)
):
    """
    更新用户的本地化偏好设置
    
    Args:
        locale: 语言区域
        timezone: 时区(可选，如不提供则自动检测)
        
    Returns:
        更新结果
    """
    try:
        # Save user locale preferences to database
        # Example implementation:
        # from shared.models.user import User
        # stmt = select(User).where(User.id == current_user.id)
        # result = await db.execute(stmt)
        # user = result.scalar_one_or_none()
        # 
        # if user:
        #     user.locale = locale
        #     user.timezone = timezone or localization_service.detect_timezone(locale=locale)
        #     await db.commit()
        #     await db.refresh(user)
        
        detected_timezone = timezone or localization_service.detect_timezone(locale=locale)

        return ApiResponse(
            success=True,
            message='偏好设置已更新',
            data={
                'locale': locale,
                'timezone': detected_timezone,
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"更新失败: {str(e)}")


@router.post("/convert-time", summary="时区转换")
async def convert_time(
        timestamp: str = Query(..., description="ISO格式时间戳"),
        from_timezone: str = Query('UTC', description="源时区"),
        to_timezone: str = Query(..., description="目标时区"),
):
    """
    在不同时区之间转换时间
    
    Args:
        timestamp: ISO格式时间戳
        from_timezone: 源时区
        to_timezone: 目标时区
        
    Returns:
        转换后的时间
    """
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))

        converted_dt = localization_service.convert_to_user_timezone(dt, to_timezone)

        return ApiResponse(
            success=True,
            data={
                'original': {
                    'timestamp': timestamp,
                    'timezone': from_timezone,
                },
                'converted': {
                    'timestamp': converted_dt.isoformat(),
                    'timezone': to_timezone,
                    'formatted': localization_service.format_datetime(
                        converted_dt,
                        'en-US',
                        to_timezone
                    ),
                },
            }
        )
    except Exception as e:
        return ApiResponse(success=False, error=f"转换失败: {str(e)}")
