"""
Logo 库管理模块
负责加载和管理品牌 Logo 库
"""

import json
from pathlib import Path
from typing import Dict, List, Optional

class LogoLibrary:
    """Logo 库管理类"""

    def __init__(self, library_path: str = "logo_library"):
        """
        初始化 Logo 库

        Args:
            library_path: Logo 库目录路径
        """
        # 如果是相对路径，从项目根目录开始
        if not Path(library_path).is_absolute():
            # 获取当前文件所在目录（项目根目录）
            project_root = Path(__file__).parent
            self.library_path = project_root / library_path
        else:
            self.library_path = Path(library_path)

        self.metadata_file = self.library_path / "metadata.json"
        self.metadata = self._load_metadata()

    def _load_metadata(self) -> Dict:
        """加载 Logo 元数据"""
        if not self.metadata_file.exists():
            raise FileNotFoundError(f"Logo 元数据文件不存在: {self.metadata_file}")

        with open(self.metadata_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_all_logos(self) -> List[Dict]:
        """获取所有 Logo 信息"""
        return self.metadata.get("logos", [])

    def get_logo_by_id(self, logo_id: str) -> Optional[Dict]:
        """
        根据 ID 获取 Logo 信息

        Args:
            logo_id: Logo ID

        Returns:
            Logo 信息字典，如果不存在则返回 None
        """
        for logo in self.metadata.get("logos", []):
            if logo["id"] == logo_id:
                return logo
        return None

    def get_logo_path(self, logo_id: str) -> Optional[str]:
        """
        获取 Logo 文件的完整路径

        Args:
            logo_id: Logo ID

        Returns:
            Logo 文件路径，如果不存在则返回 None
        """
        logo = self.get_logo_by_id(logo_id)
        if logo:
            return str(self.library_path / logo["filename"])
        return None

    def filter_logos_by_background(self, background_type: str) -> List[Dict]:
        """
        根据背景类型筛选合适的 Logo

        Args:
            background_type: 背景类型 (white/light/dark/black)

        Returns:
            合适的 Logo 列表
        """
        suitable_logos = []
        for logo in self.metadata.get("logos", []):
            if background_type in logo["background"]["recommended"]:
                suitable_logos.append(logo)
        return suitable_logos

    def filter_logos_by_style(self, style: str) -> List[Dict]:
        """
        根据易拉宝风格筛选合适的 Logo

        Args:
            style: 易拉宝风格 (科技感/简约商务/自然清新/时尚活力/高端奢华)

        Returns:
            合适的 Logo 列表
        """
        suitable_logos = []
        for logo in self.metadata.get("logos", []):
            if style in logo["suitableFor"]["bannerStyles"]:
                suitable_logos.append(logo)
        return suitable_logos

    def get_placement_rules(self) -> Dict:
        """获取 Logo 放置规则"""
        return self.metadata.get("placementRules", {})

    def get_usage_guidelines(self) -> Dict:
        """获取使用指南"""
        return self.metadata.get("usageGuidelines", {})

    def recommend_logo(
        self,
        banner_style: str,
        background_type: str,
        prefer_variant: Optional[str] = None
    ) -> Optional[Dict]:
        """
        推荐最合适的 Logo

        Args:
            banner_style: 易拉宝风格
            background_type: 背景类型
            prefer_variant: 偏好的变体 (原色/反白/墨稿)，可选

        Returns:
            推荐的 Logo 信息
        """
        # 先按风格筛选
        style_matched = self.filter_logos_by_style(banner_style)

        # 再按背景筛选
        bg_matched = [
            logo for logo in style_matched
            if background_type in logo["background"]["recommended"]
        ]

        # 如果有偏好变体，优先选择
        if prefer_variant and bg_matched:
            for logo in bg_matched:
                if logo["variant"] == prefer_variant:
                    return logo

        # 返回第一个匹配的
        return bg_matched[0] if bg_matched else None


# 全局 Logo 库实例
logo_library = LogoLibrary()


if __name__ == "__main__":
    # 测试代码
    lib = LogoLibrary()

    print("=== Logo 库信息 ===")
    print(f"品牌: {lib.metadata['brand']}")
    print(f"Logo 数量: {len(lib.get_all_logos())}")

    print("\n=== 所有 Logo ===")
    for logo in lib.get_all_logos():
        print(f"- {logo['displayName']} ({logo['id']})")

    print("\n=== 推荐测试 ===")
    recommended = lib.recommend_logo("科技感", "light", "原色")
    if recommended:
        print(f"推荐: {recommended['displayName']}")
        print(f"文件: {recommended['filename']}")
        print(f"理由: {recommended['style']['characteristics']}")
