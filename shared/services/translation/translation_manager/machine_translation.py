"""
机器翻译服务
支持多个翻译提供商：百度、有道、DeepL 等
"""

import asyncio
import hashlib
import os
import random
import time
import uuid
from typing import Dict, List, Any, Optional

import httpx

# 翻译提供商配置
TRANSLATION_PROVIDERS = {
    "baidu": {
        "name": "百度翻译",
        "api_url": "https://fanyi-api.baidu.com/api/trans/vip/translate",
        "requires_key": True
    },
    "youdao": {
        "name": "有道翻译",
        "api_url": "https://openapi.youdao.com/api",
        "requires_key": True
    },
    "deepl": {
        "name": "DeepL",
        "api_url": "https://api-free.deepl.com/v2/translate",
        "requires_key": True
    }
}

# 百度翻译语言映射
BAIDU_LANG_MAP = {
    "en": "en", "zh-CN": "zh", "zh-TW": "cht", "ja": "jp", "ko": "kor",
    "fr": "fra", "de": "de", "es": "spa", "ru": "ru", "ar": "ara"
}

# API 密钥环境变量
API_KEYS = {
    "baidu": ("BAIDU_TRANSLATE_APP_ID", "BAIDU_TRANSLATE_SECRET_KEY"),
    "youdao": ("YOUDAO_TRANSLATE_APP_KEY", "YOUDAO_TRANSLATE_APP_SECRET"),
    "deepl": ("DEEPL_AUTH_KEY", None)
}


class MachineTranslationService:
    """
    机器翻译服务
    
    支持的提供商:
    1. 百度翻译
    2. 有道翻译
    3. DeepL
    4. Google Translate (预留)
    
    功能:
    1. 自动翻译草稿
    2. 批量翻译
    3. 翻译记忆库
    4. 人工校对工作流
    """
    
    def __init__(self):
        self.providers = TRANSLATION_PROVIDERS
        self.translation_memory = {}
    
    async def translate_text(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        provider: str = "baidu",
        api_key: Optional[str] = None,
        secret_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """翻译文本"""
        if provider not in self.providers:
            return {"success": False, "error": f"不支持的翻译提供商: {provider}"}
        
        memory_key = f"{source_lang}_{target_lang}_{hashlib.md5(text.encode()).hexdigest()}"
        if memory_key in self.translation_memory:
            return {
                "success": True,
                "translated_text": self.translation_memory[memory_key],
                "from_cache": True,
                "provider": provider
            }
        
        try:
            if provider == "baidu":
                result = await self._translate_with_baidu(text, source_lang, target_lang, api_key, secret_key)
            elif provider == "youdao":
                result = await self._translate_with_youdao(text, source_lang, target_lang, api_key, secret_key)
            elif provider == "deepl":
                result = await self._translate_with_deepl(text, source_lang, target_lang, api_key)
            else:
                result = {"success": False, "error": "未实现的提供商"}
            
            if result["success"]:
                self.translation_memory[memory_key] = result["translated_text"]
            
            return result
        except Exception as e:
            return {"success": False, "error": f"翻译失败: {str(e)}"}
    
    async def batch_translate(
        self,
        texts: List[str],
        source_lang: str,
        target_lang: str,
        provider: str = "baidu",
        api_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        delay_between_requests: float = 1.0
    ) -> Dict[str, Any]:
        """批量翻译"""
        results = []
        success_count = 0
        failed_count = 0
        
        for i, text in enumerate(texts):
            if i > 0:
                await asyncio.sleep(delay_between_requests)
            
            result = await self.translate_text(
                text=text, source_lang=source_lang, target_lang=target_lang,
                provider=provider, api_key=api_key, secret_key=secret_key
            )
            
            results.append({
                "original": text,
                "translated": result.get("translated_text", ""),
                "success": result["success"],
                "error": result.get("error")
            })
            
            if result["success"]:
                success_count += 1
            else:
                failed_count += 1
        
        return {
            "success": failed_count == 0,
            "total": len(texts),
            "success_count": success_count,
            "failed_count": failed_count,
            "results": results
        }
    
    async def _translate_with_baidu(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        app_id: Optional[str] = None,
        secret_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """使用百度翻译"""
        app_id = app_id or os.getenv(API_KEYS["baidu"][0], "")
        secret_key = secret_key or os.getenv(API_KEYS["baidu"][1], "")
        
        if not app_id or not secret_key:
            return {"success": False, "error": "未配置百度翻译 API 密钥"}
        
        salt = str(random.randint(32768, 65536))
        sign = hashlib.md5(f"{app_id}{text}{salt}{secret_key}".encode('utf-8')).hexdigest()
        
        params = {
            "q": text,
            "from": self._convert_to_baidu_lang(source_lang),
            "to": self._convert_to_baidu_lang(target_lang),
            "appid": app_id,
            "salt": salt,
            "sign": sign
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(self.providers["baidu"]["api_url"], params=params)
            
            if response.status_code != 200:
                return {"success": False, "error": f"API 请求失败: {response.status_code}"}
            
            data = response.json()
            
            if "error_code" in data:
                return {"success": False, "error": f"百度翻译错误: {data.get('error_msg', '未知错误')}"}

            translated_text = "\n".join(item["dst"] for item in data.get("trans_result", []))
            
            return {
                "success": True,
                "translated_text": translated_text,
                "from_cache": False,
                "provider": "baidu"
            }
    
    async def _translate_with_youdao(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        app_key: Optional[str] = None,
        app_secret: Optional[str] = None
    ) -> Dict[str, Any]:
        """使用有道翻译"""
        app_key = app_key or os.getenv(API_KEYS["youdao"][0], "")
        app_secret = app_secret or os.getenv(API_KEYS["youdao"][1], "")
        
        if not app_key or not app_secret:
            return {"success": False, "error": "未配置有道翻译 API 密钥"}
        
        curtime = str(int(time.time()))
        salt = str(uuid.uuid1())
        sign = hashlib.sha256(
            f"{app_key}{self._truncate_text(text)}{salt}{curtime}{app_secret}".encode('utf-8')).hexdigest()
        
        params = {
            "q": text,
            "from": source_lang,
            "to": target_lang,
            "appKey": app_key,
            "salt": salt,
            "sign": sign,
            "signType": "v3",
            "curtime": curtime
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(self.providers["youdao"]["api_url"], params=params)
            
            if response.status_code != 200:
                return {"success": False, "error": f"API 请求失败: {response.status_code}"}
            
            data = response.json()
            
            if data.get("errorCode") != "0":
                return {"success": False, "error": f"有道翻译错误: {data.get('errorCode', '未知错误')}"}

            translated_text = "\n".join(data.get("translation", []))
            
            return {
                "success": True,
                "translated_text": translated_text,
                "from_cache": False,
                "provider": "youdao"
            }
    
    async def _translate_with_deepl(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        auth_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """使用 DeepL 翻译"""
        auth_key = auth_key or os.getenv(API_KEYS["deepl"][0], "")
        
        if not auth_key:
            return {"success": False, "error": "未配置 DeepL API 密钥"}
        
        target_lang = target_lang.upper().split('-')[0]
        data = {"text": [text], "target_lang": target_lang}
        
        if source_lang:
            data["source_lang"] = source_lang.upper().split('-')[0]
        
        headers = {
            "Authorization": f"DeepL-Auth-Key {auth_key}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.providers["deepl"]["api_url"],
                json=data,
                headers=headers
            )
            
            if response.status_code != 200:
                return {"success": False, "error": f"API 请求失败: {response.status_code} - {response.text}"}
            
            result = response.json()
            
            if "translations" not in result:
                return {"success": False, "error": "DeepL 返回格式错误"}
            
            return {
                "success": True,
                "translated_text": result["translations"][0]["text"],
                "from_cache": False,
                "provider": "deepl"
            }
    
    def get_translation_memory_stats(self) -> Dict[str, Any]:
        """获取翻译记忆库统计"""
        return {
            "total_entries": len(self.translation_memory),
            "memory_size_kb": len(str(self.translation_memory).encode('utf-8')) / 1024
        }
    
    def clear_translation_memory(self):
        """清空翻译记忆库"""
        self.translation_memory.clear()
        return {"success": True, "message": "翻译记忆库已清空"}
    
    def _convert_to_baidu_lang(self, lang_code: str) -> str:
        """转换为百度翻译语言代码"""
        return BAIDU_LANG_MAP.get(lang_code, lang_code)
    
    def _truncate_text(self, text: str, max_length: int = 20) -> str:
        """截断文本用于签名"""
        if len(text) <= max_length:
            return text
        return text[:10] + str(len(text)) + text[-10:]


# 全局实例
machine_translation_service = MachineTranslationService()
