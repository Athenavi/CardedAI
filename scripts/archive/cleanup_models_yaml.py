"""
从 config/models.yaml 中删除不需要的模型定义。
运行方式: python scripts/cleanup_models_yaml.py
"""
import re
import sys

# 需要删除的模型名称列表
MODELS_TO_REMOVE = {
    # 私信/屏蔽
    "PrivateMessage", "UserBlock",
    # 页面浏览/用户活动统计
    "PageView", "UserActivity",
    # VIP会员系统
    "VIPPlan", "VIPSubscription", "VIPFeature",
    # 邮件订阅
    "EmailSubscription",
    # 表单系统
    "Form", "FormField", "FormSubmission",
    # 电商系统
    "Product", "Cart", "CartItem", "Order", "OrderItem",
    # 广告系统
    "AdPlacement", "Ad", "AdClick", "AdImpression",
    # 收益系统
    "RevenueRecord", "RevenueSharingConfig", "PayoutRequest", "UserRevenueStats",
    # 群聊系统
    "ChatGroup", "ChatGroupMember", "ChatGroupInvite",
    # 定时报表
    "ScheduledReport", "ReportHistory",
    # 工作区/任务
    "Workspace", "WorkspaceMember", "Task",
    # 多站点
    "Site", "SiteUser", "ContentMapping",
    # 第三方分析配置
    "GoogleAnalyticsConfig", "BaiduAnalyticsConfig",
    # 通知集成
    "NotificationIntegration",
    # SSO/LDAP/SAML
    "SAMLConfig", "LDAPConfig", "SSOProvider",
    # 支付系统
    "PaymentGateway", "PaymentTransaction", "CryptoPayment", "TaxConfig",
    # 企业版
    "EnterpriseLicense", "SupportTicket", "SupportTicketReply",
    # 部署
    "DeploymentScript", "DeploymentLog",
    # 监控
    "MonitoringAlert", "MonitoringMetric",
    # 迁移
    "MigrationTask", "MigrationLog",
    # 全局样式配置(与GlobalStyle重复)
    "GlobalStyleConfig",
}

def find_model_blocks(lines):
    """找到所有模型块的起止行号"""
    blocks = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # 模型定义在 "  ModelName:" 格式（2空格缩进 + 大写字母开头）
        match = re.match(r'^  ([A-Z][a-zA-Z0-9]+):\s*$', line)
        if match:
            model_name = match.group(1)
            start = i
            # 找到该模型块的结束位置：下一个同级模型或文件末尾
            end = i + 1
            while end < len(lines):
                next_line = lines[end]
                # 遇到下一个同级模型定义或文件末尾
                if re.match(r'^  [A-Z][a-zA-Z0-9]+:\s*$', next_line):
                    break
                end += 1
            blocks.append((model_name, start, end))
            i = end
        else:
            i += 1
    return blocks

def main():
    yaml_path = "config/models.yaml"

    with open(yaml_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    print(f"原始文件: {len(lines)} 行")

    blocks = find_model_blocks(lines)
    print(f"找到 {len(blocks)} 个模型定义")

    # 找到需要删除的块
    blocks_to_remove = []
    models_found = set()
    for name, start, end in blocks:
        if name in MODELS_TO_REMOVE:
            blocks_to_remove.append((name, start, end))
            models_found.add(name)
            print(f"  将删除: {name} (行 {start+1}-{end})")

    # 检查是否有未找到的模型
    not_found = MODELS_TO_REMOVE - models_found
    if not_found:
        print(f"\n⚠️ 以下模型未在文件中找到: {not_found}")

    print(f"\n将删除 {len(blocks_to_remove)} 个模型定义")

    # 从后往前删除，避免行号偏移
    blocks_to_remove.sort(key=lambda x: x[1], reverse=True)

    new_lines = list(lines)
    for name, start, end in blocks_to_remove:
        # 也删除块前的空行（如果有）
        while start > 0 and new_lines[start - 1].strip() == '':
            start -= 1
        del new_lines[start:end]

    print(f"清理后: {len(new_lines)} 行 (删除了 {len(lines) - len(new_lines)} 行)")

    with open(yaml_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

    print(f"\n✅ 已写入 {yaml_path}")
    print(f"删除的模型: {', '.join(sorted(m[0] for m in blocks_to_remove))}")

if __name__ == "__main__":
    main()
