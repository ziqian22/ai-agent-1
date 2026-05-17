import json
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime
import shutil


class TestRecorder:
    """测试记录管理"""

    def __init__(self, config_file: str = "workflows.json", results_dir: str = "results"):
        self.config_file = config_file
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)

    def _load_config(self) -> Dict:
        """加载配置文件"""
        if Path(self.config_file).exists():
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"workflows": [], "test_history": []}

    def _save_config(self, config: Dict):
        """保存配置文件"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

    def add_test_record(self, workflow_id: str, workflow_name: str,
                       task_id: str, params: Dict,
                       results: List[Dict], status: str,
                       cost_time: str = "", notes: str = "") -> str:
        """
        添加测试记录

        Args:
            workflow_id: 工作流ID
            workflow_name: 工作流名称
            task_id: 任务ID
            params: 使用的参数
            results: 生成结果列表
            status: 任务状态
            cost_time: 耗时
            notes: 备注

        Returns:
            测试记录ID
        """
        config = self._load_config()

        test_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        timestamp = datetime.now().isoformat()

        # 创建测试结果目录
        test_dir = self.results_dir / test_id
        test_dir.mkdir(exist_ok=True)

        # 保存结果图片的本地路径
        saved_images = []
        for idx, result in enumerate(results):
            if result.get('url'):
                image_name = f"result_{idx}.{result.get('outputType', 'png')}"
                saved_images.append(str(test_dir / image_name))

        record = {
            "test_id": test_id,
            "timestamp": timestamp,
            "workflow_id": workflow_id,
            "workflow_name": workflow_name,
            "task_id": task_id,
            "params": params,
            "results": results,
            "saved_images": saved_images,
            "status": status,
            "cost_time": cost_time,
            "rating": 0,
            "notes": notes
        }

        config['test_history'].append(record)
        self._save_config(config)

        return test_id

    def get_test_record(self, test_id: str) -> Optional[Dict]:
        """获取测试记录"""
        config = self._load_config()
        for record in config['test_history']:
            if record['test_id'] == test_id:
                return record
        return None

    def get_all_test_records(self) -> List[Dict]:
        """获取所有测试记录"""
        config = self._load_config()
        return config['test_history']

    def get_workflow_tests(self, workflow_id: str) -> List[Dict]:
        """获取指定工作流的所有测试记录"""
        config = self._load_config()
        return [
            record for record in config['test_history']
            if record['workflow_id'] == workflow_id
        ]

    def update_rating(self, test_id: str, rating: int) -> bool:
        """
        更新测试评分

        Args:
            test_id: 测试ID
            rating: 评分(1-5)

        Returns:
            是否成功
        """
        config = self._load_config()
        for record in config['test_history']:
            if record['test_id'] == test_id:
                record['rating'] = rating
                self._save_config(config)
                return True
        return False

    def update_notes(self, test_id: str, notes: str) -> bool:
        """
        更新测试备注

        Args:
            test_id: 测试ID
            notes: 备注内容

        Returns:
            是否成功
        """
        config = self._load_config()
        for record in config['test_history']:
            if record['test_id'] == test_id:
                record['notes'] = notes
                self._save_config(config)
                return True
        return False

    def delete_test_record(self, test_id: str) -> bool:
        """删除测试记录"""
        config = self._load_config()
        original_len = len(config['test_history'])

        config['test_history'] = [
            record for record in config['test_history']
            if record['test_id'] != test_id
        ]

        if len(config['test_history']) < original_len:
            # 删除测试结果目录
            test_dir = self.results_dir / test_id
            if test_dir.exists():
                shutil.rmtree(test_dir)

            self._save_config(config)
            return True
        return False

    def get_test_statistics(self) -> Dict:
        """获取测试统计信息"""
        config = self._load_config()
        records = config['test_history']

        if not records:
            return {
                "total_tests": 0,
                "success_count": 0,
                "failed_count": 0,
                "avg_rating": 0,
                "workflows_tested": 0
            }

        success_count = sum(1 for r in records if r['status'] == 'SUCCESS')
        failed_count = sum(1 for r in records if r['status'] == 'FAILED')
        ratings = [r['rating'] for r in records if r['rating'] > 0]
        avg_rating = sum(ratings) / len(ratings) if ratings else 0
        workflows_tested = len(set(r['workflow_id'] for r in records))

        return {
            "total_tests": len(records),
            "success_count": success_count,
            "failed_count": failed_count,
            "avg_rating": round(avg_rating, 2),
            "workflows_tested": workflows_tested
        }
