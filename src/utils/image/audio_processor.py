"""
音频文件处理工具
支持从音频文件中提取封面图片（ID3标签）
"""
import io

from typing import Optional, Tuple

from src.unified_logger import default_logger as logger


def extract_audio_cover(audio_path: str) -> Optional[bytes]:
    """
    从音频文件中提取封面图片
    
    Args:
        audio_path: 音频文件路径
        
    Returns:
        封面图片的字节数据，如果没有封面则返回 None
    """
    try:
        from mutagen import File as MutagenFile
        from mutagen.id3 import ID3
        from mutagen.mp3 import MP3
        from mutagen.flac import FLAC
        from mutagen.mp4 import MP4
        from mutagen.oggvorbis import OggVorbis
        from mutagen.oggopus import OggOpus
        
        # 尝试不同的音频格式
        audio_file = None
        lower_path = audio_path.lower()
        
        if lower_path.endswith('.mp3'):
            audio_file = MP3(audio_path)
        elif lower_path.endswith('.flac'):
            audio_file = FLAC(audio_path)
        elif lower_path.endswith(('.m4a', '.mp4', '.aac')):
            audio_file = MP4(audio_path)
        elif lower_path.endswith('.ogg'):
            try:
                audio_file = OggVorbis(audio_path)
            except:
                audio_file = OggOpus(audio_path)
        else:
            # 尝试通用方法
            audio_file = MutagenFile(audio_path)
        
        if not audio_file:
            logger.warning(f"无法识别音频文件格式: {audio_path}")
            return None
        
        cover_data = None
        
        # MP3 格式 (ID3 标签)
        if hasattr(audio_file, 'tags') and isinstance(audio_file.tags, ID3):
            # 查找 APIC 帧（Attached Picture）
            for tag in audio_file.tags.values():
                if tag.FrameID == 'APIC':
                    cover_data = tag.data
                    logger.info(f"从 MP3 文件中提取到封面图片，大小: {len(cover_data)} bytes")
                    break
        
        # FLAC 格式
        elif hasattr(audio_file, 'pictures') and audio_file.pictures:
            # FLAC 可能有多个图片，取第一个
            cover_data = audio_file.pictures[0].data
            logger.info(f"从 FLAC 文件中提取到封面图片，大小: {len(cover_data)} bytes")
        
        # MP4/M4A 格式
        elif hasattr(audio_file, 'tags') and 'covr' in audio_file.tags:
            covers = audio_file.tags['covr']
            if covers:
                cover_data = bytes(covers[0])
                logger.info(f"从 MP4/M4A 文件中提取到封面图片，大小: {len(cover_data)} bytes")
        
        # OGG Vorbis/Opus 格式
        elif hasattr(audio_file, 'tags') and audio_file.tags:
            # OGG 通常使用 METADATA_BLOCK_PICTURE
            # 这里简化处理，实际可能需要更复杂的解析
            logger.debug(f"OGG 格式暂不支持封面提取")
        
        if cover_data:
            logger.info(f"成功从音频文件提取封面: {audio_path}")
            return cover_data
        else:
            logger.debug(f"音频文件没有嵌入封面: {audio_path}")
            return None
            
    except ImportError:
        logger.error("mutagen 库未安装，请运行: pip install mutagen")
        return None
    except Exception as e:
        logger.error(f"提取音频封面失败: {audio_path}, 错误: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return None


def create_audio_thumbnail(audio_path: str, thumbnail_path: str, size: Tuple[int, int] = (200, 200)) -> bool:
    """
    为音频文件创建缩略图（从封面提取）
    
    Args:
        audio_path: 音频文件路径
        thumbnail_path: 缩略图保存路径
        size: 缩略图尺寸 (width, height)
        
    Returns:
        是否成功创建缩略图
    """
    try:
        from PIL import Image
        
        # 提取封面
        cover_data = extract_audio_cover(audio_path)
        if not cover_data:
            logger.info(f"音频文件没有封面，生成默认缩略图: {audio_path}")
            # 生成默认的音乐图标缩略图
            return _create_default_audio_thumbnail(thumbnail_path, size)
        
        # 将封面数据转换为 PIL Image
        try:
            img = Image.open(io.BytesIO(cover_data))
        except Exception as e:
            logger.warning(f"封面数据无法解析为图片: {e}，生成默认缩略图")
            return _create_default_audio_thumbnail(thumbnail_path, size)
        
        # 调整大小为正方形缩略图
        img.thumbnail(size, Image.Resampling.LANCZOS)
        
        # 如果不是 RGB 模式，转换
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # 保存为 JPEG
        img.save(thumbnail_path, 'JPEG', quality=85, optimize=True)
        
        logger.info(f"音频缩略图生成成功: {thumbnail_path}")
        return True
        
    except Exception as e:
        logger.error(f"创建音频缩略图失败: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return False


def _create_default_audio_thumbnail(thumbnail_path: str, size: Tuple[int, int] = (200, 200)) -> bool:
    """
    创建默认的音频缩略图（音乐图标）
    
    Args:
        thumbnail_path: 缩略图保存路径
        size: 缩略图尺寸
        
    Returns:
        是否成功创建
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        width, height = size
        # 创建渐变背景
        img = Image.new('RGB', (width, height), color=(100, 100, 150))
        draw = ImageDraw.Draw(img)
        
        # 绘制圆形背景
        margin = 20
        draw.ellipse([margin, margin, width - margin, height - margin], 
                     fill=(70, 70, 120))
        
        # 绘制音符符号（简化的♪）
        try:
            font = ImageFont.truetype("arial.ttf", 60)
        except:
            font = ImageFont.load_default()
        
        # 计算文字位置（居中）
        text = "♪"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (width - text_width) // 2
        y = (height - text_height) // 2 - 10
        
        # 绘制音符
        draw.text((x, y), text, fill=(255, 255, 255), font=font)
        
        # 保存
        img.save(thumbnail_path, 'JPEG', quality=85, optimize=True)
        
        logger.info(f"默认音频缩略图生成成功: {thumbnail_path}")
        return True
        
    except Exception as e:
        logger.error(f"创建默认音频缩略图失败: {e}")
        return False


if __name__ == "__main__":
    # 测试
    import sys
    
    if len(sys.argv) > 1:
        audio_file = sys.argv[1]
        output_file = "test_audio_thumb.jpg"
        
        print(f"测试音频封面提取: {audio_file}")
        success = create_audio_thumbnail(audio_file, output_file)
        
        if success:
            print(f"✅ 缩略图已保存到: {output_file}")
        else:
            print("❌ 缩略图生成失败")
    else:
        print("用法: python audio_processor.py <audio_file>")
