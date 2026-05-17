import httpx
import asyncio
import time
from typing import Dict, List, Optional, Any
from pathlib import Path


class RunningHubClient:
    """Running Hub API客户端"""

    def __init__(self, api_key: str, base_url: str = "https://www.runninghub.cn/openapi/v2"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

    def upload_image(self, image_path: str) -> Optional[str]:
        """
        上传图片到Running Hub

        Args:
            image_path: 本地图片路径

        Returns:
            上传后的文件名(fileName字段),失败返回None
        """
        try:
            url = f"{self.base_url}/media/upload/binary"

            with open(image_path, 'rb') as f:
                files = {'file': f}
                headers = {"Authorization": f"Bearer {self.api_key}"}

                response = httpx.post(url, files=files, headers=headers, timeout=30.0)
                response.raise_for_status()

                result = response.json()
                if result.get('code') == 0:
                    return result['data']['fileName']
                else:
                    print(f"上传失败: {result.get('message')}")
                    return None

        except Exception as e:
            print(f"上传图片出错: {str(e)}")
            return None

    def start_workflow(self, workflow_id: str, node_info_list: List[Dict],
                       workflow_type: str = "workflow",
                       instance_type: str = "default",
                       use_personal_queue: bool = False) -> Optional[Dict]:
        """
        启动工作流

        Args:
            workflow_id: 工作流ID
            node_info_list: 节点参数列表
            workflow_type: 工作流类型 ("workflow" 或 "ai-app")
            instance_type: 实例类型 ("default" 或 "plus")
            use_personal_queue: 是否使用个人队列

        Returns:
            响应数据,包含taskId等信息
        """
        try:
            url = f"{self.base_url}/run/{workflow_type}/{workflow_id}"

            payload = {
                "nodeInfoList": node_info_list,
                "instanceType": instance_type,
                "usePersonalQueue": str(use_personal_queue).lower()
            }

            response = httpx.post(url, json=payload, headers=self.headers, timeout=30.0)
            response.raise_for_status()

            return response.json()

        except Exception as e:
            print(f"启动工作流出错: {str(e)}")
            return None

    def query_task(self, task_id: str) -> Optional[Dict]:
        """
        查询任务状态

        Args:
            task_id: 任务ID

        Returns:
            任务状态信息
        """
        try:
            url = f"{self.base_url}/query"
            payload = {"taskId": task_id}

            response = httpx.post(url, json=payload, headers=self.headers, timeout=30.0)
            response.raise_for_status()

            return response.json()

        except Exception as e:
            print(f"查询任务出错: {str(e)}")
            return None

    def wait_for_completion(self, task_id: str, max_wait_time: int = 600,
                           poll_interval: int = 5) -> Optional[Dict]:
        """
        等待任务完成(轮询)

        Args:
            task_id: 任务ID
            max_wait_time: 最大等待时间(秒)
            poll_interval: 轮询间隔(秒)

        Returns:
            完成后的任务信息
        """
        start_time = time.time()

        while time.time() - start_time < max_wait_time:
            result = self.query_task(task_id)

            if not result:
                return None

            status = result.get('status')

            if status == 'SUCCESS':
                return result
            elif status == 'FAILED':
                print(f"任务失败: {result.get('errorMessage')}")
                return result

            # 继续等待
            time.sleep(poll_interval)

        print(f"任务超时(超过{max_wait_time}秒)")
        return None

    def download_image(self, image_url: str, save_path: str) -> bool:
        """
        下载图片

        Args:
            image_url: 图片URL
            save_path: 保存路径

        Returns:
            是否成功
        """
        try:
            response = httpx.get(image_url, timeout=30.0)
            response.raise_for_status()

            Path(save_path).parent.mkdir(parents=True, exist_ok=True)

            with open(save_path, 'wb') as f:
                f.write(response.content)

            return True

        except Exception as e:
            print(f"下载图片出错: {str(e)}")
            return False

    def test_connection(self) -> bool:
        """
        测试API连接

        Returns:
            连接是否正常
        """
        try:
            # 尝试查询一个不存在的任务,如果返回正常格式的错误说明连接正常
            url = f"{self.base_url}/query"
            payload = {"taskId": "test_connection"}

            response = httpx.post(url, json=payload, headers=self.headers, timeout=10.0)

            # 只要能收到响应就说明连接正常
            return response.status_code in [200, 400, 404]

        except Exception as e:
            print(f"连接测试失败: {str(e)}")
            return False
