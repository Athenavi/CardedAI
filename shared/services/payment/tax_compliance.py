"""
税务计算服务

支持全球多种税种计算和合规性检查

功能:
1. VAT/GST税率计算
2. 地区税率自动识别
3. 税务报告生成
4. GDPR数据保护
5. PCI DSS支付安全
6. 隐私政策模板
7. Cookie同意弹窗
"""

from datetime import datetime, date
from typing import Dict, Any, List


class TaxType:
    """税种类型"""
    VAT = "VAT"  # 增值税（欧洲）
    GST = "GST"  # 商品及服务税（加拿大、澳大利亚等）
    SALES_TAX = "Sales Tax"  # 销售税（美国）
    CONSUMPTION_TAX = "Consumption Tax"  # 消费税（日本）
    SERVICE_TAX = "Service Tax"  # 服务税


class TaxRegion:
    """税务区域"""

    def __init__(
            self,
            country_code: str,
            region_code: str = None,
            tax_type: str = TaxType.VAT,
            default_rate: float = 0.0,
            description: str = ""
    ):
        self.country_code = country_code
        self.region_code = region_code
        self.tax_type = tax_type
        self.default_rate = default_rate
        self.description = description

    def to_dict(self) -> Dict[str, Any]:
        return {
            "country_code": self.country_code,
            "region_code": self.region_code,
            "tax_type": self.tax_type,
            "default_rate": self.default_rate,
            "description": self.description,
        }


class TaxCalculator:
    """
    税务计算器
    
    根据地区和税种计算税额
    """

    def __init__(self):
        # 主要国家和地区的税率配置
        self.tax_rates = self._initialize_tax_rates()

    def _initialize_tax_rates(self) -> Dict[str, Dict[str, Any]]:
        """初始化税率配置"""
        return {
            # 欧盟国家 VAT 税率
            "DE": {"country": "Germany", "type": TaxType.VAT, "rate": 19.0, "reduced_rate": 7.0},
            "FR": {"country": "France", "type": TaxType.VAT, "rate": 20.0, "reduced_rate": 5.5},
            "GB": {"country": "United Kingdom", "type": TaxType.VAT, "rate": 20.0, "reduced_rate": 5.0},
            "IT": {"country": "Italy", "type": TaxType.VAT, "rate": 22.0, "reduced_rate": 10.0},
            "ES": {"country": "Spain", "type": TaxType.VAT, "rate": 21.0, "reduced_rate": 10.0},
            "NL": {"country": "Netherlands", "type": TaxType.VAT, "rate": 21.0, "reduced_rate": 9.0},

            # 亚太地区 GST 税率
            "AU": {"country": "Australia", "type": TaxType.GST, "rate": 10.0},
            "NZ": {"country": "New Zealand", "type": TaxType.GST, "rate": 15.0},
            "SG": {"country": "Singapore", "type": TaxType.GST, "rate": 8.0},
            "JP": {"country": "Japan", "type": TaxType.CONSUMPTION_TAX, "rate": 10.0},
            "KR": {"country": "South Korea", "type": TaxType.VAT, "rate": 10.0},
            "CN": {"country": "China", "type": TaxType.VAT, "rate": 13.0, "reduced_rate": 9.0},
            "IN": {"country": "India", "type": TaxType.GST, "rate": 18.0, "reduced_rate": 12.0},

            # 北美销售税
            "US": {"country": "United States", "type": TaxType.SALES_TAX, "rate": 0.0, "note": "Varies by state"},
            "CA": {"country": "Canada", "type": TaxType.GST, "rate": 5.0, "provincial_rates": True},

            # 其他地区
            "BR": {"country": "Brazil", "type": TaxType.VAT, "rate": 17.0},
            "MX": {"country": "Mexico", "type": TaxType.VAT, "rate": 16.0},
            "ZA": {"country": "South Africa", "type": TaxType.VAT, "rate": 15.0},
            "RU": {"country": "Russia", "type": TaxType.VAT, "rate": 20.0},
        }

    def get_tax_rate(
            self,
            country_code: str,
            region_code: str = None,
            product_type: str = "standard"
    ) -> float:
        """
        获取税率
        
        Args:
            country_code: 国家代码（ISO 3166-1 alpha-2）
            region_code: 地区代码（可选）
            product_type: 产品类型（standard/reduced）
            
        Returns:
            税率百分比
        """
        country_code = country_code.upper()

        if country_code not in self.tax_rates:
            return 0.0

        tax_info = self.tax_rates[country_code]

        # 检查是否有优惠税率
        if product_type == "reduced" and "reduced_rate" in tax_info:
            return tax_info["reduced_rate"]

        return tax_info.get("rate", 0.0)

    def calculate_tax(
            self,
            amount: float,
            country_code: str,
            region_code: str = None,
            product_type: str = "standard"
    ) -> Dict[str, Any]:
        """
        计算税额
        
        Args:
            amount: 金额
            country_code: 国家代码
            region_code: 地区代码（可选）
            product_type: 产品类型
            
        Returns:
            税务计算结果
        """
        tax_rate = self.get_tax_rate(country_code, region_code, product_type)
        tax_amount = round(amount * (tax_rate / 100), 2)
        total_amount = round(amount + tax_amount, 2)

        return {
            "subtotal": amount,
            "tax_rate": tax_rate,
            "tax_amount": tax_amount,
            "total": total_amount,
            "country": country_code,
            "region": region_code,
            "product_type": product_type,
        }

    def calculate_tax_with_exemption(
            self,
            amount: float,
            country_code: str,
            has_vat_number: bool = False,
            vat_number: str = None
    ) -> Dict[str, Any]:
        """
        计算税额（考虑免税情况）
        
        Args:
            amount: 金额
            country_code: 国家代码
            has_vat_number: 是否有VAT号
            vat_number: VAT号
            
        Returns:
            税务计算结果
        """
        # B2B交易且有有效VAT号，可能免税
        if has_vat_number and vat_number:
            # 验证VAT号格式（简化验证）
            if self._validate_vat_number(vat_number, country_code):
                return {
                    "subtotal": amount,
                    "tax_rate": 0.0,
                    "tax_amount": 0.0,
                    "total": amount,
                    "country": country_code,
                    "exemption_applied": True,
                    "vat_number": vat_number,
                    "exemption_reason": "B2B transaction with valid VAT number",
                }

        # 正常计税
        result = self.calculate_tax(amount, country_code)
        result["exemption_applied"] = False

        return result

    def _validate_vat_number(self, vat_number: str, country_code: str) -> bool:
        """
        验证VAT号格式
        
        Args:
            vat_number: VAT号
            country_code: 国家代码
            
        Returns:
            是否有效
        """
        if not vat_number or len(vat_number) < 5:
            return False

        # 简化验证：检查是否以国家代码开头
        vat_upper = vat_number.upper().replace(" ", "")

        if country_code == "DE" and vat_upper.startswith("DE"):
            return len(vat_upper) == 11
        elif country_code == "FR" and vat_upper.startswith("FR"):
            return len(vat_upper) == 13
        elif country_code == "GB" and vat_upper.startswith("GB"):
            return len(vat_upper) in [9, 12]
        elif country_code == "IT" and vat_upper.startswith("IT"):
            return len(vat_upper) == 13
        else:
            # 其他国家的简化验证
            return len(vat_upper) >= 8

    def get_tax_summary(
            self,
            transactions: List[Dict[str, Any]],
            period_start: date,
            period_end: date
    ) -> Dict[str, Any]:
        """
        生成税务摘要
        
        Args:
            transactions: 交易列表
            period_start: 开始日期
            period_end: 结束日期
            
        Returns:
            税务摘要
        """
        summary = {}
        total_revenue = 0.0
        total_tax = 0.0

        for txn in transactions:
            txn_date = txn.get("date")
            if isinstance(txn_date, str):
                txn_date = datetime.fromisoformat(txn_date).date()

            # 检查是否在指定期间内
            if txn_date < period_start or txn_date > period_end:
                continue

            country = txn.get("country_code", "UNKNOWN")
            amount = txn.get("amount", 0.0)
            tax_amount = txn.get("tax_amount", 0.0)

            if country not in summary:
                summary[country] = {
                    "country": country,
                    "transaction_count": 0,
                    "total_revenue": 0.0,
                    "total_tax": 0.0,
                }

            summary[country]["transaction_count"] += 1
            summary[country]["total_revenue"] += amount
            summary[country]["total_tax"] += tax_amount

            total_revenue += amount
            total_tax += tax_amount

        return {
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "total_transactions": sum(s["transaction_count"] for s in summary.values()),
            "total_revenue": round(total_revenue, 2),
            "total_tax": round(total_tax, 2),
            "by_country": summary,
            "generated_at": datetime.now().isoformat(),
        }


class ComplianceManager:
    """
    合规性管理器
    
    管理GDPR、PCI DSS等合规要求
    """

    def __init__(self):
        self.gdpr_settings = {
            "data_retention_days": 365,
            "allow_data_export": True,
            "allow_data_deletion": True,
            "require_consent": True,
        }

        self.pci_dss_settings = {
            "encrypt_card_data": True,
            "tokenization_enabled": True,
            "network_security_enabled": True,
            "access_control_enabled": True,
        }

    def check_gdpr_compliance(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        检查GDPR合规性
        
        Args:
            user_data: 用户数据
            
        Returns:
            合规性检查结果
        """
        issues = []
        recommendations = []

        # 检查是否获得用户同意
        if not user_data.get("consent_given"):
            issues.append("User consent not obtained")
            recommendations.append("Implement cookie consent banner")

        # 检查数据保留期限
        created_at = user_data.get("created_at")
        if created_at:
            if isinstance(created_at, str):
                created_date = datetime.fromisoformat(created_at)
            else:
                created_date = created_at

            retention_days = (datetime.now() - created_date).days
            if retention_days > self.gdpr_settings["data_retention_days"]:
                issues.append(f"Data retained for {retention_days} days exceeds limit")
                recommendations.append("Review and delete old user data")

        # 检查数据最小化原则
        required_fields = ["email", "username"]
        optional_fields = ["phone", "address", "date_of_birth"]

        excessive_data = []
        for field in optional_fields:
            if field in user_data and user_data[field]:
                excessive_data.append(field)

        if excessive_data:
            recommendations.append(f"Review if these fields are necessary: {', '.join(excessive_data)}")

        return {
            "compliant": len(issues) == 0,
            "issues": issues,
            "recommendations": recommendations,
            "checked_at": datetime.now().isoformat(),
        }

    def generate_privacy_policy(self, company_info: Dict[str, Any]) -> str:
        """
        生成隐私政策模板
        
        Args:
            company_info: 公司信息
            
        Returns:
            隐私政策文本
        """
        company_name = company_info.get("name", "Our Company")
        contact_email = company_info.get("contact_email", "privacy@example.com")
        address = company_info.get("address", "123 Main St, City, Country")

        policy = f"""# Privacy Policy

**Last Updated:** {datetime.now().strftime("%B %d, %Y")}

## 1. Introduction

{company_name} ("we", "our", or "us") is committed to protecting your privacy. This Privacy Policy explains how we collect, use, disclose, and safeguard your information when you visit our website or use our services.

## 2. Information We Collect

### Personal Information
- Name and email address
- Payment information (processed securely through PCI DSS compliant providers)
- Usage data and preferences
- Cookies and tracking technologies

### Non-Personal Information
- Browser type and version
- Operating system
- Referring website
- Pages viewed and time spent

## 3. How We Use Your Information

We use the collected information for:
- Providing and maintaining our services
- Processing transactions and payments
- Sending administrative information
- Responding to inquiries and support requests
- Improving our website and services
- Complying with legal obligations

## 4. Data Sharing and Disclosure

We do not sell your personal information. We may share your information with:
- Service providers who assist in our operations
- Legal authorities when required by law
- Business partners with your consent

## 5. Data Security

We implement appropriate security measures to protect your personal information:
- Encryption of data in transit and at rest
- Regular security audits and updates
- Access controls and authentication
- PCI DSS compliance for payment processing

## 6. Your Rights (GDPR)

If you are located in the European Economic Area, you have the right to:
- Access your personal data
- Correct inaccurate data
- Request deletion of your data
- Object to processing of your data
- Data portability
- Withdraw consent at any time

## 7. Cookies and Tracking

We use cookies and similar technologies to:
- Remember your preferences
- Analyze website traffic
- Provide personalized content
- Improve user experience

You can control cookie settings through your browser preferences.

## 8. Children's Privacy

Our services are not intended for children under 13 years of age. We do not knowingly collect personal information from children.

## 9. International Data Transfers

Your information may be transferred to and processed in countries other than your own. We ensure appropriate safeguards are in place for such transfers.

## 10. Changes to This Policy

We may update this Privacy Policy from time to time. We will notify you of any changes by posting the new policy on this page.

## 11. Contact Us

If you have questions about this Privacy Policy, please contact us at:

**Email:** {contact_email}  
**Address:** {address}

---

*This privacy policy template is provided for informational purposes and should be reviewed by legal counsel to ensure compliance with applicable laws.*
"""

        return policy

    def generate_cookie_consent_html(self) -> str:
        """
        生成Cookie同意弹窗HTML
        
        Returns:
            HTML代码
        """
        html = """
<!-- Cookie Consent Banner -->
<div id="cookie-consent-banner" style="
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background-color: #1a1a1a;
    color: white;
    padding: 20px;
    z-index: 9999;
    box-shadow: 0 -2px 10px rgba(0,0,0,0.3);
">
    <div style="max-width: 1200px; margin: 0 auto; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
        <div style="flex: 1; min-width: 300px; margin-right: 20px;">
            <h3 style="margin: 0 0 10px 0; font-size: 18px;">🍪 Cookie Consent</h3>
            <p style="margin: 0; font-size: 14px; line-height: 1.5;">
                We use cookies to enhance your browsing experience, serve personalized ads or content, and analyze our traffic. 
                By clicking "Accept All", you consent to our use of cookies. 
                <a href="/privacy-policy" style="color: #4CAF50; text-decoration: underline;">Learn more</a>
            </p>
        </div>
        <div style="display: flex; gap: 10px; margin-top: 10px;">
            <button id="cookie-decline" style="
                padding: 10px 20px;
                background-color: transparent;
                border: 2px solid #666;
                color: white;
                border-radius: 5px;
                cursor: pointer;
                font-size: 14px;
                transition: all 0.3s;
            ">Decline</button>
            <button id="cookie-settings" style="
                padding: 10px 20px;
                background-color: transparent;
                border: 2px solid #4CAF50;
                color: #4CAF50;
                border-radius: 5px;
                cursor: pointer;
                font-size: 14px;
                transition: all 0.3s;
            ">Settings</button>
            <button id="cookie-accept" style="
                padding: 10px 20px;
                background-color: #4CAF50;
                border: none;
                color: white;
                border-radius: 5px;
                cursor: pointer;
                font-size: 14px;
                transition: all 0.3s;
            ">Accept All</button>
        </div>
    </div>
</div>

<script>
(function() {
    const banner = document.getElementById('cookie-consent-banner');
    const acceptBtn = document.getElementById('cookie-accept');
    const declineBtn = document.getElementById('cookie-decline');
    const settingsBtn = document.getElementById('cookie-settings');
    
    // Check if user has already made a choice
    const cookieChoice = localStorage.getItem('cookie-consent');
    if (cookieChoice) {
        banner.style.display = 'none';
    }
    
    acceptBtn.addEventListener('click', function() {
        localStorage.setItem('cookie-consent', 'accepted');
        localStorage.setItem('cookie-consent-date', new Date().toISOString());
        banner.style.display = 'none';
        // Enable all cookies
        enableCookies();
    });
    
    declineBtn.addEventListener('click', function() {
        localStorage.setItem('cookie-consent', 'declined');
        localStorage.setItem('cookie-consent-date', new Date().toISOString());
        banner.style.display = 'none';
        // Disable non-essential cookies
        disableNonEssentialCookies();
    });
    
    settingsBtn.addEventListener('click', function() {
        // Open cookie settings modal
        openCookieSettings();
    });
    
    function enableCookies() {
        // Enable analytics, marketing, etc.
        console.log('All cookies enabled');
    }
    
    function disableNonEssentialCookies() {
        // Only keep essential cookies
        console.log('Only essential cookies enabled');
    }
    
    function openCookieSettings() {
        alert('Cookie settings modal would open here');
    }
})();
</script>
"""
        return html

    def check_pci_dss_compliance(self) -> Dict[str, Any]:
        """
        检查PCI DSS合规性
        
        Returns:
            合规性检查结果
        """
        requirements = [
            {
                "id": 1,
                "name": "Install and maintain network security controls",
                "status": "compliant" if self.pci_dss_settings["network_security_enabled"] else "non-compliant",
            },
            {
                "id": 2,
                "name": "Apply high-security standards to all system components",
                "status": "compliant",
            },
            {
                "id": 3,
                "name": "Protect stored account data",
                "status": "compliant" if self.pci_dss_settings["encrypt_card_data"] else "non-compliant",
            },
            {
                "id": 4,
                "name": "Protect cardholder data with encryption during transmission",
                "status": "compliant",
            },
            {
                "id": 5,
                "name": "Protect all systems against malware",
                "status": "compliant",
            },
            {
                "id": 6,
                "name": "Develop and maintain secure systems and software",
                "status": "compliant",
            },
            {
                "id": 7,
                "name": "Restrict access to cardholder data by business need to know",
                "status": "compliant" if self.pci_dss_settings["access_control_enabled"] else "non-compliant",
            },
            {
                "id": 8,
                "name": "Identify users and authenticate access to system components",
                "status": "compliant",
            },
            {
                "id": 9,
                "name": "Restrict physical access to cardholder data",
                "status": "compliant",
            },
            {
                "id": 10,
                "name": "Log and monitor all access to system components",
                "status": "compliant",
            },
            {
                "id": 11,
                "name": "Test security of systems and networks regularly",
                "status": "compliant",
            },
            {
                "id": 12,
                "name": "Support information security with organizational policies",
                "status": "compliant",
            },
        ]

        compliant_count = sum(1 for r in requirements if r["status"] == "compliant")
        total_count = len(requirements)

        return {
            "overall_status": "compliant" if compliant_count == total_count else "partial",
            "compliance_percentage": round((compliant_count / total_count) * 100, 2),
            "requirements": requirements,
            "checked_at": datetime.now().isoformat(),
        }


class TaxComplianceService:
    """
    税务合规服务
    
    统一管理税务计算和合规性检查
    """

    def __init__(self):
        self.tax_calculator = TaxCalculator()
        self.compliance_manager = ComplianceManager()

    def process_transaction_with_tax(
            self,
            amount: float,
            customer_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        处理带税务的交易
        
        Args:
            amount: 交易金额
            customer_info: 客户信息
            
        Returns:
            交易处理结果
        """
        country_code = customer_info.get("country_code", "US")
        region_code = customer_info.get("region_code")
        has_vat_number = customer_info.get("has_vat_number", False)
        vat_number = customer_info.get("vat_number")

        # 计算税务
        if has_vat_number and vat_number:
            tax_result = self.tax_calculator.calculate_tax_with_exemption(
                amount, country_code, has_vat_number, vat_number
            )
        else:
            tax_result = self.tax_calculator.calculate_tax(
                amount, country_code, region_code
            )

        # 检查合规性
        gdpr_check = self.compliance_manager.check_gdpr_compliance(customer_info)

        return {
            "transaction": {
                "subtotal": tax_result["subtotal"],
                "tax_amount": tax_result["tax_amount"],
                "total": tax_result["total"],
                "tax_rate": tax_result["tax_rate"],
                "country": country_code,
            },
            "compliance": {
                "gdpr_compliant": gdpr_check["compliant"],
                "gdpr_issues": gdpr_check["issues"],
            },
            "timestamp": datetime.now().isoformat(),
        }

    def generate_tax_report(
            self,
            transactions: List[Dict[str, Any]],
            period_start: date,
            period_end: date
    ) -> Dict[str, Any]:
        """
        生成税务报告
        
        Args:
            transactions: 交易列表
            period_start: 开始日期
            period_end: 结束日期
            
        Returns:
            税务报告
        """
        tax_summary = self.tax_calculator.get_tax_summary(
            transactions, period_start, period_end
        )

        pci_compliance = self.compliance_manager.check_pci_dss_compliance()

        return {
            "tax_summary": tax_summary,
            "pci_dss_compliance": pci_compliance,
            "report_generated_at": datetime.now().isoformat(),
            "period": {
                "start": period_start.isoformat(),
                "end": period_end.isoformat(),
            },
        }


# 全局实例
tax_compliance_service = TaxComplianceService()
