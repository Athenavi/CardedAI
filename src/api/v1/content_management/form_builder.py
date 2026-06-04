"""
表单构建器API
提供动态表单的创建、管理、提交等功能
"""

import json
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, Query, Body, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.form import Form
from shared.models.form_field import FormField
from shared.models.form_submission import FormSubmission
from shared.services.content_management.form_builder import form_builder
from src.api.v1.core.responses import ApiResponse
from src.auth.auth_deps import admin_required as admin_required_api
from src.extensions import get_async_db_session as get_async_db

router = APIRouter(tags=["form-builder"])


async def send_form_notification_email(
    form_title: str,
    notification_email: str,
    submission_data: Dict[str, Any]
):
    """
    后台发送表单通知邮件(不阻塞主进程)

    Args:
        form_title: 表单标题
        notification_email: 通知邮箱
        submission_data: 提交数据
    """
    try:
        from shared.services.notifications.email_service import email_service
        from datetime import datetime

        subject = f"新表单提交: {form_title}"

        # 构建HTML邮件内容
        html_content = f"""
        <h2>新表单提交</h2>
        <p><strong>表单:</strong> {form_title}</p>
        <p><strong>提交时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <h3>提交数据:</h3>
        <ul>
        """

        for key, value in submission_data.items():
            html_content += f"<li><strong>{key}:</strong> {value}</li>"

        html_content += "</ul>"

        # 纯文本内容
        text_content = f"新表单提交: {form_title}\n\n" + "\n".join(
            [f"{k}: {v}" for k, v in submission_data.items()]
        )

        # 发送邮件
        email_service.send_email(
            to_email=notification_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )

        print(f"表单通知邮件已发送到: {notification_email}")

    except Exception as e:
        print(f"发送表单通知邮件失败: {e}")
        import traceback
        traceback.print_exc()


@router.get("/field-types")
async def get_field_types():
    """获取所有支持的字段类型"""
    try:
        field_types = form_builder.get_field_types()

        return ApiResponse(
            success=True,
            data={'field_types': field_types}
        )

    except Exception as e:
        return ApiResponse(success=False, error=f"获取字段类型失败: {str(e)}")


@router.get("/templates")
async def get_form_templates():
    """获取表单模板列表"""
    try:
        templates = form_builder.get_templates()

        return ApiResponse(
            success=True,
            data={'templates': templates}
        )

    except Exception as e:
        return ApiResponse(success=False, error=f"获取模板失败: {str(e)}")


@router.get("/")
async def list_forms(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_async_db),
    current_user=Depends(admin_required_api)
):
    """
    获取表单列表

    Args:
        page: 页码
        per_page: 每页数量
        status: 按状态筛选 (draft, published, archived)
    """
    try:
        from sqlalchemy import func

        query = select(Form)
        if status:
            query = query.where(Form.status == status)

        # 获取总数
        count_stmt = select(func.count(Form.id))
        if status:
            count_stmt = count_stmt.where(Form.status == status)
        count_result = await db.execute(count_stmt)
        total = count_result.scalar() or 0

        # 分页查询
        offset = (page - 1) * per_page
        stmt = query.order_by(Form.created_at.desc()).offset(offset).limit(per_page)
        result = await db.execute(stmt)
        forms = result.scalars().all()

        form_list = []
        for f in forms:
            # 统计每个表单的提交数量
            sub_count_stmt = select(func.count(FormSubmission.id)).where(
                FormSubmission.form_id == f.id
            )
            sub_count_result = await db.execute(sub_count_stmt)
            submission_count = sub_count_result.scalar() or 0

            form_list.append({
                'id': f.id,
                'title': f.title,
                'slug': f.slug,
                'description': f.description,
                'status': f.status,
                'submission_count': submission_count,
                'email_notification': f.email_notification,
                'notification_email': f.notification_email,
                'store_submissions': f.store_submissions,
                'created_at': f.created_at.isoformat() if f.created_at else None,
                'updated_at': f.updated_at.isoformat() if f.updated_at else None,
                'published_at': f.published_at.isoformat() if f.published_at else None,
            })

        return ApiResponse(
            success=True,
            data={
                'forms': form_list,
                'total': total,
                'page': page,
                'per_page': per_page
            }
        )

    except Exception as e:
        return ApiResponse(success=False, error=f"获取表单列表失败: {str(e)}")


@router.post("/")
async def create_form(
        title: str = Body(...),
        description: str = Body(''),
        fields: Optional[List[Dict]] = Body(None),
        template: Optional[str] = Body(None),
        settings: Optional[Dict] = Body(None),
        current_user=Depends(admin_required_api)
):
    """
    创建新表单

    Args:
        title: 表单标题
        description: 表单描述
        fields: 字段配置列表
        template: 使用预设模板
        settings: 表单设置
    """
    try:
        result = form_builder.create_form(
            title=title,
            description=description,
            fields=fields,
            template=template,
            settings=settings
        )

        if result['success']:
            return ApiResponse(
                success=True,
                data=result['data'],
                message="表单创建成功"
            )
        else:
            return ApiResponse(success=False, error=result.get('error'))

    except Exception as e:
        return ApiResponse(success=False, error=f"创建表单失败: {str(e)}")


@router.post("/validate")
async def validate_form_submission(
        form_id: int = Body(...),
        submission: Dict[str, Any] = Body(...),
        db: AsyncSession = Depends(get_async_db)
):
    """
    验证表单提交数据

    Args:
        form_id: 表单ID
        submission: 提交的表单数据
    """
    try:
        # 从数据库获取表单配置
        stmt = select(Form).where(Form.id == form_id)
        result = await db.execute(stmt)
        form = result.scalar_one_or_none()

        if not form:
            return ApiResponse(success=False, error="表单不存在")

        # 获取表单字段
        stmt = select(FormField).where(
            FormField.form_id == form_id,
            FormField.is_active == True
        ).order_by(FormField.order_index)
        result = await db.execute(stmt)
        fields = result.scalars().all()

        # 构建表单数据
        form_data = {
            'id': form.id,
            'title': form.title,
            'description': form.description,
            'fields': [
                {
                    'type': field.field_type,
                    'name': field.label.lower().replace(' ', '_'),
                    'label': field.label,
                    'config': {
                        'required': field.required,
                        'placeholder': field.placeholder,
                        'help_text': field.help_text,
                        'default_value': field.default_value,
                        'options': json.loads(field.options) if field.options else None,
                        'validation_rules': json.loads(field.validation_rules) if field.validation_rules else None
                    }
                }
                for field in fields
            ]
        }

        validation_result = form_builder.validate_form_submission(
            form_data=form_data,
            submission=submission
        )

        if validation_result['valid']:
            return ApiResponse(
                success=True,
                data={'valid': True, 'message': '验证通过'},
                message="表单验证通过"
            )
        else:
            return ApiResponse(
                success=False,
                data={
                    'valid': False,
                    'errors': validation_result['errors']
                },
                error="表单验证失败"
            )

    except Exception as e:
        return ApiResponse(success=False, error=f"验证失败: {str(e)}")


@router.get("/{form_id}/html")
async def generate_form_html(
        form_id: int,
        db: AsyncSession = Depends(get_async_db)
):
    """
    生成表单HTML代码

    Args:
        form_id: 表单ID
    """
    try:
        # 从数据库获取表单配置
        stmt = select(Form).where(Form.id == form_id)
        result = await db.execute(stmt)
        form = result.scalar_one_or_none()

        if not form:
            return ApiResponse(success=False, error="表单不存在")

        # 获取表单字段
        stmt = select(FormField).where(
            FormField.form_id == form_id,
            FormField.is_active == True
        ).order_by(FormField.order_index)
        result = await db.execute(stmt)
        fields = result.scalars().all()

        # 构建表单数据
        sample_form = {
            'title': form.title,
            'description': form.description,
            'fields': [
                {
                    'type': field.field_type,
                    'name': field.label.lower().replace(' ', '_'),
                    'label': field.label,
                    'config': {
                        'required': field.required,
                        'placeholder': field.placeholder,
                        'help_text': field.help_text,
                        'rows': 6 if field.field_type == 'textarea' else None,
                        'options': json.loads(field.options) if field.options else None
                    }
                }
                for field in fields
            ],
            'settings': {
                'submit_button_text': '提交'
            }
        }

        html = form_builder.generate_form_html(sample_form, f'form-{form_id}')

        return ApiResponse(
            success=True,
            data={'html': html}
        )

    except Exception as e:
        return ApiResponse(success=False, error=f"生成HTML失败: {str(e)}")


@router.post("/{form_id}/submit")
async def submit_form(
        form_id: int,
        submission: Dict[str, Any] = Body(...),
        background_tasks: BackgroundTasks = None,
        db: AsyncSession = Depends(get_async_db)
):
    """
    提交表单数据

    Args:
        form_id: 表单ID
        submission: 表单数据
    """
    try:
        # 1. 从数据库获取表单配置
        stmt = select(Form).where(Form.id == form_id)
        result = await db.execute(stmt)
        form = result.scalar_one_or_none()

        if not form:
            return ApiResponse(success=False, error="表单不存在")

        if form.status != 'published':
            return ApiResponse(success=False, error="表单未发布")

        # 获取表单字段
        stmt = select(FormField).where(
            FormField.form_id == form_id,
            FormField.is_active == True
        ).order_by(FormField.order_index)
        result = await db.execute(stmt)
        fields = result.scalars().all()

        form_data = {
            'fields': [
                {
                    'type': field.field_type,
                    'name': field.label.lower().replace(' ', '_'),
                    'label': field.label,
                    'config': {'required': field.required}
                }
                for field in fields
            ]
        }

        # 2. 验证提交数据
        validation_result = form_builder.validate_form_submission(
            form_data=form_data,
            submission=submission
        )

        if not validation_result['valid']:
            return ApiResponse(
                success=False,
                data={'errors': validation_result['errors']},
                error="表单验证失败"
            )

        # 3. 保存提交记录
        from datetime import datetime
        submission_record = FormSubmission(
            form_id=form_id,
            data=json.dumps(submission, ensure_ascii=False),
            ip_address=None,  # 可以从request中获取
            user_agent=None,
            status='new',
            created_at=datetime.now()
        )
        db.add(submission_record)
        await db.commit()

        # 4. 后台发送通知邮件(如果配置) - 不阻塞主进程
        if background_tasks and form.notification_email:
            background_tasks.add_task(
                send_form_notification_email,
                form_title=form.title,
                notification_email=form.notification_email,
                submission_data=submission
            )

        return ApiResponse(
            success=True,
            message="表单提交成功"
        )

    except Exception as e:
        return ApiResponse(success=False, error=f"提交失败: {str(e)}")


@router.get("/{form_id}/submissions")
async def get_form_submissions(
        form_id: int,
        page: int = Query(1, ge=1),
        per_page: int = Query(20, ge=1, le=100),
        db: AsyncSession = Depends(get_async_db),
        current_user=Depends(admin_required_api)
):
    """
    获取表单提交记录

    Args:
        form_id: 表单ID
        page: 页码
        per_page: 每页数量
    """
    try:
        # 从数据库查询提交记录
        from sqlalchemy import func

        # 获取总数
        count_stmt = select(func.count(FormSubmission.id)).where(
            FormSubmission.form_id == form_id
        )
        count_result = await db.execute(count_stmt)
        total = count_result.scalar()

        # 分页查询
        offset = (page - 1) * per_page
        stmt = select(FormSubmission).where(
            FormSubmission.form_id == form_id
        ).order_by(
            FormSubmission.created_at.desc()
        ).offset(offset).limit(per_page)
        result = await db.execute(stmt)
        submissions = result.scalars().all()

        # 转换为字典
        submission_list = []
        for sub in submissions:
            try:
                data = json.loads(sub.data) if sub.data else {}
            except:
                data = {}

            submission_list.append({
                'id': sub.id,
                'data': data,
                'ip_address': sub.ip_address,
                'user_agent': sub.user_agent,
                'status': sub.status,
                'created_at': sub.created_at.isoformat() if sub.created_at else None
            })

        return ApiResponse(
            success=True,
            data={
                'submissions': submission_list,
                'total': total,
                'page': page,
                'per_page': per_page
            }
        )

    except Exception as e:
        return ApiResponse(success=False, error=f"获取提交记录失败: {str(e)}")


@router.get("/{form_id}/statistics")
async def get_form_statistics(
        form_id: int,
        db: AsyncSession = Depends(get_async_db),
        current_user=Depends(admin_required_api)
):
    """
    获取表单统计数据

    Args:
        form_id: 表单ID
    """
    try:
        # 从数据库统计表单数据
        from sqlalchemy import func
        from datetime import datetime, timedelta

        # 总提交数
        count_stmt = select(func.count(FormSubmission.id)).where(
            FormSubmission.form_id == form_id
        )
        count_result = await db.execute(count_stmt)
        total_submissions = count_result.scalar() or 0

        # 最近7天提交数
        seven_days_ago = datetime.now() - timedelta(days=7)
        recent_stmt = select(func.count(FormSubmission.id)).where(
            FormSubmission.form_id == form_id,
            FormSubmission.created_at >= seven_days_ago
        )
        recent_result = await db.execute(recent_stmt)
        recent_submissions = recent_result.scalar() or 0

        # 完成率 (这里简化处理,实际需要更复杂的逻辑)
        completion_rate = 100.0 if total_submissions > 0 else 0

        stats = {
            'form_id': form_id,
            'total_submissions': total_submissions,
            'recent_submissions': recent_submissions,
            'completion_rate': completion_rate,
            'average_completion_time': None
        }

        return ApiResponse(
            success=True,
            data=stats
        )

    except Exception as e:
        return ApiResponse(success=False, error=f"获取统计数据失败: {str(e)}")


@router.delete("/{form_id}")
async def delete_form(
        form_id: int,
        db: AsyncSession = Depends(get_async_db),
        current_user=Depends(admin_required_api)
):
    """
    删除表单

    Args:
        form_id: 表单ID
    """
    try:
        # 从数据库删除表单及其提交记录
        # 先检查表单是否存在
        stmt = select(Form).where(Form.id == form_id)
        result = await db.execute(stmt)
        form = result.scalar_one_or_none()

        if not form:
            return ApiResponse(success=False, error="表单不存在")

        # 删除相关字段
        from sqlalchemy import delete
        stmt = delete(FormField).where(FormField.form_id == form_id)
        await db.execute(stmt)

        # 删除相关提交记录
        stmt = delete(FormSubmission).where(FormSubmission.form_id == form_id)
        await db.execute(stmt)

        # 删除表单
        await db.delete(form)
        await db.commit()

        return ApiResponse(
            success=True,
            message="表单删除成功"
        )

    except Exception as e:
        return ApiResponse(success=False, error=f"删除失败: {str(e)}")
