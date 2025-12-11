from __future__ import annotations



from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class Task:
    """A single task in the system."""
    id: str
    title: str
    created_at: datetime
    completed: bool = False
    due_date: Optional[datetime] = None

    def mark_done(self) -> None:
        """Mark this task as completed."""
        self.completed = True
        

    def is_overdue(self, now: Optional[datetime] = None) -> bool:
        """Return True if the task is overdue."""
        if self.due_date is None:
            return False
        current_time = now or datetime.utcnow()
        return not self.completed and current_time > self.due_date


class TaskRepository:
    """Simple in-memory repository for tasks."""

    def __init__(self) -> None:
        self._tasks: Dict[str, Task] = {}

    def save(self, task: Task) -> None:
        """Insert or update a task."""
        self._tasks[task.id] = task

    def get(self, task_id: str) -> Optional[Task]:
        """Return a task by its identifier."""
        return self._tasks.get(task_id)

    def list_all(self) -> List[Task]:
        """Return all tasks."""
        return list(self._tasks.values())

    def delete(self, task_id: str) -> None:
        """Delete a task if it exists."""
        self._tasks.pop(task_id, None)


class TaskService:
    """High-level API for working with tasks."""

    def __init__(self, repository: TaskRepository) -> None:
        self._repository = repository

    def create_task(
        self,
        task_id: str,
        title: str,
        due_date: Optional[datetime] = None,
    ) -> Task:
        """Create and store a new task."""
        task = Task(
            id=task_id,
            title=title,
            created_at=datetime.utcnow(),
            due_date=due_date,
        )
        self._repository.save(task)
        return task

    def complete_task(self, task_id: str) -> bool:
        """Mark a task as completed. Returns True if successful."""
        task = self._repository.get(task_id)
        if task is None:
            return False
        task.mark_done()
        self._repository.save(task)
        return True

    def get_summary(self) -> dict:
        """Return a small summary of open vs completed tasks."""
        tasks = self._repository.list_all()
        total = len(tasks)
        done = sum(1 for t in tasks if t.completed)
        open_tasks = total - done
        overdue = sum(1 for t in tasks if t.is_overdue())
        return {
            "total": total,
            "completed": done,
            "open": open_tasks,
            "overdue": overdue,
        }


def build_sample_data() -> TaskService:
    """Create a TaskService pre-populated with a few tasks."""
    repo = TaskRepository()
    service = TaskService(repo)

    service.create_task("T-1", "Read assignment brief")
    service.create_task("T-2", "Implement workflow engine")
    service.create_task("T-3", "Write README")
    return service


if __name__ == "__main__":
    service = build_sample_data()
    service.complete_task("T-1")
    summary = service.get_summary()
    print("Task summary:", summary)

