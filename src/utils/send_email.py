import smtplib
import uuid
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from src.setting import app_config


async def request_email_change(user_id, cache_instance, domain, new_email):
    # 生成唯一令牌
    token = str(uuid.uuid4())
    temp_email_value = {
        'token': token,
        'new_email': new_email
    }

    cache_instance.set(f"temp_email_{user_id}", temp_email_value, timeout=600)

    # 生成临时访问链接 (实际应用中应通过邮件发送)
    temp_link = f'{domain}api/change-email/confirm/{token}'
    if await api_mail(user_id=user_id,
                      body_content=f'您可以通过点击如下的链接来完成邮箱更新\n\n{temp_link}\n\n如果不是您发起的请求，请忽略该邮件'):
        print(temp_link)


# 获取邮件配置
def get_mail_config():
    mail_username = getattr(app_config, 'MAIL_USERNAME', '')
    mail_from_address = getattr(app_config, 'MAIL_FROM_ADDRESS', None) or getattr(app_config, 'MAIL_USERNAME', None)

    # 如果mail_from_address仍然为空，使用一个默认的有效邮箱地址
    if not mail_from_address or mail_from_address.strip() == '' or mail_from_address == '':
        mail_from_address = "noreply@example.com"  # 默认值，必须是一个有效的邮箱地址

    config = {
        'MAIL_USERNAME': mail_username,
        'MAIL_PASSWORD': getattr(app_config, 'MAIL_PASSWORD', ''),
        'MAIL_FROM': mail_from_address,  # 发送者邮箱
        'MAIL_PORT': getattr(app_config, 'MAIL_PORT', 587),
        'MAIL_SERVER': getattr(app_config, 'MAIL_SERVER', 'smtp.gmail.com'),
        'MAIL_STARTTLS': True,
        'MAIL_SSL_TLS': False
    }
    return config


async def api_mail(user_id, body_content, site_name='系统通知', recipient: Optional[str] = None):
    config = get_mail_config()

    subject = f'{site_name} - 通知邮件'
    body = body_content + "\n\n\n此邮件为系统自动发送，请勿回复。"

    # 如果没有指定收件人，使用配置中的邮箱
    recipient_email = recipient if recipient else app_config.MAIL_USERNAME

    # 创建邮件
    msg = MIMEMultipart()
    msg['From'] = config['MAIL_FROM']
    msg['To'] = recipient_email
    msg['Subject'] = subject

    # 添加邮件正文
    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    # 发送邮件
    try:
        # 创建SMTP连接
        server = smtplib.SMTP(config['MAIL_SERVER'], config['MAIL_PORT'])

        if config['MAIL_STARTTLS']:
            server.starttls()

        # 登录并发送邮件
        server.login(config['MAIL_USERNAME'], config['MAIL_PASSWORD'])
        text = msg.as_string()
        server.sendmail(config['MAIL_FROM'], recipient_email, text)
        server.quit()

        print(f"邮件派送人: {user_id if user_id != 0 else '系统'}")
        return True
    except Exception as e:
        print(f"邮件发送失败: {str(e)}")
        return False
