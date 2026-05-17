"""
产品知识库管理模块
用于存储和管理产品信息，支持持久化
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import shutil


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
        except Exception as e:
            print(f"保存产品数据失败: {str(e)}")

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

        # 复制图片文件
        saved_image_path = None
        if image_path and Path(image_path).exists():
            image_ext = Path(image_path).suffix
            saved_image_path = product_dir / f"product{image_ext}"
            shutil.copy(image_path, saved_image_path)

        saved_logo_path = None
        if logo_path and Path(logo_path).exists():
            logo_ext = Path(logo_path).suffix
            saved_logo_path = product_dir / f"logo{logo_ext}"
            shutil.copy(logo_path, saved_logo_path)

        # 构建产品记录
        product_record = {
            "id": product_id,
            "product_info": product_info,
            "image_path": str(saved_image_path) if saved_image_path else None,
            "logo_path": str(saved_logo_path) if saved_logo_path else None,
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
