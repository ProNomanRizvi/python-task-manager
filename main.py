import json
import os
import tempfile
from pathlib import Path
from datetime import datetime
from functools import wraps

TASKS_FILE = "tasks.jsonl"
LOG_FILE = "log.txt"


class TaskDataError(ValueError):
    """Stored task data is invalid; do not overwrite it."""


def parse_task(line, line_number):
    try:
        task = json.loads(line)
    except json.JSONDecodeError as exc:
        raise TaskDataError(f"Invalid JSON on line {line_number}.") from exc

    if (
        not isinstance(task, dict)
        or isinstance(task.get("id"), bool)
        or not isinstance(task.get("id"), int)
        or task["id"] < 1
        or not isinstance(task.get("title"), str)
        or not task["title"].strip()
        or not isinstance(task.get("completed"), bool)
        or not isinstance(task.get("created_at"), str)
    ):
        raise TaskDataError(f"Invalid task on line {line_number}.")
    return task


def log_call(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        with open(LOG_FILE, "a") as file:
            file.write(
                f"{datetime.now().isoformat()} | "
                f"{func.__name__} | "
                f"args={args} | kwargs={kwargs}\n"
            )
        return func(*args, **kwargs)

    return wrapper


@log_call
def load_tasks():
    tasks = []
    seen_ids = set()

    try:
        with open(TASKS_FILE, "r") as file:
            for line_number, line in enumerate(file, start=1):
                if not line.strip():
                    continue
                task = parse_task(line, line_number)
                if task["id"] in seen_ids:
                    raise TaskDataError(f"Duplicate task ID on line {line_number}.")
                seen_ids.add(task["id"])
                tasks.append(task)
    except FileNotFoundError:
        return []

    return tasks


@log_call
def save_tasks(tasks):
    """Replace the task file only after the complete new version is written."""
    path = Path(TASKS_FILE)
    temp_name = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent,
            prefix=f".{path.name}.", suffix=".tmp", delete=False
        ) as temp_file:
            temp_name = temp_file.name
            seen_ids = set()
            for line_number, task in enumerate(tasks, start=1):
                # Validate before replacing the existing file.
                task = parse_task(json.dumps(task), line_number)
                if task["id"] in seen_ids:
                    raise TaskDataError(f"Duplicate task ID on line {line_number}.")
                seen_ids.add(task["id"])
                temp_file.write(json.dumps(task) + "\n")
            temp_file.flush()
            os.fsync(temp_file.fileno())
        os.replace(temp_name, path)
    finally:
        if temp_name is not None and os.path.exists(temp_name):
            os.unlink(temp_name)


@log_call
def add_task(tasks, title):
    new_id = max((task["id"] for task in tasks), default=0) + 1

    tasks.append(
        {
            "id": new_id,
            "title": title,
            "completed": False,
            "created_at": datetime.now().strftime("%Y-%m-%d, %I:%M %p"),
        }
    )
    print(f"{title} Added")


@log_call
def mark_complete(tasks, task_id):
    for task in tasks:
        if task["id"] == task_id:
            task["completed"] = True
            print("Task marked as completed.")
            return True

    print("Task ID not found.")
    return False


@log_call
def delete_task(tasks, task_id):
    for task in tasks:
        if task["id"] == task_id:
            tasks.remove(task)
            print("Task deleted successfully.")
            return True

    print("Task ID not found.")
    return False


@log_call
def list_tasks(tasks):
    if not tasks:
        print("No tasks found.")
        return

    print("\nTasks:")
    for task in tasks:
        status = "✓" if task["completed"] else "✗"
        print(f"{task['id']}. {task['title']} [{status}]")


def read_tasks_generator(filepath):
    try:
        with open(filepath, "r") as file:
            seen_ids = set()
            for line_number, line in enumerate(file, start=1):
                if not line.strip():
                    continue
                task = parse_task(line, line_number)
                if task["id"] in seen_ids:
                    raise TaskDataError(f"Duplicate task ID on line {line_number}.")
                seen_ids.add(task["id"])
                yield task
    except FileNotFoundError:
        return


@log_call
def main():
    try:
        tasks = load_tasks()
    except TaskDataError as exc:
        print(f"Cannot load tasks: {exc}")
        print(f"Original file preserved: {TASKS_FILE}. Repair it before editing tasks.")
        return

    while True:
        print("\n===== TO-DO MENU =====")
        print("1. Add Task")
        print("2. Complete Task")
        print("3. Delete Task")
        print("4. List Tasks")
        print("5. View Tasks (Generator)")
        print("6. Exit")

        try:
            choice = int(input("Enter choice: "))

            if choice == 1:
                title = input("Task title: ").strip()
                if title:
                    add_task(tasks, title)
                    save_tasks(tasks)
                else:
                    print("Title cannot be empty.")

            elif choice == 2:
                task_id = int(input("Task ID: "))
                if mark_complete(tasks, task_id):
                    save_tasks(tasks)

            elif choice == 3:
                task_id = int(input("Task ID: "))
                if delete_task(tasks, task_id):
                    save_tasks(tasks)

            elif choice == 4:
                list_tasks(tasks)

            elif choice == 5:
                print("\nTasks (Generator):")

                try:
                    for task in read_tasks_generator(TASKS_FILE):
                        status = "✓" if task["completed"] else "✗"
                        print(f"{task['id']}. {task['title']} [{status}]")
                except TaskDataError as exc:
                    print(f"Cannot display tasks: {exc}")

            elif choice == 6:
                print("Goodbye!")
                break

            else:
                print("Invalid choice.")

        except ValueError:
            print("Please enter a valid number.")


if __name__ == "__main__":
    main()
