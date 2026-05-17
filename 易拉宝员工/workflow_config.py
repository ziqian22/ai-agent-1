import json
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime


class WorkflowConfig:
    """工作流配置管理"""

    def __init__(self, config_file: str = "workflows.json"):
        self.config_file = config_file
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """加载配置文件"""
        if Path(self.config_file).exists():
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"workflows": [], "test_history": []}

    def _save_config(self):
        """保存配置文件"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)

    def add_workflow(self, workflow_id: str, name: str, description: str,
                     workflow_type: str = "workflow",
                     node_info_template: List[Dict] = None) -> bool:
        """
        添加工作流配置

        Args:
            workflow_id: 工作流ID
            name: 工作流名称
            description: 工作流描述
            workflow_type: 工作流类型 ("workflow" 或 "ai-app")
            node_info_template: 节点参数模板

        Returns:
            是否成功
        """
        # 检查是否已存在
        for wf in self.config['workflows']:
            if wf['id'] == workflow_id:
                print(f"工作流 {workflow_id} 已存在")
                return False

        workflow = {
            "id": workflow_id,
            "name": name,
            "description": description,
            "type": workflow_type,
            "node_info_template": node_info_template or [],
            "created_at": datetime.now().isoformat()
        }

        self.config['workflows'].append(workflow)
        self._save_config()
        return True

    def get_workflow(self, workflow_id: str) -> Optional[Dict]:
        """获取工作流配置"""
        for wf in self.config['workflows']:
            if wf['id'] == workflow_id:
                return wf
        return None

    def get_all_workflows(self) -> List[Dict]:
        """获取所有工作流"""
        return self.config['workflows']

    def update_workflow(self, workflow_id: str, **kwargs) -> bool:
        """
        更新工作流配置

        Args:
            workflow_id: 工作流ID
            **kwargs: 要更新的字段

        Returns:
            是否成功
        """
        for wf in self.config['workflows']:
            if wf['id'] == workflow_id:
                wf.update(kwargs)
                wf['updated_at'] = datetime.now().isoformat()
                self._save_config()
                return True
        return False

    def delete_workflow(self, workflow_id: str) -> bool:
        """删除工作流配置"""
        original_len = len(self.config['workflows'])
        self.config['workflows'] = [
            wf for wf in self.config['workflows']
            if wf['id'] != workflow_id
        ]

        if len(self.config['workflows']) < original_len:
            self._save_config()
            return True
        return False

    def add_node_info(self, workflow_id: str, node_id: str,
                     field_name: str, field_type: str = "text",
                     description: str = "", default_value: str = "") -> bool:
        """
        为工作流添加节点参数配置

        Args:
            workflow_id: 工作流ID
            node_id: 节点ID
            field_name: 字段名
            field_type: 字段类型 (text, image, number, select)
            description: 描述
            default_value: 默认值

        Returns:
            是否成功
        """
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            return False

        node_info = {
            "nodeId": node_id,
            "fieldName": field_name,
            "fieldType": field_type,
            "description": description,
            "defaultValue": default_value
        }

        workflow['node_info_template'].append(node_info)
        self._save_config()
        return True

    def remove_node_info(self, workflow_id: str, node_id: str, field_name: str) -> bool:
        """删除节点参数配置"""
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            return False

        original_len = len(workflow['node_info_template'])
        workflow['node_info_template'] = [
            ni for ni in workflow['node_info_template']
            if not (ni['nodeId'] == node_id and ni['fieldName'] == field_name)
        ]

        if len(workflow['node_info_template']) < original_len:
            self._save_config()
            return True
        return False
