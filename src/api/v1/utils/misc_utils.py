"""
杂项工具函数
"""
import random


def generate_random_text(length=4):
    """生成随机的验证码文本"""
    characters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    captcha_text = ''.join(random.choice(characters) for _ in range(length))
    return captcha_text
