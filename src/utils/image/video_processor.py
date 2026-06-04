"""
视频处理工具
支持视频转码、缩略图提取等功能
需要安装ffmpeg才能使用
"""

import os
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List

from src.unified_logger import default_logger as logger


class VideoProcessor:
    """视频处理器，使用ffmpeg进行视频处理"""

    def __init__(self, ffmpeg_path: Optional[str] = None):
        """
        初始化视频处理器
        
        Args:
            ffmpeg_path: ffmpeg可执行文件路径，如果为None则从PATH中查找
        """
        # 优先使用传入的路径，其次使用配置文件中的路径
        if ffmpeg_path is None:
            try:
                from src.setting import app_config
                self.ffmpeg_path = getattr(app_config, 'FFMPEG_PATH', 'ffmpeg')
                self.ffprobe_path = getattr(app_config, 'FFPROBE_PATH', 'ffprobe')
            except Exception:
                self.ffmpeg_path = 'ffmpeg'
                self.ffprobe_path = 'ffprobe'
        else:
            self.ffmpeg_path = ffmpeg_path
            self.ffprobe_path = ffmpeg_path.replace('ffmpeg', 'ffprobe') if 'ffmpeg' in ffmpeg_path else 'ffprobe'

        # 检查ffmpeg是否可用
        if not self._check_ffmpeg():
            logger.warning("FFmpeg 未安装或不可用，视频处理功能将被禁用")

    def _check_ffmpeg(self) -> bool:
        """检查ffmpeg是否可用"""
        try:
            result = subprocess.run(
                [self.ffmpeg_path, '-version'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def get_video_info(self, video_path: str) -> Optional[Dict[str, Any]]:
        """
        获取视频信息
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            包含视频信息的字典，包括：duration, width, height, codec, fps等
        """
        try:
            cmd = [
                self.ffprobe_path,
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                video_path
            ]

            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30,
                encoding='utf-8'
            )

            if result.returncode != 0:
                logger.error(f"ffprobe 执行失败: {result.stderr}")
                return None

            import json
            info = json.loads(result.stdout)

            # 提取视频流信息
            video_stream = None
            for stream in info.get('streams', []):
                if stream.get('codec_type') == 'video':
                    video_stream = stream
                    break

            if not video_stream:
                logger.error("未找到视频流")
                return None

            format_info = info.get('format', {})

            return {
                'duration': float(format_info.get('duration', 0)),
                'width': int(video_stream.get('width', 0)),
                'height': int(video_stream.get('height', 0)),
                'codec': video_stream.get('codec_name', ''),
                'fps': eval(video_stream.get('r_frame_rate', '0/1')),
                'bitrate': int(format_info.get('bit_rate', 0)),
                'file_size': int(format_info.get('size', 0)),
            }

        except Exception as e:
            logger.error(f"获取视频信息失败: {str(e)}")
            return None

    def create_thumbnail(
            self,
            video_path: str,
            thumbnail_path: str,
            time: float = 1.0,
            width: int = 320,
            quality: int = 85
    ) -> bool:
        """
        从视频中提取缩略图
        
        Args:
            video_path: 视频文件路径
            thumbnail_path: 缩略图保存路径
            time: 提取时间点（秒）
            width: 缩略图宽度（高度自动计算保持比例）
            quality: JPEG质量 (1-100)
            
        Returns:
            是否成功
        """
        try:
            # 确保输出目录存在
            os.makedirs(os.path.dirname(thumbnail_path), exist_ok=True)

            cmd = [
                self.ffmpeg_path,
                '-i', video_path,
                '-ss', str(time),  # 时间点
                '-vframes', '1',  # 只提取一帧
                '-vf', f'scale={width}:-1',  # 缩放
                '-q:v', str(int(quality / 10)),  # JPEG质量
                '-y',  # 覆盖输出文件
                thumbnail_path
            ]

            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=60
            )

            if result.returncode != 0:
                logger.error(f"ffmpeg 缩略图提取失败: {result.stderr.decode()}")
                return False

            # 验证输出文件
            if os.path.exists(thumbnail_path) and os.path.getsize(thumbnail_path) > 0:
                logger.info(f"成功创建视频缩略图: {thumbnail_path}")
                return True
            else:
                logger.error("缩略图文件创建失败")
                return False

        except subprocess.TimeoutExpired:
            logger.error("视频缩略图提取超时")
            return False
        except Exception as e:
            logger.error(f"创建视频缩略图失败: {str(e)}")
            return False

    def transcode_video(
            self,
            input_path: str,
            output_path: str,
            preset: str = 'medium',
            crf: int = 23,
            max_width: Optional[int] = None,
            max_height: Optional[int] = None,
            audio_bitrate: str = '128k',
            video_codec: str = 'libx264',
            container: str = 'mp4'
    ) -> Dict[str, Any]:
        """
        转码视频
        
        Args:
            input_path: 输入视频路径
            output_path: 输出视频路径
            preset: x264预设 (ultrafast, fast, medium, slow, veryslow)
            crf: 恒定质量因子 (18-28, 越小质量越高)
            max_width: 最大宽度（可选，保持比例）
            max_height: 最大高度（可选，保持比例）
            audio_bitrate: 音频比特率
            video_codec: 视频编码器
            container: 容器格式 (mp4, webm等)
            
        Returns:
            包含转码结果的字典
        """
        try:
            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # 构建滤镜参数
            filter_params = []
            if max_width or max_height:
                scale_filter = 'scale='
                if max_width and max_height:
                    scale_filter += f'min({max_width}\\,iw*{max_height}/ih):min({max_height}\\,ih*{max_width}/iw)'
                elif max_width:
                    scale_filter += f'{max_width}:-1'
                else:
                    scale_filter += f'-1:{max_height}'
                filter_params.append(scale_filter)

            # 构建命令
            cmd = [
                self.ffmpeg_path,
                '-i', input_path,
                '-c:v', video_codec,
                '-preset', preset,
                '-crf', str(crf),
            ]

            # 添加滤镜
            if filter_params:
                cmd.extend(['-vf', ','.join(filter_params)])

            # 音频设置
            cmd.extend([
                '-c:a', 'aac',
                '-b:a', audio_bitrate,
                '-movflags', '+faststart',  # Web优化
                '-y',  # 覆盖输出
                output_path
            ])

            logger.info(f"开始转码视频: {input_path} -> {output_path}")

            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=600  # 10分钟超时
            )

            if result.returncode != 0:
                error_msg = result.stderr.decode()
                logger.error(f"视频转码失败: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg
                }

            # 验证输出文件
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                original_size = os.path.getsize(input_path)
                transcoded_size = os.path.getsize(output_path)
                compression_ratio = (1 - transcoded_size / original_size) * 100 if original_size > 0 else 0

                logger.info(f"视频转码成功: {output_path}")
                logger.info(f"原始大小: {original_size / 1024 / 1024:.2f}MB, "
                            f"转码后: {transcoded_size / 1024 / 1024:.2f}MB, "
                            f"压缩率: {compression_ratio:.2f}%")

                return {
                    'success': True,
                    'output_path': output_path,
                    'original_size': original_size,
                    'transcoded_size': transcoded_size,
                    'compression_ratio': round(compression_ratio, 2)
                }
            else:
                return {
                    'success': False,
                    'error': '输出文件不存在或为空'
                }

        except subprocess.TimeoutExpired:
            logger.error("视频转码超时")
            return {
                'success': False,
                'error': '转码超时'
            }
        except Exception as e:
            logger.error(f"视频转码失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def generate_multiple_resolutions(
            self,
            input_path: str,
            output_dir: str,
            resolutions: Optional[List[Dict[str, int]]] = None
    ) -> List[Dict[str, Any]]:
        """
        生成多种分辨率的视频版本
        
        Args:
            input_path: 输入视频路径
            output_dir: 输出目录
            resolutions: 分辨率列表，例如 [{'width': 1920, 'height': 1080}, {'width': 1280, 'height': 720}]
                        如果为None，则使用默认分辨率
            
        Returns:
            转码结果列表
        """
        if resolutions is None:
            resolutions = [
                {'width': 1920, 'height': 1080, 'label': '1080p'},
                {'width': 1280, 'height': 720, 'label': '720p'},
                {'width': 854, 'height': 480, 'label': '480p'},
                {'width': 640, 'height': 360, 'label': '360p'},
            ]

        # 获取原始视频信息
        video_info = self.get_video_info(input_path)
        if not video_info:
            logger.error("无法获取视频信息")
            return []

        original_width = video_info['width']
        original_height = video_info['height']

        results = []
        base_name = Path(input_path).stem

        for res in resolutions:
            # 跳过比原始视频更大的分辨率
            if res['width'] > original_width and res['height'] > original_height:
                continue

            output_filename = f"{base_name}_{res['label']}.mp4"
            output_path = os.path.join(output_dir, output_filename)

            logger.info(f"生成 {res['label']} 分辨率: {output_path}")

            result = self.transcode_video(
                input_path=input_path,
                output_path=output_path,
                max_width=res['width'],
                max_height=res['height'],
                preset='fast',
                crf=23
            )

            result['resolution'] = res['label']
            result['width'] = res['width']
            result['height'] = res['height']
            results.append(result)

        return results

    def extract_audio(
            self,
            video_path: str,
            output_path: str,
            audio_format: str = 'mp3',
            audio_bitrate: str = '192k'
    ) -> bool:
        """
        从视频中提取音频
        
        Args:
            video_path: 视频文件路径
            output_path: 输出音频路径
            audio_format: 音频格式 (mp3, aac, ogg等)
            audio_bitrate: 音频比特率
            
        Returns:
            是否成功
        """
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # 根据格式选择编码器
            codec_map = {
                'mp3': 'libmp3lame',
                'aac': 'aac',
                'ogg': 'libvorbis',
                'wav': 'pcm_s16le',
            }

            codec = codec_map.get(audio_format, 'aac')

            cmd = [
                self.ffmpeg_path,
                '-i', video_path,
                '-vn',  # 不包含视频
                '-acodec', codec,
                '-b:a', audio_bitrate,
                '-y',
                output_path
            ]

            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=300
            )

            if result.returncode != 0:
                logger.error(f"音频提取失败: {result.stderr.decode()}")
                return False

            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                logger.info(f"成功提取音频: {output_path}")
                return True
            else:
                return False

        except Exception as e:
            logger.error(f"提取音频失败: {str(e)}")
            return False

    def convert_to_gif(
            self,
            video_path: str,
            output_path: str,
            duration: Optional[float] = None,
            fps: int = 10,
            width: int = 480
    ) -> bool:
        """
        将视频转换为GIF
        
        Args:
            video_path: 视频文件路径
            output_path: 输出GIF路径
            duration: GIF时长（秒），None表示全部
            fps: 帧率
            width: GIF宽度
            
        Returns:
            是否成功
        """
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            cmd = [
                self.ffmpeg_path,
                '-i', video_path,
                '-vf', f'fps={fps},scale={width}:-1:flags=lanczos',
                '-t', str(duration) if duration else '999999',
                '-y',
                output_path
            ]

            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=300
            )

            if result.returncode != 0:
                logger.error(f"GIF转换失败: {result.stderr.decode()}")
                return False

            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                logger.info(f"成功创建GIF: {output_path}")
                return True
            else:
                return False

        except Exception as e:
            logger.error(f"转换GIF失败: {str(e)}")
            return False


# 全局实例
video_processor = VideoProcessor()
