"""
远程存储管理器
支持S3、OSS、FTP等远程存储
"""

from pathlib import Path
from typing import Dict, Any


class RemoteStorageManager:
    """远程存储管理器"""

    def upload_to_remote(self, backup_path: Path, remote_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        上传备份到远程存储
        
        Args:
            backup_path: 备份文件路径
            remote_config: 远程存储配置 {type: 's3|oss|ftp', ...}
        """
        try:
            remote_type = remote_config.get('type', 's3')

            # 压缩备份
            zip_path = backup_path.parent / f"{backup_path.name}.zip"
            self._compress_backup(backup_path, zip_path)

            # 根据类型上传
            if remote_type == 's3':
                result = self._upload_to_s3(zip_path, remote_config)
            elif remote_type == 'oss':
                result = self._upload_to_oss(zip_path, remote_config)
            elif remote_type == 'ftp':
                result = self._upload_to_ftp(zip_path, remote_config)
            else:
                if zip_path.exists():
                    zip_path.unlink()
                return {'success': False, 'error': f'不支持的远程存储类型: {remote_type}'}

            if not result.get('success'):
                print(f"[RemoteStorage] Upload failed, keeping zip file for retry")

            return result
        except Exception as e:
            print(f"[RemoteStorage] Remote upload failed: {e}")
            return {'success': False, 'error': str(e)}

    def _compress_backup(self, backup_path: Path, zip_path: Path):
        """压缩备份文件夹"""
        import zipfile

        print(f"[RemoteStorage] Compressing backup...")
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in backup_path.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(backup_path)
                    zipf.write(file_path, arcname)

        compressed_size = zip_path.stat().st_size
        print(f"[RemoteStorage] Backup compressed: {zip_path.name} ({compressed_size / 1024:.2f} KB)")

    def _upload_to_s3(self, zip_path: Path, config: Dict) -> Dict[str, Any]:
        """上传到AWS S3"""
        try:
            import boto3

            s3_client = boto3.client(
                's3',
                aws_access_key_id=config.get('access_key'),
                aws_secret_access_key=config.get('secret_key'),
                region_name=config.get('region', 'us-east-1')
            )

            bucket = config.get('bucket')
            s3_key = f"backups/{zip_path.name}"
            s3_client.upload_file(str(zip_path), bucket, s3_key)

            zip_path.unlink()

            return {
                'success': True,
                'message': '已上传到S3',
                'remote_path': f"s3://{bucket}/{s3_key}"
            }
        except ImportError:
            return {'success': False, 'error': 'S3上传需要安装boto3: pip install boto3'}
        except Exception as e:
            return {'success': False, 'error': f'S3上传失败: {str(e)}'}

    def _upload_to_oss(self, zip_path: Path, config: Dict) -> Dict[str, Any]:
        """上传到阿里云OSS"""
        try:
            import oss2

            auth = oss2.Auth(config['access_key'], config['secret_key'])
            bucket = oss2.Bucket(auth, config['endpoint'], config['bucket'])

            oss_key = f"backups/{zip_path.name}"
            bucket.put_object_from_file(oss_key, str(zip_path))

            zip_path.unlink()

            return {
                'success': True,
                'message': '已上传到OSS',
                'remote_path': f"oss://{config['bucket']}/{oss_key}"
            }
        except ImportError:
            return {'success': False, 'error': 'OSS上传需要安装oss2: pip install oss2'}
        except Exception as e:
            return {'success': False, 'error': f'OSS上传失败: {str(e)}'}

    def _upload_to_ftp(self, zip_path: Path, config: Dict) -> Dict[str, Any]:
        """上传到FTP服务器"""
        try:
            from ftplib import FTP

            ftp = FTP(config['host'])
            ftp.login(config.get('user', 'anonymous'), config.get('password', ''))

            remote_dir = config.get('directory', '/backups')
            try:
                ftp.cwd(remote_dir)
            except:
                ftp.mkd(remote_dir)
                ftp.cwd(remote_dir)

            with open(zip_path, 'rb') as f:
                ftp.storbinary(f'STOR {zip_path.name}', f)

            ftp.quit()
            zip_path.unlink()

            return {
                'success': True,
                'message': '已上传到FTP',
                'remote_path': f"ftp://{config['host']}{remote_dir}/{zip_path.name}"
            }
        except Exception as e:
            return {'success': False, 'error': f'FTP上传失败: {str(e)}'}
