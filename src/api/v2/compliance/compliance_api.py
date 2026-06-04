"""
合规性管理 API - V2 版本
提供 GDPR、CCPA、中国网络安全法等法规的合规性检查和指导
"""
from typing import Optional

from fastapi import APIRouter, Depends, Body

from shared.models.user import User
from shared.services.compliance.compliance_service import ComplianceService
from src.api.v1.core.responses import ApiResponse
from src.auth import jwt_required_dependency as jwt_required

router = APIRouter(prefix="/compliance", tags=["Compliance Management"])

# 初始化合规性服务
compliance_service = ComplianceService()


@router.get("/gdpr/check", summary="GDPR 合规性检查")
async def check_gdpr_compliance(
        current_user: User = Depends(jwt_required)
):
    """
    执行 GDPR 合规性检查
    
    返回详细的合规性要求清单和实施建议
    """
    # 检查管理员权限
    if not current_user.is_superuser:
        return ApiResponse(
            success=False,
            error="需要管理员权限"
        )

    try:
        result = compliance_service.check_gdpr_compliance()

        return ApiResponse(
            success=True,
            data=result
        )

    except Exception as e:
        return ApiResponse(
            success=False,
            error=f"检查失败: {str(e)}"
        )


@router.get("/ccpa/check", summary="CCPA 合规性检查")
async def check_ccpa_compliance(
        current_user: User = Depends(jwt_required)
):
    """
    执行 CCPA 合规性检查
    
    返回加州消费者隐私法案的合规要求和实施指南
    """
    # 检查管理员权限
    if not current_user.is_superuser:
        return ApiResponse(
            success=False,
            error="需要管理员权限"
        )

    try:
        result = compliance_service.check_ccpa_compliance()

        return ApiResponse(
            success=True,
            data=result
        )

    except Exception as e:
        return ApiResponse(
            success=False,
            error=f"检查失败: {str(e)}"
        )


@router.get("/china/check", summary="中国网络安全法合规性检查")
async def check_china_cybersecurity_compliance(
        current_user: User = Depends(jwt_required)
):
    """
    执行中国网络安全法合规性检查
    
    包括网络安全法、数据安全法、个人信息保护法的要求
    """
    # 检查管理员权限
    if not current_user.is_superuser:
        return ApiResponse(
            success=False,
            error="需要管理员权限"
        )

    try:
        result = compliance_service.check_china_cybersecurity_compliance()

        return ApiResponse(
            success=True,
            data=result
        )

    except Exception as e:
        return ApiResponse(
            success=False,
            error=f"检查失败: {str(e)}"
        )


@router.get("/checklist/{region}", summary="获取地区合规检查清单")
async def get_compliance_checklist(
        region: str,
        current_user: User = Depends(jwt_required)
):
    """
    获取特定地区的合规性检查清单
    
    参数:
    - region: 地区代码 (eu, california, china, global)
    
    返回该地区的完整合规要求和实施步骤
    """
    # 检查管理员权限
    if not current_user.is_superuser:
        return ApiResponse(
            success=False,
            error="需要管理员权限"
        )

    try:
        result = compliance_service.get_compliance_checklist(region)

        return ApiResponse(
            success=True,
            data=result
        )

    except Exception as e:
        return ApiResponse(
            success=False,
            error=f"获取清单失败: {str(e)}"
        )


@router.post("/privacy-policy/generate", summary="生成隐私政策模板")
async def generate_privacy_policy(
        company_name: Optional[str] = Body(None),
        company_email: Optional[str] = Body(None),
        company_address: Optional[str] = Body(None),
        current_user: User = Depends(jwt_required)
):
    """
    生成隐私政策模板
    
    参数:
    - company_name: 公司名称
    - company_email: 联系邮箱
    - company_address: 公司地址
    
    返回可定制的隐私政策模板
    """
    try:
        company_info = {}
        if company_name:
            company_info['name'] = company_name
        if company_email:
            company_info['email'] = company_email
        if company_address:
            company_info['address'] = company_address

        template = compliance_service.generate_privacy_policy_template(company_info)

        return ApiResponse(
            success=True,
            data={
                'template': template,
                'format': 'markdown',
                'note': '请根据实际情况修改模板内容，并咨询法律专业人士'
            }
        )

    except Exception as e:
        return ApiResponse(
            success=False,
            error=f"生成失败: {str(e)}"
        )


@router.get("/data-retention", summary="获取数据保留建议")
async def get_data_retention_recommendations(
        current_user: User = Depends(jwt_required)
):
    """
    获取不同类型数据的保留期限建议
    
    基于各法规要求提供最佳实践
    """
    try:
        recommendations = compliance_service.get_data_retention_recommendations()

        return ApiResponse(
            success=True,
            data=recommendations
        )

    except Exception as e:
        return ApiResponse(
            success=False,
            error=f"获取建议失败: {str(e)}"
        )


@router.get("/overview", summary="合规性概览")
async def get_compliance_overview(
        current_user: User = Depends(jwt_required)
):
    """
    获取所有适用法规的概览信息
    
    快速了解需要遵守的主要法规和要求
    """
    return ApiResponse(
        success=True,
        data={
            'title': '数据隐私与合规概览',
            'regulations': [
                {
                    'name': 'GDPR',
                    'full_name': '欧盟通用数据保护条例',
                    'region': 'European Union',
                    'effective_date': '2018-05-25',
                    'applies_if': '处理欧盟公民的个人数据',
                    'key_rights': [
                        '访问权',
                        '删除权（被遗忘权）',
                        '数据可携带权',
                        '反对权',
                        '限制处理权'
                    ],
                    'max_penalty': '€20 million or 4% of annual turnover',
                    'documentation_url': 'https://gdpr-info.eu/'
                },
                {
                    'name': 'CCPA/CPRA',
                    'full_name': '加州消费者隐私法案 / 加州隐私权利法案',
                    'region': 'California, USA',
                    'effective_date': '2020-01-01 (CCPA), 2023-01-01 (CPRA)',
                    'applies_if': '面向加州消费者且满足收入或数据处理门槛',
                    'key_rights': [
                        '知情权',
                        '删除权',
                        '选择退出出售权',
                        '更正权',
                        '限制敏感信息使用权'
                    ],
                    'max_penalty': '$7,500 per intentional violation',
                    'documentation_url': 'https://oag.ca.gov/privacy/ccpa'
                },
                {
                    'name': 'PIPL',
                    'full_name': '中华人民共和国个人信息保护法',
                    'region': 'China',
                    'effective_date': '2021-11-01',
                    'applies_if': '在中国境内处理自然人个人信息',
                    'key_rights': [
                        '知情权和决定权',
                        '查阅复制权',
                        '更正补充权',
                        '删除权',
                        '解释说明权'
                    ],
                    'max_penalty': '¥50 million or 5% of annual turnover',
                    'documentation_url': 'http://www.cac.gov.cn/'
                },
                {
                    'name': 'LGPD',
                    'full_name': '巴西通用数据保护法',
                    'region': 'Brazil',
                    'effective_date': '2020-09-18',
                    'applies_if': '在巴西处理个人数据',
                    'key_rights': [
                        '访问权',
                        '更正权',
                        '删除权',
                        '数据可携带权',
                        '撤销同意权'
                    ],
                    'max_penalty': 'R$50 million per violation',
                    'documentation_url': 'https://www.gov.br/anpd/'
                },
                {
                    'name': 'PDPA',
                    'full_name': '新加坡个人数据保护法',
                    'region': 'Singapore',
                    'effective_date': '2014-01-02',
                    'applies_if': '在新加坡收集、使用或披露个人数据',
                    'key_rights': [
                        '访问权',
                        '更正权',
                        '撤回同意权',
                        '投诉权'
                    ],
                    'max_penalty': 'S$1 million',
                    'documentation_url': 'https://www.pdpc.gov.sg/'
                }
            ],
            'best_practices': [
                '进行数据映射和分类',
                '实施隐私设计原则',
                '建立数据主体权利响应流程',
                '定期进行合规审计',
                '培训员工数据保护意识',
                '保持文档记录',
                '制定数据泄露应急响应计划',
                '与服务提供商签订数据处理协议'
            ],
            'tools_and_resources': [
                'OneTrust - 合规管理平台',
                'Cookiebot - Cookie 同意管理',
                'Termly - 政策生成器',
                'IAPP - 国际隐私专业人员协会',
                'EDPB Guidelines - 欧盟数据保护委员会指南'
            ]
        }
    )


@router.get("/comparison", summary="法规对比")
async def compare_regulations():
    """
    对比主要数据隐私法规的异同
    
    帮助理解不同法规的要求和差异
    """
    return ApiResponse(
        success=True,
        data={
            'title': '主要数据隐私法规对比',
            'comparison_table': {
                'headers': ['特性', 'GDPR', 'CCPA/CPRA', 'PIPL (中国)'],
                'rows': [
                    {
                        'feature': '适用范围',
                        'gdpr': '欧盟境内的数据处理活动',
                        'ccpa': '加州消费者的个人信息',
                        'pipl': '中国境内的个人信息处理'
                    },
                    {
                        'feature': '同意要求',
                        'gdpr': '明确、具体、知情的同意',
                        'ccpa': '选择退出机制为主',
                        'pipl': '单独同意或书面同意'
                    },
                    {
                        'feature': '数据最小化',
                        'gdpr': '是（核心原则）',
                        'ccpa': '部分要求',
                        'pipl': '是（必要原则）'
                    },
                    {
                        'feature': '跨境传输',
                        'gdpr': '充分性决定、SCC、BCR',
                        'ccpa': '无特别限制',
                        'pipl': '安全评估、标准合同、认证'
                    },
                    {
                        'feature': '数据本地化',
                        'gdpr': '无要求',
                        'ccpa': '无要求',
                        'pipl': '关键信息基础设施运营者需本地存储'
                    },
                    {
                        'feature': 'DPO/负责人',
                        'gdpr': '某些情况下必须任命',
                        'ccpa': '无要求',
                        'pipl': '个人信息保护负责人'
                    },
                    {
                        'feature': '影响评估',
                        'gdpr': 'DPIA（数据保护影响评估）',
                        'ccpa': '无明确要求',
                        'pipl': '个人信息保护影响评估'
                    },
                    {
                        'feature': '泄露通知时限',
                        'gdpr': '72小时',
                        'ccpa': '尽快通知',
                        'pipl': '立即采取补救措施并通知'
                    },
                    {
                        'feature': '消费者权利',
                        'gdpr': '8项主要权利',
                        'ccpa': '5项主要权利',
                        'pipl': '7项主要权利'
                    },
                    {
                        'feature': '罚款上限',
                        'gdpr': '€20M或4%营业额',
                        'ccpa': '$7,500/故意违规',
                        'pipl': '¥50M或5%营业额'
                    }
                ]
            },
            'key_differences': [
                {
                    'aspect': '同意模式',
                    'description': 'GDPR采用选择加入（opt-in），CCPA采用选择退出（opt-out），PIPL根据情况要求单独同意'
                },
                {
                    'aspect': '地域范围',
                    'description': 'GDPR有域外效力，CCPA主要针对加州居民，PIPL适用于中国境内处理活动'
                },
                {
                    'aspect': '数据主权',
                    'description': 'PIPL强调数据本地化和出境管制，GDPR关注充分性保护，CCPA无此要求'
                },
                {
                    'aspect': '执行力度',
                    'description': 'GDPR由各国监管机构执行，CCPA允许私人诉讼，PIPL由网信部门监管'
                }
            ],
            'compliance_strategy': [
                '采用最高标准（通常以GDPR为基准）',
                '实施统一的隐私管理框架',
                '按地区定制特定要求',
                '定期监控法规变化',
                '建立全球合规团队'
            ]
        }
    )
