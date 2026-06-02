"""
Supabase Storage 存储管理
用于持久化存储生成的易拉宝图片
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
import httpx

load_dotenv()


class SupabaseStorage:
    """Supabase 对象存储管理类"""

    def __init__(self):
        """初始化 Supabase 客户端"""
        self.enabled = self._check_config()

        if self.enabled:
            self.supabase_url = os.getenv('SUPABASE_URL')
            self.supabase_key = os.getenv('SUPABASE_KEY')
            self.bucket_name = os.getenv('SUPABASE_BUCKET', 'banner-images')

    def _check_config(self) -> bool:
        """检查 Supabase 配置是否完整"""
        return bool(os.getenv('SUPABASE_URL') and os.getenv('SUPABASE_KEY'))

    def upload_file(self, local_path: str, remote_path: str) -> Optional[str]:
        """
        上传文件到 Supabase Storage

        Args:
            local_path: 本地文件路径
            remote_path: 远程路径（如 'results/banner_123.png'）

        Returns:
            文件的公开访问 URL，失败返回 None
        """
        if not self.enabled:
            print("[WARN] Supabase not configured, skip upload")
            return None

        try:
            # 读取文件
            with open(local_path, 'rb') as f:
                file_data = f.read()

            # 上传到 Supabase
            upload_url = f"{self.supabase_url}/storage/v1/object/{self.bucket_name}/{remote_path}"

            headers = {
                'Authorization': f'Bearer {self.supabase_key}',
                'Content-Type': self._get_content_type(local_path),
                'x-upsert': 'true'  # 如果文件存在则覆盖
            }

            response = httpx.post(upload_url, headers=headers, content=file_data, timeout=30.0)

            if response.status_code in [200, 201]:
                # 生成公开 URL
                public_url = f"{self.supabase_url}/storage/v1/object/public/{self.bucket_name}/{remote_path}"
                print(f"[SUCCESS] Upload: {remote_path} -> {public_url}")
                return public_url
            else:
                print(f"[ERROR] Upload failed: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            print(f"[ERROR] Upload failed: {e}")
            return None

    def _get_content_type(self, file_path: str) -> str:
        """根据文件扩展名获取 Content-Type"""
        ext = Path(file_path).suffix.lower()
        content_types = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
        }
        return content_types.get(ext, 'application/octet-stream')

    def delete_file(self, remote_path: str) -> bool:
        """
        删除 Supabase Storage 中的文件

        Args:
            remote_path: 远程路径

        Returns:
            是否删除成功
        """
        if not self.enabled:
            return False

        try:
            delete_url = f"{self.supabase_url}/storage/v1/object/{self.bucket_name}/{remote_path}"
            headers = {'Authorization': f'Bearer {self.supabase_key}'}

            response = httpx.delete(delete_url, headers=headers, timeout=10.0)

            if response.status_code == 200:
                print(f"✅ 删除成功: {remote_path}")
                return True
            else:
                print(f"❌ 删除失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 删除失败: {e}")
            return False

    def list_files(self, prefix: str = '') -> list:
        """
        列出 Supabase Storage 中的文件

        Args:
            prefix: 路径前缀（如 'results/'）

        Returns:
            文件路径列表
        """
        if not self.enabled:
            return []

        try:
            list_url = f"{self.supabase_url}/storage/v1/object/list/{self.bucket_name}"
            headers = {'Authorization': f'Bearer {self.supabase_key}'}

            params = {}
            if prefix:
                params['prefix'] = prefix

            response = httpx.get(list_url, headers=headers, params=params, timeout=10.0)

            if response.status_code == 200:
                files = response.json()
                return [f['name'] for f in files if 'name' in f]
            else:
                print(f"❌ 列出文件失败: {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ 列出文件失败: {e}")
            return []


# 全局实例
supabase_storage = SupabaseStorage()


def upload_image(local_path: str, category: str = 'results') -> Optional[str]:
    """
    便捷函数：上传图片到 Supabase Storage

    Args:
        local_path: 本地文件路径
        category: 分类（results/logos/products）

    Returns:
        公开访问 URL
    """
    filename = Path(local_path).name
    remote_path = f"{category}/{filename}"
    return supabase_storage.upload_file(local_path, remote_path)
