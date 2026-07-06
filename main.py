import json
from datetime import datetime
from functools import wraps

TASKS_FILE = "tasks.jsonl"
LOG_FILE = "log.txt"


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

    try:
        with open(TASKS_FILE, "r") as file:
            for line in file:
                line = line.strip()
                if line:
                    tasks.append(json.loads(line))

    except FileNotFoundError:
        return []

    except json.JSONDecodeError:
        return []

    return tasks


@log_call
def save_tasks(tasks):
    with open(TASKS_FILE, "w") as file:
        for task in tasks:
            file.write(json.dumps(task) + "\n")


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
            for line in file:
                line = line.strip()

                if line:
                    yield json.loads(line)

    except FileNotFoundError:
        return

    except json.JSONDecodeError:
        return


@log_call
def main():
    tasks = load_tasks()

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

                for task in read_tasks_generator(TASKS_FILE):
                    status = "✓" if task["completed"] else "✗"
                    print(f"{task['id']}. {task['title']} [{status}]")

            elif choice == 6:
                print("Goodbye!")
                break

            else:
                print("Invalid choice.")

        except ValueError:
            print("Please enter a valid number.")


if __name__ == "__main__":
    main()