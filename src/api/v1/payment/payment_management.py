"""
支付系统管理 API

提供支付网关(PaymentGateway)、支付交易(PaymentTransaction)、税务配置(TaxConfig) 的 CRUD 管理接口
"""
import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models import PaymentGateway, PaymentTransaction, TaxConfig
from src.api.v1.core.responses import ApiResponse
from src.auth import jwt_required_dependency as jwt_required
from src.extensions import get_async_db_session as get_async_db

router = APIRouter(tags=["payment-management"])


# ==================== 支付网关管理 ====================


@router.get("/gateways")
async def list_gateways(
    page: int = Query(1, ge=1, description="页码"),
    per_page: int = Query(20, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    provider: Optional[str] = Query(None, description="提供商筛选"),
    is_active: Optional[bool] = Query(None, description="是否激活"),
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(jwt_required),
):
    """
    获取支付网关列表

    支持分页、搜索、按提供商和激活状态筛选
    """
    try:
        # 检查管理员权限
        is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
        if not is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")

        query = select(PaymentGateway)

        # 搜索
        if search:
            query = query.where(
                or_(
                    PaymentGateway.name.ilike(f"%{search}%"),
                    PaymentGateway.provider.ilike(f"%{search}%"),
                )
            )

        # 提供商筛选
        if provider:
            query = query.where(PaymentGateway.provider == provider)

        # 激活状态筛选
        if is_active is not None:
            query = query.where(PaymentGateway.is_active == is_active)

        # 按创建时间降序排序
        query = query.order_by(PaymentGateway.created_at.desc())

        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # 分页
        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)

        result = await db.execute(query)
        gateways = result.scalars().all()

        return ApiResponse(
            success=True,
            data={
                "gateways": [g.to_dict() for g in gateways],
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": total,
                    "total_pages": (total + per_page - 1) // per_page if total > 0 else 0,
                },
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.get("/gateways/{gateway_id}")
async def get_gateway(
    gateway_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(jwt_required),
):
    """获取支付网关详情"""
    try:
        is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
        if not is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")

        query = select(PaymentGateway).where(PaymentGateway.id == gateway_id)
        result = await db.execute(query)
        gateway = result.scalar_one_or_none()

        if not gateway:
            return ApiResponse(success=False, error="支付网关不存在")

        return ApiResponse(success=True, data=gateway.to_dict(exclude_sensitive=False))
    except HTTPException:
        raise
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.post("/gateways")
async def create_gateway(
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(jwt_required),
):
    """创建支付网关"""
    try:
        is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
        if not is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")

        data = await request.json()

        name = data.get("name")
        provider = data.get("provider")
        if not name or not provider:
            return ApiResponse(success=False, error="name 和 provider 为必填字段")

        # 检查同一 provider 下是否已有同名网关
        existing = await db.execute(
            select(PaymentGateway).where(
                PaymentGateway.name == name,
                PaymentGateway.provider == provider,
            )
        )
        if existing.scalar_one_or_none():
            return ApiResponse(success=False, error=f"网关 '{name}' (provider={provider}) 已存在")

        # 处理 config_data：如果是 dict 则序列化为 JSON 字符串
        config_data = data.get("config_data")
        if isinstance(config_data, dict):
            config_data = json.dumps(config_data, ensure_ascii=False)

        now = datetime.utcnow()
        gateway = PaymentGateway(
            name=name,
            provider=provider,
            config_data=config_data,
            is_active=data.get("is_active", False),
            supported_currencies=data.get("supported_currencies", "USD,CNY"),
            created_at=now,
            updated_at=now,
        )

        db.add(gateway)
        await db.commit()
        await db.refresh(gateway)

        return ApiResponse(success=True, data=gateway.to_dict(), message="支付网关创建成功")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        return ApiResponse(success=False, error=str(e))


@router.put("/gateways/{gateway_id}")
async def update_gateway(
    gateway_id: int,
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(jwt_required),
):
    """更新支付网关"""
    try:
        is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
        if not is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")

        query = select(PaymentGateway).where(PaymentGateway.id == gateway_id)
        result = await db.execute(query)
        gateway = result.scalar_one_or_none()

        if not gateway:
            return ApiResponse(success=False, error="支付网关不存在")

        data = await request.json()

        # 可更新字段
        updatable_fields = ["name", "provider", "is_active", "supported_currencies"]
        for field in updatable_fields:
            if field in data:
                setattr(gateway, field, data[field])

        # 特殊处理 config_data
        if "config_data" in data:
            config_data = data["config_data"]
            gateway.config_data = json.dumps(config_data, ensure_ascii=False) if isinstance(config_data,
                                                                                            dict) else config_data

        gateway.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(gateway)

        return ApiResponse(success=True, data=gateway.to_dict(), message="支付网关更新成功")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        return ApiResponse(success=False, error=str(e))


@router.delete("/gateways/{gateway_id}")
async def delete_gateway(
    gateway_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(jwt_required),
):
    """删除支付网关"""
    try:
        is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
        if not is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")

        query = select(PaymentGateway).where(PaymentGateway.id == gateway_id)
        result = await db.execute(query)
        gateway = result.scalar_one_or_none()

        if not gateway:
            return ApiResponse(success=False, error="支付网关不存在")

        # 检查是否有关联的交易记录
        txn_count_query = select(func.count()).where(PaymentTransaction.gateway == gateway_id)
        txn_count_result = await db.execute(txn_count_query)
        txn_count = txn_count_result.scalar()

        if txn_count > 0:
            return ApiResponse(
                success=False,
                error=f"该网关下有 {txn_count} 条交易记录，请先删除或迁移交易记录后再删除网关",
            )

        await db.delete(gateway)
        await db.commit()

        return ApiResponse(success=True, message="支付网关删除成功")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        return ApiResponse(success=False, error=str(e))


# ==================== 支付交易管理 ====================


@router.get("/transactions")
async def list_transactions(
    page: int = Query(1, ge=1, description="页码"),
    per_page: int = Query(20, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索订单ID/交易ID"),
    status: Optional[str] = Query(None, description="交易状态"),
    payment_method: Optional[str] = Query(None, description="支付方式"),
    currency: Optional[str] = Query(None, description="货币类型"),
    user_id: Optional[int] = Query(None, description="用户ID"),
    gateway_id: Optional[int] = Query(None, description="网关ID"),
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(jwt_required),
):
    """
    获取支付交易列表

    支持分页、多条件筛选
    """
    try:
        is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
        if not is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")

        query = select(PaymentTransaction)

        # 搜索
        if search:
            query = query.where(
                or_(
                    PaymentTransaction.order_id.ilike(f"%{search}%"),
                    PaymentTransaction.transaction_id.ilike(f"%{search}%"),
                )
            )

        # 状态筛选
        if status:
            query = query.where(PaymentTransaction.status == status)

        # 支付方式筛选
        if payment_method:
            query = query.where(PaymentTransaction.payment_method == payment_method)

        # 货币筛选
        if currency:
            query = query.where(PaymentTransaction.currency == currency.upper())

        # 用户筛选
        if user_id:
            query = query.where(PaymentTransaction.user == user_id)

        # 网关筛选
        if gateway_id:
            query = query.where(PaymentTransaction.gateway == gateway_id)

        # 按创建时间降序排序
        query = query.order_by(PaymentTransaction.created_at.desc())

        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # 分页
        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)

        result = await db.execute(query)
        transactions = result.scalars().all()

        return ApiResponse(
            success=True,
            data={
                "transactions": [t.to_dict() for t in transactions],
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": total,
                    "total_pages": (total + per_page - 1) // per_page if total > 0 else 0,
                },
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.get("/transactions/{transaction_id}")
async def get_transaction(
    transaction_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(jwt_required),
):
    """获取支付交易详情"""
    try:
        is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
        if not is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")

        query = select(PaymentTransaction).where(PaymentTransaction.id == transaction_id)
        result = await db.execute(query)
        transaction = result.scalar_one_or_none()

        if not transaction:
            return ApiResponse(success=False, error="交易记录不存在")

        return ApiResponse(success=True, data=transaction.to_dict(exclude_sensitive=False))
    except HTTPException:
        raise
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.post("/transactions")
async def create_transaction(
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(jwt_required),
):
    """创建支付交易记录（管理员手动记录）"""
    try:
        is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
        if not is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")

        data = await request.json()

        user = data.get("user")
        amount = data.get("amount")
        if not user or amount is None:
            return ApiResponse(success=False, error="user 和 amount 为必填字段")

        # 验证网关存在性
        gateway_id = data.get("gateway")
        if gateway_id:
            gw_query = select(PaymentGateway).where(PaymentGateway.id == gateway_id)
            gw_result = await db.execute(gw_query)
            if not gw_result.scalar_one_or_none():
                return ApiResponse(success=False, error=f"网关 ID={gateway_id} 不存在")

        # 检查 order_id 唯一性
        order_id = data.get("order_id")
        if order_id:
            existing = await db.execute(
                select(PaymentTransaction).where(PaymentTransaction.order_id == order_id)
            )
            if existing.scalar_one_or_none():
                return ApiResponse(success=False, error=f"订单ID '{order_id}' 已存在")

        now = datetime.utcnow()
        transaction = PaymentTransaction(
            user=user,
            order_id=order_id,
            gateway=gateway_id,
            amount=amount,
            currency=data.get("currency", "USD"),
            status=data.get("status", "pending"),
            transaction_id=data.get("transaction_id"),
            payment_method=data.get("payment_method"),
            extra_metadata=json.dumps(data["extra_metadata"], ensure_ascii=False)
            if "extra_metadata" in data and isinstance(data["extra_metadata"], dict)
            else data.get("extra_metadata"),
            created_at=now,
            updated_at=now,
        )

        db.add(transaction)
        await db.commit()
        await db.refresh(transaction)

        return ApiResponse(success=True, data=transaction.to_dict(), message="交易记录创建成功")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        return ApiResponse(success=False, error=str(e))


@router.put("/transactions/{transaction_id}")
async def update_transaction(
    transaction_id: int,
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(jwt_required),
):
    """更新支付交易记录"""
    try:
        is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
        if not is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")

        query = select(PaymentTransaction).where(PaymentTransaction.id == transaction_id)
        result = await db.execute(query)
        transaction = result.scalar_one_or_none()

        if not transaction:
            return ApiResponse(success=False, error="交易记录不存在")

        data = await request.json()

        # 可更新字段
        updatable_fields = [
            "status", "transaction_id", "payment_method", "currency",
            "order_id",
        ]
        for field in updatable_fields:
            if field in data:
                setattr(transaction, field, data[field])

        # 金额更新需谨慎
        if "amount" in data:
            transaction.amount = data["amount"]

        # 特殊处理 extra_metadata
        if "extra_metadata" in data:
            meta = data["extra_metadata"]
            transaction.extra_metadata = json.dumps(meta, ensure_ascii=False) if isinstance(meta, dict) else meta

        transaction.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(transaction)

        return ApiResponse(success=True, data=transaction.to_dict(), message="交易记录更新成功")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        return ApiResponse(success=False, error=str(e))


@router.delete("/transactions/{transaction_id}")
async def delete_transaction(
    transaction_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(jwt_required),
):
    """删除支付交易记录"""
    try:
        is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
        if not is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")

        query = select(PaymentTransaction).where(PaymentTransaction.id == transaction_id)
        result = await db.execute(query)
        transaction = result.scalar_one_or_none()

        if not transaction:
            return ApiResponse(success=False, error="交易记录不存在")

        # 安全检查：只允许删除 pending 或 failed 状态的交易
        if transaction.status not in ("pending", "failed", "cancelled"):
            return ApiResponse(
                success=False,
                error=f"不允许删除状态为 '{transaction.status}' 的交易记录，请先将其状态变更为 cancelled",
            )

        await db.delete(transaction)
        await db.commit()

        return ApiResponse(success=True, message="交易记录删除成功")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        return ApiResponse(success=False, error=str(e))


# ==================== 税务配置管理 ====================


@router.get("/tax-configs")
async def list_tax_configs(
    page: int = Query(1, ge=1, description="页码"),
    per_page: int = Query(20, ge=1, le=100, description="每页数量"),
    country: Optional[str] = Query(None, description="国家代码 (ISO 3166-1)"),
    region: Optional[str] = Query(None, description="地区"),
    tax_type: Optional[str] = Query(None, description="税种类型"),
    is_active: Optional[bool] = Query(None, description="是否激活"),
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(jwt_required),
):
    """
    获取税务配置列表

    支持分页、按国家/地区/税种/激活状态筛选
    """
    try:
        is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
        if not is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")

        query = select(TaxConfig)

        # 国家筛选
        if country:
            query = query.where(TaxConfig.country == country.upper())

        # 地区筛选
        if region:
            query = query.where(TaxConfig.region.ilike(f"%{region}%"))

        # 税种筛选
        if tax_type:
            query = query.where(TaxConfig.tax_type == tax_type)

        # 激活状态筛选
        if is_active is not None:
            query = query.where(TaxConfig.is_active == is_active)

        # 按国家、地区排序
        query = query.order_by(TaxConfig.country, TaxConfig.region, TaxConfig.created_at.desc())

        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # 分页
        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)

        result = await db.execute(query)
        configs = result.scalars().all()

        return ApiResponse(
            success=True,
            data={
                "tax_configs": [c.to_dict() for c in configs],
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": total,
                    "total_pages": (total + per_page - 1) // per_page if total > 0 else 0,
                },
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.get("/tax-configs/{config_id}")
async def get_tax_config(
    config_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(jwt_required),
):
    """获取税务配置详情"""
    try:
        is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
        if not is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")

        query = select(TaxConfig).where(TaxConfig.id == config_id)
        result = await db.execute(query)
        config = result.scalar_one_or_none()

        if not config:
            return ApiResponse(success=False, error="税务配置不存在")

        return ApiResponse(success=True, data=config.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        return ApiResponse(success=False, error=str(e))


@router.post("/tax-configs")
async def create_tax_config(
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(jwt_required),
):
    """创建税务配置"""
    try:
        is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
        if not is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")

        data = await request.json()

        country = data.get("country")
        tax_type = data.get("tax_type")
        rate = data.get("rate")
        if not country or not tax_type or rate is None:
            return ApiResponse(success=False, error="country、tax_type、rate 为必填字段")

        # 检查同一国家/地区/税种下是否已有配置
        existing_query = select(TaxConfig).where(
            TaxConfig.country == country.upper(),
            TaxConfig.tax_type == tax_type,
        )
        # 如果有 region，也要匹配
        region = data.get("region")
        if region:
            existing_query = existing_query.where(TaxConfig.region == region)
        else:
            existing_query = existing_query.where(TaxConfig.region.is_(None))

        existing_result = await db.execute(existing_query)
        if existing_result.scalar_one_or_none():
            region_label = f"/{region}" if region else ""
            return ApiResponse(
                success=False,
                error=f"国家 {country.upper()}{region_label} 的 {tax_type} 税务配置已存在",
            )

        now = datetime.utcnow()

        # 处理日期字段
        effective_from = data.get("effective_from")
        if isinstance(effective_from, str):
            effective_from = datetime.fromisoformat(effective_from.replace("Z", "+00:00"))
        elif effective_from is None:
            effective_from = now

        effective_to = data.get("effective_to")
        if isinstance(effective_to, str):
            effective_to = datetime.fromisoformat(effective_to.replace("Z", "+00:00"))

        config = TaxConfig(
            country=country.upper(),
            region=region,
            tax_type=tax_type,
            rate=rate,
            description=data.get("description"),
            is_active=data.get("is_active", True),
            effective_from=effective_from,
            effective_to=effective_to,
            created_at=now,
            updated_at=now,
        )

        db.add(config)
        await db.commit()
        await db.refresh(config)

        return ApiResponse(success=True, data=config.to_dict(), message="税务配置创建成功")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        return ApiResponse(success=False, error=str(e))


@router.put("/tax-configs/{config_id}")
async def update_tax_config(
    config_id: int,
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(jwt_required),
):
    """更新税务配置"""
    try:
        is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
        if not is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")

        query = select(TaxConfig).where(TaxConfig.id == config_id)
        result = await db.execute(query)
        config = result.scalar_one_or_none()

        if not config:
            return ApiResponse(success=False, error="税务配置不存在")

        data = await request.json()

        # 可更新字段
        updatable_fields = ["country", "region", "tax_type", "rate", "description", "is_active"]
        for field in updatable_fields:
            if field in data:
                value = data[field]
                if field == "country" and value:
                    value = value.upper()
                setattr(config, field, value)

        # 日期字段
        if "effective_from" in data:
            ef = data["effective_from"]
            config.effective_from = datetime.fromisoformat(ef.replace("Z", "+00:00")) if isinstance(ef, str) else ef

        if "effective_to" in data:
            et = data["effective_to"]
            config.effective_to = datetime.fromisoformat(et.replace("Z", "+00:00")) if isinstance(et, str) else et

        config.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(config)

        return ApiResponse(success=True, data=config.to_dict(), message="税务配置更新成功")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        return ApiResponse(success=False, error=str(e))


@router.delete("/tax-configs/{config_id}")
async def delete_tax_config(
    config_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(jwt_required),
):
    """删除税务配置"""
    try:
        is_admin = getattr(current_user, 'is_superuser', False) or getattr(current_user, 'is_staff', False)
        if not is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")

        query = select(TaxConfig).where(TaxConfig.id == config_id)
        result = await db.execute(query)
        config = result.scalar_one_or_none()

        if not config:
            return ApiResponse(success=False, error="税务配置不存在")

        await db.delete(config)
        await db.commit()

        return ApiResponse(success=True, message="税务配置删除成功")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        return ApiResponse(success=False, error=str(e))
