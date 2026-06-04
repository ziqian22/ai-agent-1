"""
产品知识库管理模块
用于存储和管理产品信息，支持持久化
支持自动备份到 Supabase Storage
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import shutil
import httpx
from dotenv import load_dotenv

load_dotenv()


class KnowledgeBase:
    """产品知识库管理器"""

    def __init__(self, db_path: str = "knowledge_base"):
        """
        初始化知识库

        Args:
            db_path: 知识库存储路径
        """
        self.db_path = Path(db_path)
        self.db_path.mkdir(exist_ok=True)

        # 产品数据文件
        self.products_file = self.db_path / "products.json"

        # 产品文件存储目录
        self.files_dir = self.db_path / "files"
        self.files_dir.mkdir(exist_ok=True)

        # Supabase 配置
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY')
        self.supabase_bucket = os.getenv('SUPABASE_BUCKET', 'banner-images')
        self.backup_enabled = bool(self.supabase_url and self.supabase_key)

        if self.backup_enabled:
            print("[INFO] Supabase 备份已启用")
            # 启动时尝试从 Supabase 恢复数据
            self.restore_from_supabase()
        else:
            print("[WARN] Supabase 未配置，备份功能禁用")

        # 加载产品数据
        self.products = self._load_products()

    def _load_products(self) -> List[Dict[str, Any]]:
        """从文件加载产品数据"""
        if self.products_file.exists():
            try:
                with open(self.products_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载产品数据失败: {str(e)}")
                return []
        return []

    def _save_products(self):
        """保存产品数据到文件"""
        try:
            with open(self.products_file, 'w', encoding='utf-8') as f:
                json.dump(self.products, f, ensure_ascii=False, indent=2)

            # 自动备份到 Supabase
            if self.backup_enabled:
                self.backup_to_supabase()
        except Exception as e:
            print(f"保存产品数据失败: {str(e)}")

    def backup_to_supabase(self):
        """备份 products.json 到 Supabase Storage"""
        if not self.backup_enabled:
            return

        try:
            # 读取 products.json 文件
            with open(self.products_file, 'rb') as f:
                file_data = f.read()

            # 构建上传 URL
            remote_path = "backups/products.json"
            url = f"{self.supabase_url}/storage/v1/object/{self.supabase_bucket}/{remote_path}"

            headers = {
                "Authorization": f"Bearer {self.supabase_key}",
                "Content-Type": "application/json"
            }

            # 上传文件（使用 POST 或 PUT）
            with httpx.Client(timeout=30.0) as client:
                # 先尝试更新（PUT）
                response = client.put(url, headers=headers, content=file_data)

                # 如果文件不存在，使用 POST 创建
                if response.status_code == 404:
                    url = f"{self.supabase_url}/storage/v1/object/{self.supabase_bucket}/{remote_path}"
                    response = client.post(url, headers=headers, content=file_data)

                if response.status_code in [200, 201]:
                    print(f"[SUCCESS] 已备份到 Supabase: {remote_path}")
                else:
                    print(f"[WARN] 备份到 Supabase 失败: {response.status_code} - {response.text}")

        except Exception as e:
            print(f"[ERROR] 备份到 Supabase 失败: {str(e)}")

    def restore_from_supabase(self):
        """从 Supabase Storage 恢复 products.json"""
        if not self.backup_enabled:
            return

        # 如果本地文件已存在且不为空，跳过恢复
        if self.products_file.exists():
            try:
                with open(self.products_file, 'r', encoding='utf-8') as f:
                    local_data = json.load(f)
                    if local_data:
                        print("[INFO] 本地产品数据已存在，跳过从 Supabase 恢复")
                        return
            except:
                pass

        try:
            # 构建下载 URL
            remote_path = "backups/products.json"
            url = f"{self.supabase_url}/storage/v1/object/public/{self.supabase_bucket}/{remote_path}"

            # 下载文件
            with httpx.Client(timeout=30.0) as client:
                response = client.get(url)

                if response.status_code == 200:
                    # 保存到本地
                    with open(self.products_file, 'wb') as f:
                        f.write(response.content)
                    print(f"[SUCCESS] 已从 Supabase 恢复产品数据")
                elif response.status_code == 404:
                    print("[INFO] Supabase 上没有备份文件，使用空数据")
                else:
                    print(f"[WARN] 从 Supabase 恢复失败: {response.status_code}")

        except Exception as e:
            print(f"[ERROR] 从 Supabase 恢复失败: {str(e)}")

    def _upload_file_to_supabase(self, local_path: str, remote_path: str) -> Optional[str]:
        """
        上传文件到 Supabase Storage

        Args:
            local_path: 本地文件路径
            remote_path: 远程路径（如 'products/product_123/image.png'）

        Returns:
            文件的公开访问 URL，失败返回 None
        """
        if not self.backup_enabled:
            return None

        try:
            # 读取文件
            with open(local_path, 'rb') as f:
                file_data = f.read()

            # 构建上传 URL
            url = f"{self.supabase_url}/storage/v1/object/{self.supabase_bucket}/{remote_path}"

            headers = {
                'Authorization': f'Bearer {self.supabase_key}',
                'Content-Type': self._get_content_type(local_path),
                'x-upsert': 'true'
            }

            # 上传
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, headers=headers, content=file_data)

                if response.status_code in [200, 201]:
                    public_url = f"{self.supabase_url}/storage/v1/object/public/{self.supabase_bucket}/{remote_path}"
                    print(f"[SUCCESS] 上传文件到 Supabase: {remote_path}")
                    return public_url
                else:
                    print(f"[WARN] 上传文件到 Supabase 失败: {response.status_code}")
                    return None

        except Exception as e:
            print(f"[ERROR] 上传文件到 Supabase 失败: {str(e)}")
            return None

    def _get_content_type(self, file_path: str) -> str:
        """根据文件扩展名获取 Content-Type"""
        ext = Path(file_path).suffix.lower()
        content_types = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
            '.json': 'application/json',
        }
        return content_types.get(ext, 'application/octet-stream')

    def add_product(
        self,
        product_info: Dict[str, Any],
        image_path: Optional[str] = None,
        logo_path: Optional[str] = None
    ) -> str:
        """
        添加产品到知识库

        Args:
            product_info: 产品信息字典
            image_path: 产品图片路径
            logo_path: Logo路径

        Returns:
            产品ID
        """
        # 生成产品ID
        product_id = f"product_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 创建产品目录
        product_dir = self.files_dir / product_id
        product_dir.mkdir(exist_ok=True)

        # 复制图片文件到本地，并上传到 Supabase
        saved_image_path = None
        saved_image_url = None
        if image_path and Path(image_path).exists():
            image_ext = Path(image_path).suffix
            saved_image_path = product_dir / f"product{image_ext}"
            shutil.copy(image_path, saved_image_path)

            # 上传到 Supabase
            if self.backup_enabled:
                remote_path = f"products/{product_id}/product{image_ext}"
                saved_image_url = self._upload_file_to_supabase(str(saved_image_path), remote_path)

        saved_logo_path = None
        saved_logo_url = None
        if logo_path and Path(logo_path).exists():
            logo_ext = Path(logo_path).suffix
            saved_logo_path = product_dir / f"logo{logo_ext}"
            shutil.copy(logo_path, saved_logo_path)

            # 上传到 Supabase
            if self.backup_enabled:
                remote_path = f"products/{product_id}/logo{logo_ext}"
                saved_logo_url = self._upload_file_to_supabase(str(saved_logo_path), remote_path)

        # 构建产品记录
        product_record = {
            "id": product_id,
            "product_info": product_info,
            "image_path": str(saved_image_path) if saved_image_path else None,
            "image_url": saved_image_url,  # Supabase URL
            "logo_path": str(saved_logo_path) if saved_logo_path else None,
            "logo_url": saved_logo_url,  # Supabase URL
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "generation_history": []  # 历史生成记录
        }

        # 添加到产品列表
        self.products.append(product_record)

        # 保存
        self._save_products()

        return product_id

    def get_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        """
        获取产品信息

        Args:
            product_id: 产品ID

        Returns:
            产品信息字典，如果不存在返回None
        """
        for product in self.products:
            if product["id"] == product_id:
                return product
        return None

    def get_all_products(self) -> List[Dict[str, Any]]:
        """
        获取所有产品

        Returns:
            产品列表
        """
        return self.products

    def search_products(self, keyword: str) -> List[Dict[str, Any]]:
        """
        搜索产品

        Args:
            keyword: 搜索关键词

        Returns:
            匹配的产品列表
        """
        keyword_lower = keyword.lower()
        results = []

        for product in self.products:
            product_info = product.get("product_info", {})

            # 搜索产品名称
            if keyword_lower in product_info.get("product_name", "").lower():
                results.append(product)
                continue

            # 搜索品牌
            if keyword_lower in product_info.get("brand", "").lower():
                results.append(product)
                continue

            # 搜索产品类型
            if keyword_lower in product_info.get("product_type", "").lower():
                results.append(product)
                continue

        return results

    def update_product(self, product_id: str, product_info: Dict[str, Any]) -> bool:
        """
        更新产品信息

        Args:
            product_id: 产品ID
            product_info: 新的产品信息

        Returns:
            是否更新成功
        """
        for product in self.products:
            if product["id"] == product_id:
                product["product_info"] = product_info
                product["updated_at"] = datetime.now().isoformat()
                self._save_products()
                return True
        return False

    def delete_product(self, product_id: str) -> bool:
        """
        删除产品

        Args:
            product_id: 产品ID

        Returns:
            是否删除成功
        """
        for i, product in enumerate(self.products):
            if product["id"] == product_id:
                # 删除产品文件目录
                product_dir = self.files_dir / product_id
                if product_dir.exists():
                    shutil.rmtree(product_dir)

                # 从列表中移除
                self.products.pop(i)
                self._save_products()
                return True
        return False

    def add_generation_record(
        self,
        product_id: str,
        style_name: str,
        result_files: List[str],
        user_rating: Optional[int] = None
    ) -> bool:
        """
        添加生成记录

        Args:
            product_id: 产品ID
            style_name: 风格名称
            result_files: 生成的文件路径列表
            user_rating: 用户评分（1-5）

        Returns:
            是否添加成功
        """
        for product in self.products:
            if product["id"] == product_id:
                record = {
                    "style": style_name,
                    "result_files": result_files,
                    "user_rating": user_rating,
                    "created_at": datetime.now().isoformat()
                }
                product["generation_history"].append(record)
                self._save_products()
                return True
        return False

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取知识库统计信息

        Returns:
            统计信息字典
        """
        total_products = len(self.products)
        total_generations = sum(
            len(p.get("generation_history", []))
            for p in self.products
        )

        # 统计产品类型
        product_types = {}
        for product in self.products:
            product_type = product.get("product_info", {}).get("product_type", "未分类")
            product_types[product_type] = product_types.get(product_type, 0) + 1

        return {
            "total_products": total_products,
            "total_generations": total_generations,
            "product_types": product_types
        }


# 测试代码
if __name__ == "__main__":
    # 创建知识库实例
    kb = KnowledgeBase()

    # 测试添加产品
    test_product = {
        "product_name": "测试产品",
        "brand": "测试品牌",
        "product_type": "测试类型",
        "features": ["特点1", "特点2"],
        "scenes": ["场景1", "场景2"]
    }

    product_id = kb.add_product(test_product)
    print(f"添加产品成功，ID: {product_id}")

    # 测试获取所有产品
    all_products = kb.get_all_products()
    print(f"知识库中共有 {len(all_products)} 个产品")

    # 测试搜索
    results = kb.search_products("测试")
    print(f"搜索'测试'找到 {len(results)} 个产品")

    # 测试统计
    stats = kb.get_statistics()
    print(f"统计信息: {stats}")
