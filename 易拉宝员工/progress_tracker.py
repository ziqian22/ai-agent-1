"""
进度跟踪器
用于跟踪易拉宝生成过程的进度和状态
"""

import time
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


class TaskStep(Enum):
    """任务步骤枚举"""
    UPLOAD_IMAGE = "上传图片"
    ANALYZE_IMAGE = "分析图片"
    GENERATE_PROMPT = "生成提示词"
    CALL_API = "调用生成API"
    PROCESS_RESULT = "处理结果"
    COMPLETED = "完成"


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"      # 待处理
    RUNNING = "running"      # 进行中
    SUCCESS = "success"      # 成功
    FAILED = "failed"        # 失败


class ProgressTracker:
    """进度跟踪器"""

    def __init__(self):
        self.current_step: Optional[TaskStep] = None
        self.steps_status: Dict[TaskStep, TaskStatus] = {}
        self.logs: List[Dict[str, Any]] = []
        self.start_time: Optional[float] = None
        self.total_steps = len(TaskStep)
        self.completed_steps = 0

        # 初始化所有步骤为待处理
        for step in TaskStep:
            self.steps_status[step] = TaskStatus.PENDING

    def start_task(self):
        """开始任务"""
        self.start_time = time.time()
        self.add_log("任务开始")

    def start_step(self, step: TaskStep):
        """开始某个步骤"""
        self.current_step = step
        self.steps_status[step] = TaskStatus.RUNNING
        self.add_log(f"开始: {step.value}")

    def complete_step(self, step: TaskStep, success: bool = True):
        """完成某个步骤"""
        if success:
            self.steps_status[step] = TaskStatus.SUCCESS
            self.completed_steps += 1
            self.add_log(f"完成: {step.value}")
        else:
            self.steps_status[step] = TaskStatus.FAILED
            self.add_log(f"失败: {step.value}")

    def add_log(self, message: str, level: str = "info"):
        """
        添加日志

        Args:
            message: 日志消息
            level: 日志级别 (info/warning/error)
        """
        log_entry = {
            "time": datetime.now().strftime("%H:%M:%S"),
            "message": message,
            "level": level
        }
        self.logs.append(log_entry)

    def get_progress_percentage(self) -> int:
        """
        获取进度百分比

        Returns:
            进度百分比 (0-100)
        """
        if self.total_steps == 0:
            return 0
        return int((self.completed_steps / self.total_steps) * 100)

    def get_eta(self) -> str:
        """
        估算剩余时间

        Returns:
            剩余时间字符串
        """
        if not self.start_time or self.completed_steps == 0:
            return "计算中..."

        elapsed = time.time() - self.start_time
        avg_time_per_step = elapsed / self.completed_steps
        remaining_steps = self.total_steps - self.completed_steps
        eta_seconds = int(avg_time_per_step * remaining_steps)

        if eta_seconds < 60:
            return f"{eta_seconds}秒"
        else:
            minutes = eta_seconds // 60
            seconds = eta_seconds % 60
            return f"{minutes}分{seconds}秒"

    def get_step_status_icon(self, step: TaskStep) -> str:
        """
        获取步骤状态图标

        Args:
            step: 任务步骤

        Returns:
            状态图标
        """
        status = self.steps_status.get(step, TaskStatus.PENDING)

        if status == TaskStatus.SUCCESS:
            return "✅"
        elif status == TaskStatus.RUNNING:
            return "⏳"
        elif status == TaskStatus.FAILED:
            return "❌"
        else:
            return "⚪"

    def get_progress_summary(self) -> Dict[str, Any]:
        """
        获取进度摘要

        Returns:
            进度摘要字典
        """
        return {
            "current_step": self.current_step.value if self.current_step else None,
            "percentage": self.get_progress_percentage(),
            "eta": self.get_eta(),
            "steps": [
                {
                    "name": step.value,
                    "status": self.steps_status[step].value,
                    "icon": self.get_step_status_icon(step)
                }
                for step in TaskStep
            ],
            "logs": self.logs[-10:]  # 最近10条日志
        }

    def reset(self):
        """重置跟踪器"""
        self.__init__()


class MultiTaskProgressTracker:
    """多任务进度跟踪器（用于批量生成）"""

    def __init__(self):
        self.tasks: Dict[str, ProgressTracker] = {}

    def create_task(self, task_id: str) -> ProgressTracker:
        """
        创建新任务

        Args:
            task_id: 任务ID

        Returns:
            进度跟踪器
        """
        tracker = ProgressTracker()
        self.tasks[task_id] = tracker
        return tracker

    def get_task(self, task_id: str) -> Optional[ProgressTracker]:
        """
        获取任务跟踪器

        Args:
            task_id: 任务ID

        Returns:
            进度跟踪器
        """
        return self.tasks.get(task_id)

    def get_all_tasks_summary(self) -> List[Dict[str, Any]]:
        """
        获取所有任务的摘要

        Returns:
            任务摘要列表
        """
        return [
            {
                "task_id": task_id,
                "progress": tracker.get_progress_summary()
            }
            for task_id, tracker in self.tasks.items()
        ]

    def get_overall_progress(self) -> int:
        """
        获取总体进度

        Returns:
            总体进度百分比
        """
        if not self.tasks:
            return 0

        total_progress = sum(
            tracker.get_progress_percentage()
            for tracker in self.tasks.values()
        )
        return int(total_progress / len(self.tasks))

    def remove_task(self, task_id: str):
        """删除任务"""
        if task_id in self.tasks:
            del self.tasks[task_id]

    def clear_completed_tasks(self):
        """清除已完成的任务"""
        completed_tasks = [
            task_id for task_id, tracker in self.tasks.items()
            if tracker.completed_steps == tracker.total_steps
        ]
        for task_id in completed_tasks:
            del self.tasks[task_id]


# 测试代码
if __name__ == "__main__":
    import time

    print("=" * 60)
    print("进度跟踪器测试")
    print("=" * 60)

    # 单任务测试
    print("\n【单任务测试】")
    tracker = ProgressTracker()
    tracker.start_task()

    for step in TaskStep:
        tracker.start_step(step)
        print(f"\n当前步骤: {step.value}")
        print(f"进度: {tracker.get_progress_percentage()}%")
        print(f"预计剩余: {tracker.get_eta()}")

        time.sleep(0.5)  # 模拟处理时间
        tracker.complete_step(step)

    print("\n最终摘要:")
    summary = tracker.get_progress_summary()
    print(f"进度: {summary['percentage']}%")
    print(f"步骤状态:")
    for step_info in summary['steps']:
        print(f"  {step_info['icon']} {step_info['name']}")

    # 多任务测试
    print("\n" + "=" * 60)
    print("【多任务测试】")
    multi_tracker = MultiTaskProgressTracker()

    # 创建3个任务
    for i in range(3):
        task_id = f"task_{i+1}"
        task_tracker = multi_tracker.create_task(task_id)
        task_tracker.start_task()

        # 模拟不同进度
        for j, step in enumerate(TaskStep):
            if j <= i:  # 不同任务完成不同数量的步骤
                task_tracker.start_step(step)
                task_tracker.complete_step(step)

    print(f"\n总体进度: {multi_tracker.get_overall_progress()}%")
    print("\n各任务状态:")
    for task_summary in multi_tracker.get_all_tasks_summary():
        print(f"  {task_summary['task_id']}: {task_summary['progress']['percentage']}%")
