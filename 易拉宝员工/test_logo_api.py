#!/usr/bin/env python3
"""
测试 Logo 相关 API
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_logo_library():
    """测试获取 Logo 库"""
    print("\n========== 测试 Logo 库 API ==========")
    try:
        response = requests.get(f"{BASE_URL}/api/logo-library")
        print(f"状态码: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"✅ 成功获取 Logo 库")
            print(f"品牌: {data.get('brand')}")
            print(f"Logo 数量: {len(data.get('logos', []))}")
            print(f"Logo 列表:")
            for logo in data.get('logos', []):
                print(f"  - {logo['id']}: {logo['displayName']} ({logo['variant']})")
            return True
        else:
            print(f"❌ 失败: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        return False


def test_analyze_banners():
    """测试分析易拉宝 API"""
    print("\n========== 测试分析易拉宝 API ==========")

    # 使用测试 URL（需要先生成一些易拉宝）
    test_urls = [
        "http://localhost:8000/results/banner_test1.png",
        "http://localhost:8000/results/banner_test2.png"
    ]

    try:
        response = requests.post(
            f"{BASE_URL}/api/analyze-banners-for-logo",
            json={"banner_urls": test_urls}
        )
        print(f"状态码: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"✅ 成功分析易拉宝")
            print(f"推荐数量: {len(data.get('recommendations', []))}")
            for i, rec in enumerate(data.get('recommendations', [])):
                print(f"\n易拉宝 {i+1}:")
                if 'error' in rec:
                    print(f"  ❌ 错误: {rec['error']}")
                else:
                    print(f"  推荐 Logo: {rec['recommended_logo']['id']}")
                    print(f"  位置: {rec['recommended_logo']['position']}")
                    print(f"  理由: {rec['reason']}")
            return True
        else:
            print(f"❌ 失败: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        return False


def test_static_files():
    """测试静态文件访问"""
    print("\n========== 测试静态文件访问 ==========")

    # 测试 Logo 文件
    logo_files = [
        "PUDOW朴道健康水专家-原色.png",
        "PUDOW朴道健康水专家-反白.png",
        "PUDOW朴道健康水专家-墨稿.png"
    ]

    for filename in logo_files:
        try:
            url = f"{BASE_URL}/logo_library/{filename}"
            response = requests.head(url)
            if response.status_code == 200:
                print(f"✅ {filename} - 可访问")
            else:
                print(f"❌ {filename} - 状态码 {response.status_code}")
        except Exception as e:
            print(f"❌ {filename} - 错误: {str(e)}")


if __name__ == "__main__":
    print("开始测试 Logo API...")
    print("=" * 50)

    # 测试 Logo 库
    logo_ok = test_logo_library()

    # 测试静态文件
    test_static_files()

    # 测试分析 API（可选，需要有实际的易拉宝文件）
    # test_analyze_banners()

    print("\n" + "=" * 50)
    if logo_ok:
        print("✅ 基础测试通过")
    else:
        print("❌ 测试失败")
