"""
库存跟踪服务

提供库存管理、库存检查、低库存警告等功能
基于现有 Product 模型的 stock 字段实现
"""
import json

from datetime import datetime
from typing import Dict, List

from sqlalchemy import select, update, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.product import Product

from src.unified_logger import default_logger as logger


class InventoryService:
    """库存跟踪服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def check_inventory(self, product_id: int, quantity: int) -> Dict:
        """
        检查产品库存是否充足
        
        Args:
            product_id: 产品ID
            quantity: 需要的数量
            
        Returns:
            检查结果
        """
        stmt = select(Product).where(Product.id == product_id)
        result = await self.db.execute(stmt)
        product = result.scalar_one_or_none()

        if not product:
            return {
                'available': False,
                'current_stock': 0,
                'requested_quantity': quantity,
                'message': '产品不存在'
            }

        current_stock = product.stock or 0

        return {
            'available': current_stock >= quantity,
            'current_stock': current_stock,
            'requested_quantity': quantity,
            'product_name': product.name,
            'sku': product.sku,
            'message': '库存充足' if current_stock >= quantity else f'库存不足，当前库存: {current_stock}'
        }

    async def deduct_inventory(self, product_id: int, quantity: int, order_id: int = None, user_id: int = None) -> Dict:
        """
        扣减库存（订单支付成功后）
        
        Args:
            product_id: 产品ID
            quantity: 扣减数量
            order_id: 关联订单ID
            user_id: 操作用户ID
            
        Returns:
            扣减结果
        """
        stmt = select(Product).where(Product.id == product_id)
        result = await self.db.execute(stmt)
        product = result.scalar_one_or_none()

        if not product:
            return {
                'success': False,
                'message': '产品不存在'
            }

        current_stock = product.stock or 0

        if current_stock < quantity:
            return {
                'success': False,
                'message': f'库存不足，当前库存: {current_stock}，需要: {quantity}'
            }

        # 扣减库存
        new_stock = current_stock - quantity
        await self.db.execute(
            update(Product)
            .where(Product.id == product_id)
            .values(
                stock=new_stock,
                updated_at=datetime.now()
            )
        )

        # 记录库存变更历史
        await self._log_inventory_change(
            product_id=product_id,
            change_type='sale',
            quantity_change=-quantity,
            quantity_before=current_stock,
            quantity_after=new_stock,
            reference_type='order',
            reference_id=order_id,
            notes=f'订单扣减库存',
            performed_by=user_id
        )

        logger.info(f"库存扣减成功: 产品ID={product_id}, 扣减={quantity}, 剩余={new_stock}")

        return {
            'success': True,
            'previous_stock': current_stock,
            'new_stock': new_stock,
            'deducted_quantity': quantity,
            'message': '库存扣减成功'
        }

    async def restore_inventory(self, product_id: int, quantity: int, order_id: int = None,
                                user_id: int = None) -> Dict:
        """
        恢复库存（订单取消或退款时）
        
        Args:
            product_id: 产品ID
            quantity: 恢复数量
            order_id: 关联订单ID
            user_id: 操作用户ID
            
        Returns:
            恢复结果
        """
        stmt = select(Product).where(Product.id == product_id)
        result = await self.db.execute(stmt)
        product = result.scalar_one_or_none()

        if not product:
            return {
                'success': False,
                'message': '产品不存在'
            }

        current_stock = product.stock or 0
        new_stock = current_stock + quantity

        # 恢复库存
        await self.db.execute(
            update(Product)
            .where(Product.id == product_id)
            .values(
                stock=new_stock,
                updated_at=datetime.now()
            )
        )

        # 记录库存变更历史
        await self._log_inventory_change(
            product_id=product_id,
            change_type='cancellation',
            quantity_change=quantity,
            quantity_before=current_stock,
            quantity_after=new_stock,
            reference_type='order',
            reference_id=order_id,
            notes=f'订单取消/退款，恢复库存',
            performed_by=user_id
        )

        logger.info(f"库存恢复成功: 产品ID={product_id}, 恢复={quantity}, 当前={new_stock}")

        return {
            'success': True,
            'previous_stock': current_stock,
            'new_stock': new_stock,
            'restored_quantity': quantity,
            'message': '库存恢复成功'
        }

    async def adjust_inventory(self, product_id: int, new_quantity: int, reason: str = '', user_id: int = None) -> Dict:
        """
        手动调整库存（管理员操作）
        
        Args:
            product_id: 产品ID
            new_quantity: 新的库存数量
            reason: 调整原因
            user_id: 操作用户ID
            
        Returns:
            调整结果
        """
        stmt = select(Product).where(Product.id == product_id)
        result = await self.db.execute(stmt)
        product = result.scalar_one_or_none()

        if not product:
            return {
                'success': False,
                'message': '产品不存在'
            }

        current_stock = product.stock or 0
        quantity_change = new_quantity - current_stock

        # 更新库存
        await self.db.execute(
            update(Product)
            .where(Product.id == product_id)
            .values(
                stock=new_quantity,
                updated_at=datetime.now(),
                last_restocked_at=datetime.now() if quantity_change > 0 else product.updated_at
            )
        )

        # 记录库存变更历史
        change_type = 'restock' if quantity_change > 0 else 'adjustment'
        await self._log_inventory_change(
            product_id=product_id,
            change_type=change_type,
            quantity_change=quantity_change,
            quantity_before=current_stock,
            quantity_after=new_quantity,
            reference_type='admin',
            reference_id=None,
            notes=reason or f'管理员手动调整库存',
            performed_by=user_id
        )

        logger.info(f"库存调整成功: 产品ID={product_id}, 从{current_stock}调整为{new_quantity}")

        return {
            'success': True,
            'previous_stock': current_stock,
            'new_stock': new_quantity,
            'quantity_change': quantity_change,
            'message': '库存调整成功'
        }

    async def get_low_stock_products(self, threshold: int = 10) -> List[Dict]:
        """
        获取低库存产品列表
        
        Args:
            threshold: 低库存阈值
            
        Returns:
            低库存产品列表
        """
        # 查询库存低于阈值的产品
        stmt = (
            select(Product)
            .where(
                and_(
                    Product.stock <= threshold,
                    Product.stock >= 0,
                    Product.is_active == True
                )
            )
            .order_by(Product.stock.asc())
        )

        result = await self.db.execute(stmt)
        products = result.scalars().all()

        low_stock_list = []
        for product in products:
            low_stock_list.append({
                'id': product.id,
                'name': product.name,
                'sku': product.sku,
                'current_stock': product.stock,
                'threshold': threshold,
                'shortage': threshold - product.stock,
                'is_out_of_stock': product.stock == 0
            })

        return low_stock_list

    async def get_inventory_report(self) -> Dict:
        """
        生成库存报告
        
        Returns:
            库存报告数据
        """
        # 统计总产品数
        total_stmt = select(func.count(Product.id)).where(Product.is_active == True)
        total_result = await self.db.execute(total_stmt)
        total_products = total_result.scalar() or 0

        # 统计低库存产品数（阈值=10）
        low_stock_stmt = select(func.count(Product.id)).where(
            and_(
                Product.stock <= 10,
                Product.stock >= 0,
                Product.is_active == True
            )
        )
        low_stock_result = await self.db.execute(low_stock_stmt)
        low_stock_count = low_stock_result.scalar() or 0

        # 统计缺货产品数
        out_of_stock_stmt = select(func.count(Product.id)).where(
            and_(
                Product.stock == 0,
                Product.is_active == True
            )
        )
        out_of_stock_result = await self.db.execute(out_of_stock_stmt)
        out_of_stock_count = out_of_stock_result.scalar() or 0

        # 计算总库存价值
        value_stmt = select(func.sum(Product.price * Product.stock)).where(
            and_(
                Product.is_active == True,
                Product.stock > 0
            )
        )
        value_result = await self.db.execute(value_stmt)
        total_inventory_value = float(value_result.scalar() or 0)

        return {
            'total_products': total_products,
            'low_stock_count': low_stock_count,
            'out_of_stock_count': out_of_stock_count,
            'total_inventory_value': round(total_inventory_value, 2),
            'report_generated_at': datetime.now().isoformat(),
            'message': '库存报告生成成功'
        }

    async def _log_inventory_change(
            self,
            product_id: int,
            change_type: str,
            quantity_change: int,
            quantity_before: int,
            quantity_after: int,
            reference_type: str = None,
            reference_id: int = None,
            notes: str = None,
            performed_by: int = None
    ):
        """
        记录库存变更历史到日志文件
        
        Args:
            product_id: 产品ID
            change_type: 变更类型 (sale/cancellation/restock/adjustment)
            quantity_change: 库存变化数量
            quantity_before: 变更前库存
            quantity_after: 变更后库存
            reference_type: 关联类型 (order/cart/admin)
            reference_id: 关联ID
            notes: 备注
            performed_by: 操作人ID
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'product_id': product_id,
            'change_type': change_type,
            'quantity_change': quantity_change,
            'quantity_before': quantity_before,
            'quantity_after': quantity_after,
            'reference_type': reference_type,
            'reference_id': reference_id,
            'notes': notes,
            'performed_by': performed_by
        }

        # 写入日志文件
        try:
            log_file = 'logs/inventory_changes.jsonl'
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
        except Exception as e:
            logger.error(f"记录库存变更日志失败: {e}")


def create_inventory_service(db: AsyncSession) -> InventoryService:
    """创建库存服务实例"""
    return InventoryService(db)
