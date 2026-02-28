"""
记忆系统 - 存储任务结果和学习经验
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

class MemorySystem:
    """长期记忆系统"""

    def __init__(self, data_dir: str = None):
        if data_dir is None:
            data_dir = Path(__file__).parent.parent.parent / "data" / "memory"
        else:
            data_dir = Path(data_dir)

        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.tasks_file = self.data_dir / "tasks.json"
        self.insights_file = self.data_dir / "insights.json"

        # 初始化文件
        if not self.tasks_file.exists():
            self._write_json(self.tasks_file, [])
        if not self.insights_file.exists():
            self._write_json(self.insights_file, [])

    def _read_json(self, file_path: Path) -> Any:
        """读取JSON文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []

    def _write_json(self, file_path: Path, data: Any):
        """写入JSON文件"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def save_task_result(self, task: str, result: Any):
        """保存任务结果"""
        tasks = self._read_json(self.tasks_file)

        tasks.append({
            "task": task,
            "result": str(result)[:2000],  # 限制长度
            "timestamp": datetime.now().isoformat()
        })

        # 只保留最近100条
        if len(tasks) > 100:
            tasks = tasks[-100:]

        self._write_json(self.tasks_file, tasks)

    def get_recent_tasks(self, limit: int = 10) -> List[Dict]:
        """获取最近的任务"""
        tasks = self._read_json(self.tasks_file)
        return tasks[-limit:] if len(tasks) >= limit else tasks

    def save_insight(self, category: str, content: str):
        """保存洞察"""
        insights = self._read_json(self.insights_file)

        insights.append({
            "category": category,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })

        self._write_json(self.insights_file, insights)

    def get_insights(self, category: str = None) -> List[Dict]:
        """获取洞察"""
        insights = self._read_json(self.insights_file)

        if category:
            return [i for i in insights if i.get("category") == category]

        return insights

    def search(self, keyword: str) -> List[Dict]:
        """搜索记忆"""
        results = []

        # 搜索任务
        tasks = self._read_json(self.tasks_file)
        for task in tasks:
            if keyword.lower() in str(task.get("task", "")).lower():
                results.append(task)

        # 搜索洞察
        insights = self._read_json(self.insights_file)
        for insight in insights:
            if keyword.lower() in str(insight.get("content", "")).lower():
                results.append(insight)

        return results
