"""
快速测试上传接口
"""
import requests
import sys
from pathlib import Path

def test_upload():
    """测试上传接口"""
    print("测试上传接口...")

    # 检查是否有测试图片
    test_image = Path("test_image.jpg")
    if not test_image.exists():
        print("❌ 错误: 找不到测试图片 test_image.jpg")
        print("请在项目根目录放置一张测试图片")
        return False

    # 准备请求
    url = "http://localhost:8000/api/upload"

    with open(test_image, 'rb') as f:
        files = {'file': f}
        data = {'save_to_kb': 'false'}

        try:
            response = requests.post(url, files=files, data=data, timeout=30)

            if response.status_code == 200:
                print("✅ 上传成功!")
                result = response.json()
                print(f"Session ID: {result.get('session_id')}")
                print(f"产品名称: {result.get('product_info', {}).get('product_name')}")
                return True
            else:
                print(f"❌ 上传失败: {response.status_code}")
                print(f"错误信息: {response.text}")
                return False

        except requests.exceptions.ConnectionError:
            print("❌ 错误: 无法连接到后端服务")
            print("请确保后端服务已启动 (python -m uvicorn backend.main:app)")
            return False
        except Exception as e:
            print(f"❌ 错误: {str(e)}")
            return False

if __name__ == "__main__":
    success = test_upload()
    sys.exit(0 if success else 1)
