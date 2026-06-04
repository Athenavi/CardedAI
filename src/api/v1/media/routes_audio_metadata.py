"""
音频元数据API路由
提供音频文件的封面图片和歌词信息
"""
import base64
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.media import Media
from src.auth.auth_deps import jwt_required_dependency as jwt_required
from src.extensions import get_async_db_session as get_async_db
from src.unified_logger import default_logger as logger

router = APIRouter(tags=["audio-metadata"])


@router.get("/{media_id}/metadata")
async def get_audio_metadata(
        media_id: int,
        current_user_obj=Depends(jwt_required),
        db: AsyncSession = Depends(get_async_db)
):
    """
    获取音频文件的元数据（封面、歌词等）

    Args:
        media_id: 媒体文件ID

    Returns:
        包含封面图片(base64)和歌词的JSON数据
    """
    try:
        # 查询媒体文件
        media_query = select(Media).where(Media.id == media_id)
        media_result = await db.execute(media_query)
        media = media_result.scalar_one_or_none()

        if not media:
            raise HTTPException(status_code=404, detail="媒体文件不存在")

        # 检查权限
        if media.user != current_user_obj.id and not media.is_public:
            raise HTTPException(status_code=403, detail="无权访问该媒体文件")

        # 检查是否为音频文件
        if not media.mime_type or not media.mime_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="不是音频文件")

        result = {
            "success": True,
            "data": {
                "cover_image": None,  # base64编码的封面图片
                "lyrics": [],  # 歌词数组 [{time: 秒, text: 文本}]
                "title": media.original_filename,
                "duration": media.duration
            }
        }

        # 提取封面图片
        cover_data = extract_cover_from_audio(media)
        if cover_data:
            # 转换为base64
            cover_base64 = base64.b64encode(cover_data).decode('utf-8')
            # 检测图片格式
            mime_type = detect_image_mime_type(cover_data)
            result["data"]["cover_image"] = f"data:{mime_type};base64,{cover_base64}"
            logger.info(f"成功提取音频封面: media_id={media_id}")

        # 提取歌词
        lyrics = extract_lyrics_from_audio(media)
        if lyrics:
            result["data"]["lyrics"] = lyrics
            logger.info(f"成功提取音频歌词: media_id={media_id}, 共{len(lyrics)}行")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取音频元数据失败: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


def extract_cover_from_audio(media: Media) -> Optional[bytes]:
    """从音频文件中提取封面图片"""
    try:
        from src.utils.image.audio_processor import extract_audio_cover

        # 获取文件路径
        file_path = media.file_path
        if not file_path:
            return None

        # 如果是S3路径，需要先下载到临时文件
        if file_path.startswith('s3://'):
            try:
                import tempfile
                import boto3
                from src.config import settings

                # 解析 S3 路径 (s3://bucket/key)
                parts = file_path.replace('s3://', '').split('/', 1)
                bucket = parts[0]
                key = parts[1] if len(parts) > 1 else ''

                # 从配置获取 AWS 凭据
                s3_client = boto3.client(
                    's3',
                    aws_access_key_id=getattr(settings, 'AWS_ACCESS_KEY_ID', None),
                    aws_secret_access_key=getattr(settings, 'AWS_SECRET_ACCESS_KEY', None),
                    region_name=getattr(settings, 'AWS_REGION', 'us-east-1'),
                )

                with tempfile.NamedTemporaryFile(suffix='.tmp', delete=False) as tmp_file:
                    s3_client.download_file(bucket, key, tmp_file.name)
                    result = extract_audio_cover(tmp_file.name)

                    import os
                    os.unlink(tmp_file.name)
                    return result
            except Exception as e:
                logger.error(f"S3文件下载失败: {e}")
                return None

        # 本地文件直接提取
        full_path = Path('storage/' + file_path)
        if full_path.exists():
            return extract_audio_cover(str(full_path))
        else:
            logger.warning(f"音频文件不存在: {full_path}")
            return None

    except ImportError:
        logger.error("mutagen库未安装")
        return None
    except Exception as e:
        logger.error(f"提取封面失败: {e}")
        return None


def extract_lyrics_from_audio(media: Media) -> list:
    """从音频文件的ID3标签中提取歌词（USLT帧）"""
    try:
        # 方法2: 从音频元数据中提取USLT帧（同步歌词）
        lyrics = extract_lyrics_from_id3(media)
        if lyrics:
            return lyrics

        # 方法1: 查找同名的.lrc文件（备用方案）
        # lrc_path = find_lrc_file(media)
        # if lrc_path:
        #     return parse_lrc_file(lrc_path)

        return []

    except Exception as e:
        logger.error(f"提取歌词失败: {e}")
        return []


def extract_lyrics_from_id3(media: Media) -> list:
    """从音频文件的ID3标签中提取USLT帧（同步歌词）"""
    try:
        from mutagen import File as MutagenFile
        from mutagen.id3 import ID3, USLT
        from mutagen.mp3 import MP3

        # 获取文件路径
        file_path = media.file_path
        if not file_path:
            return []

        # 仅支持本地文件
        if file_path.startswith('s3://'):
            logger.warning("S3存储的音频文件暂不支持歌词提取")
            return []

        full_path = Path("storage/" + file_path)
        if not full_path.exists():
            logger.warning(f"音频文件不存在: {full_path}")
            return []

        # 尝试读取ID3标签
        audio_file = None
        lower_path = file_path.lower()

        if lower_path.endswith('.mp3'):
            audio_file = MP3(str(full_path))
        else:
            # 尝试通用方法
            audio_file = MutagenFile(str(full_path))

        if not audio_file or not hasattr(audio_file, 'tags'):
            logger.debug(f"音频文件没有ID3标签: {file_path}")
            return []

        lyrics_list = []

        # 查找USLT帧（Unsynchronized Lyrics Text）
        for tag in audio_file.tags.values():
            if isinstance(tag, USLT):
                # USLT帧包含纯文本歌词
                lyric_text = tag.text
                if lyric_text:
                    # 尝试解析LRC格式的时间戳
                    parsed_lyrics = parse_lrc_text(lyric_text)
                    if parsed_lyrics:
                        lyrics_list.extend(parsed_lyrics)
                    else:
                        # 如果没有时间戳，将整个文本作为单行歌词
                        lyrics_list.append({
                            "time": 0.0,
                            "text": lyric_text.strip()
                        })
                    logger.info(f"从ID3标签提取到歌词: {len(lyric_text)} 字符")

        # 按时间排序
        if lyrics_list:
            lyrics_list.sort(key=lambda x: x["time"])
            logger.info(f"成功从ID3标签提取歌词: {len(lyrics_list)} 行")

        return lyrics_list

    except ImportError:
        logger.error("mutagen库未安装")
        return []
    except Exception as e:
        logger.error(f"从ID3提取歌词失败: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return []


def parse_lrc_text(text: str) -> list:
    """解析包含LRC时间戳的歌词文本"""
    try:
        import re
        lyrics = []

        # 按行分割
        lines = text.split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # LRC格式: [mm:ss.xx]歌词文本
            pattern = r'\[(\d{2}):(\d{2})\.(\d{2,3})\](.*)'
            matches = re.findall(pattern, line)

            for match in matches:
                minutes = int(match[0])
                seconds = int(match[1])
                milliseconds = int(match[2].ljust(3, '0'))  # 补齐3位
                lyric_text = match[3].strip()

                if lyric_text:  # 只添加有文本的行
                    time_in_seconds = minutes * 60 + seconds + milliseconds / 1000
                    lyrics.append({
                        "time": round(time_in_seconds, 2),
                        "text": lyric_text
                    })

        return lyrics

    except Exception as e:
        logger.error(f"解析LRC文本失败: {e}")
        return []


def find_lrc_file(media: Media) -> Optional[Path]:
    """查找与音频文件同名的.lrc歌词文件"""
    try:
        audio_path = Path(media.file_path)
        if not audio_path.exists():
            return None

        # 查找同名.lrc文件
        lrc_path = audio_path.with_suffix('.lrc')
        if lrc_path.exists():
            return lrc_path

        # 在相同目录下查找可能的歌词文件
        parent_dir = audio_path.parent
        base_name = audio_path.stem

        # 尝试几种常见的命名方式
        possible_names = [
            f"{base_name}.lrc",
            f"{base_name}.txt",
            f"lyrics_{base_name}.lrc",
        ]

        for name in possible_names:
            candidate = parent_dir / name
            if candidate.exists():
                return candidate

        return None

    except Exception as e:
        logger.error(f"查找歌词文件失败: {e}")
        return None


def parse_lrc_file(lrc_path: Path) -> list:
    """解析LRC格式的歌词文件"""
    try:
        lyrics = []

        with open(lrc_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                # LRC格式: [mm:ss.xx]歌词文本 或 [mm:ss.xx][mm:ss.xx]歌词文本
                import re
                pattern = r'\[(\d{2}):(\d{2})\.(\d{2,3})\](.*)'
                matches = re.findall(pattern, line)

                for match in matches:
                    minutes = int(match[0])
                    seconds = int(match[1])
                    milliseconds = int(match[2].ljust(3, '0'))  # 补齐3位
                    text = match[3].strip()

                    if text:  # 只添加有文本的行
                        time_in_seconds = minutes * 60 + seconds + milliseconds / 1000
                        lyrics.append({
                            "time": round(time_in_seconds, 2),
                            "text": text
                        })

        # 按时间排序
        lyrics.sort(key=lambda x: x["time"])

        return lyrics

    except Exception as e:
        logger.error(f"解析LRC文件失败: {lrc_path}, 错误: {e}")
        return []


def detect_image_mime_type(image_data: bytes) -> str:
    """检测图片数据的MIME类型"""
    if len(image_data) < 4:
        return "image/jpeg"  # 默认

    # 检查文件头
    if image_data[:3] == b'\xff\xd8\xff':
        return "image/jpeg"
    elif image_data[:4] == b'\x89PNG':
        return "image/png"
    elif image_data[:4] == b'RIFF' and image_data[8:12] == b'WEBP':
        return "image/webp"
    elif image_data[:2] == b'BM':
        return "image/bmp"
    else:
        return "image/jpeg"  # 默认JPEG
