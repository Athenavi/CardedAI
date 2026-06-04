"""
EXIF 数据读取服务
从图片文件中提取 EXIF 元数据
"""
from typing import Optional, Dict, Any

from PIL import Image
from PIL.ExifTags import TAGS

# GPS 标签常量
GPS_LAT_REF = 1
GPS_LATITUDE = 2
GPS_LON_REF = 3
GPS_LONGITUDE = 4
GPS_ALT_REF = 5
GPS_ALTITUDE = 6

# 方向映射
ORIENTATION_MAP = {
    1: 'Normal',
    3: 'Rotated 180°',
    6: 'Rotated 90° CW',
    8: 'Rotated 90° CCW'
}


class ExifService:
    """EXIF 数据提取服务"""
    
    # GPS 坐标转换
    @staticmethod
    def _convert_to_degrees(value: tuple) -> float:
        """将 GPS 坐标转换为十进制度数"""
        return value[0] + (value[1] / 60.0) + (value[2] / 3600.0)
    
    @staticmethod
    def _get_gps_location(exif_data: dict) -> Optional[dict]:
        """从 EXIF 数据中提取 GPS 坐标"""
        gps_info = exif_data.get('GPSInfo')
        if not gps_info:
            return None
        
        try:
            # 纬度
            lat_ref = gps_info.get(GPS_LAT_REF)
            lat_values = gps_info.get(GPS_LATITUDE)
            if not (lat_ref and lat_values):
                return None

            latitude = ExifService._convert_to_degrees(lat_values)
            if lat_ref != 'N':
                latitude = -latitude

            # 经度
            lon_ref = gps_info.get(GPS_LON_REF)
            lon_values = gps_info.get(GPS_LONGITUDE)
            if not (lon_ref and lon_values):
                return None

            longitude = ExifService._convert_to_degrees(lon_values)
            if lon_ref != 'E':
                longitude = -longitude
            
            # 海拔（可选）
            altitude = None
            alt_ref = gps_info.get(GPS_ALT_REF)
            alt_raw = gps_info.get(GPS_ALTITUDE)
            if alt_ref is not None and alt_raw is not None:
                altitude = float(alt_raw)
                if alt_ref == 1:  # 海平面以下
                    altitude = -altitude
            
            return {
                'latitude': round(latitude, 6),
                'longitude': round(longitude, 6),
                'altitude': round(altitude, 2) if altitude else None
            }
        except (TypeError, ZeroDivisionError):
            return None
    
    @classmethod
    def extract_exif(cls, image_path: str) -> Dict[str, Any]:
        """
        从图片文件中提取 EXIF 数据
        
        Args:
            image_path: 图片文件路径
            
        Returns:
            包含 EXIF 数据的字典
        """
        result = {
            'has_exif': False,
            'camera': {},
            'settings': {},
            'datetime': None,
            'gps': None,
            'dimensions': {},
            'raw_exif': {}
        }
        
        try:
            # 打开图片
            with Image.open(image_path) as img:
                # 获取基本尺寸信息
                result['dimensions'] = {
                    'width': img.width,
                    'height': img.height,
                    'format': img.format,
                    'mode': img.mode
                }
                
                # 尝试获取 EXIF 数据
                exif_data = img._getexif()
                if not exif_data:
                    return result
                
                result['has_exif'] = True
                
                # 解析 EXIF 标签
                parsed_exif = {}
                for tag_id, value in exif_data.items():
                    tag_name = TAGS.get(tag_id, tag_id)
                    parsed_exif[tag_name] = value
                
                result['raw_exif'] = parsed_exif
                
                # 提取相机信息
                camera_info = {}
                for key in ('Make', 'Model', 'LensModel'):
                    if key in parsed_exif:
                        camera_info[key.lower()] = parsed_exif[key]

                if 'LensInfo' in parsed_exif and 'lens' not in camera_info:
                    camera_info['lens'] = str(parsed_exif['LensInfo'])
                
                result['camera'] = camera_info
                
                # 提取拍摄参数
                settings = {}
                if 'ExposureTime' in parsed_exif:
                    exposure = parsed_exif['ExposureTime']
                    if isinstance(exposure, tuple) and exposure[0] != 0:
                        settings['shutter_speed'] = f"1/{round(exposure[1] / exposure[0])}"
                    else:
                        settings['shutter_speed'] = str(exposure)
                
                if 'FNumber' in parsed_exif:
                    fnumber = parsed_exif['FNumber']
                    f_val = fnumber[0] / fnumber[1] if isinstance(fnumber, tuple) else fnumber
                    settings['aperture'] = f"f/{f_val:.1f}"
                
                if 'ISOSpeedRatings' in parsed_exif:
                    settings['iso'] = parsed_exif['ISOSpeedRatings']
                
                if 'FocalLength' in parsed_exif:
                    focal = parsed_exif['FocalLength']
                    f_len = focal[0] / focal[1] if isinstance(focal, tuple) else focal
                    settings['focal_length'] = f"{f_len:.1f}mm"
                
                if 'Flash' in parsed_exif:
                    settings['flash'] = 'On' if parsed_exif['Flash'] & 1 else 'Off'
                
                if 'WhiteBalance' in parsed_exif:
                    settings['white_balance'] = 'Auto' if parsed_exif['WhiteBalance'] == 0 else 'Manual'
                
                result['settings'] = settings
                
                # 提取拍摄时间
                if 'DateTimeOriginal' in parsed_exif:
                    result['datetime'] = parsed_exif['DateTimeOriginal']
                elif 'DateTime' in parsed_exif:
                    result['datetime'] = parsed_exif['DateTime']
                
                # 提取 GPS 信息
                gps_data = cls._get_gps_location(parsed_exif)
                if gps_data:
                    result['gps'] = gps_data
                
                # 提取其他有用信息
                for key in ('Software', 'Artist', 'Copyright'):
                    if key in parsed_exif:
                        result[key.lower()] = parsed_exif[key]
                
                # 提取方向
                orientation = parsed_exif.get('Orientation')
                if orientation:
                    result['orientation'] = ORIENTATION_MAP.get(orientation, 'Unknown')
        
        except Exception as e:
            # 如果提取失败，返回基本结构
            result['error'] = str(e)
        
        return result
    
    @classmethod
    def format_exif_for_display(cls, exif_data: dict) -> list:
        """
        格式化 EXIF 数据用于前端显示
        
        Args:
            exif_data: EXIF 数据字典
            
        Returns:
            格式化的信息列表
        """
        info_items = []
        
        # 相机信息
        if exif_data.get('camera'):
            camera = exif_data['camera']
            if camera.get('make') and camera.get('model'):
                info_items.append({
                    'label': '相机',
                    'value': f"{camera['make']} {camera['model']}",
                    'icon': 'camera'
                })
            if camera.get('lens'):
                info_items.append({
                    'label': '镜头',
                    'value': camera['lens'],
                    'icon': 'lens'
                })
        
        # 拍摄参数
        if exif_data.get('settings'):
            settings = exif_data['settings']
            if settings.get('shutter_speed'):
                info_items.append({
                    'label': '快门速度',
                    'value': settings['shutter_speed'],
                    'icon': 'clock'
                })
            if settings.get('aperture'):
                info_items.append({
                    'label': '光圈',
                    'value': settings['aperture'],
                    'icon': 'aperture'
                })
            if settings.get('iso'):
                info_items.append({
                    'label': 'ISO',
                    'value': str(settings['iso']),
                    'icon': 'sun'
                })
            if settings.get('focal_length'):
                info_items.append({
                    'label': '焦距',
                    'value': settings['focal_length'],
                    'icon': 'focus'
                })
        
        # 拍摄时间
        if exif_data.get('datetime'):
            info_items.append({
                'label': '拍摄时间',
                'value': exif_data['datetime'],
                'icon': 'calendar'
            })
        
        # GPS 信息
        if exif_data.get('gps'):
            gps = exif_data['gps']
            location_str = f"{gps['latitude']:.6f}, {gps['longitude']:.6f}"
            if gps.get('altitude'):
                location_str += f" (海拔 {gps['altitude']}m)"
            info_items.append({
                'label': '位置',
                'value': location_str,
                'icon': 'map-pin',
                'gps': gps
            })
        
        return info_items
    
    @classmethod
    def has_significant_exif(cls, exif_data: dict) -> bool:
        """
        检查是否有重要的 EXIF 数据
        
        Args:
            exif_data: EXIF 数据字典
            
        Returns:
            是否包含重要信息
        """
        if not exif_data.get('has_exif'):
            return False
        
        # 检查是否有相机信息或拍摄参数
        if exif_data.get('camera') or exif_data.get('settings'):
            return True
        
        # 检查是否有 GPS 信息
        if exif_data.get('gps'):
            return True
        
        return False
