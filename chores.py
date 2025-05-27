import csv
from collections import defaultdict

# Load chores from CSV
chore_data = {}
with open("updated_chore_schedule.csv", newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        chore_data[row["chore"]] = {
            "difficulty": int(row["difficulty"]),
            "frequency": int(row["frequency_per_month"])
        }

# Define chore groups — pair tidy with each dust chore individually
group_definitions = {
    "tidy + dust living room": ["tidy", "dust living room"],
    "tidy + dust dining room": ["tidy", "dust dining room"],
    "tidy + dust bedroom": ["tidy", "dust bedroom"],
    "tidy + dust office": ["tidy", "dust office"],
    "sweep + mop": ["sweep", "mop"],
    "trash + recycling": ["trash", "recycling"],
    "fridge cleanout + surfaces": ["fridge cleanout", "fridge surfaces"],
    "bathroom surfaces + floor": ["bathroom surfaces", "bathroom floor"]
}

# Build list of grouped chores with adjusted frequencies
grouped_tasks = []
used = set()

for group_name, members in group_definitions.items():
    freqs = [chore_data[ch]["frequency"] for ch in members if ch in chore_data]
    if not freqs:
        continue
    freq = min(freqs)
    difficulty = sum(chore_data[ch]["difficulty"] for ch in members if ch in chore_data)
    for _ in range(freq):
        grouped_tasks.append({
            "chore": group_name,
            "difficulty": difficulty
        })
    for ch in members:
        if ch in chore_data:
            chore_data[ch]["frequency"] -= freq
            used.add(ch)

# Add remaining ungrouped tasks
for chore, info in chore_data.items():
    if chore in used or info["frequency"] <= 0:
        continue
    for _ in range(info["frequency"]):
        grouped_tasks.append({
            "chore": chore,
            "difficulty": info["difficulty"]
        })

from math import ceil
from collections import defaultdict

# Count frequencies of tasks in grouped_tasks
freq_count = defaultdict(int)
for t in grouped_tasks:
    freq_count[t["chore"]] += 1

# Organize tasks by chore name for scheduling evenly
tasks_by_chore = defaultdict(list)
for task in grouped_tasks:
    tasks_by_chore[task["chore"]].append(task)

# Prepare schedule containers
days = defaultdict(list)
day_difficulties = [0] * 30
limit_per_day = 15  # Adjusted daily difficulty limit

unplaced_tasks = []

# Function to find next suitable day for a task, checking duplicates and difficulty limit
def find_day_for_task(start_day, chore, difficulty):
    for offset in range(30):
        day = (start_day + offset) % 30
        chores_today = {t["chore"] for t in days[day]}
        if (day_difficulties[day] + difficulty <= limit_per_day) and (chore not in chores_today):
            return day
    return None  # no suitable day found

# Assign tasks evenly spaced across days
for chore, tasks in tasks_by_chore.items():
    freq = len(tasks)
    if freq == 0:
        continue
    interval = 30 / freq
    for i, task in enumerate(tasks):
        approx_day = int(round(i * interval)) % 30
        day = find_day_for_task(approx_day, chore, task["difficulty"])
        if day is None:
            # fallback
            day = find_day_for_task(0, chore, task["difficulty"])
            if day is None:
                unplaced_tasks.append(task)
                continue
        days[day].append(task)
        day_difficulties[day] += task["difficulty"]

# Write output to a text file with tasks sorted ascending by difficulty per day
with open("monthly_chore_schedule.txt", "w") as f:
    for day in range(30):
        f.write(f"Day {day + 1} (Total difficulty: {day_difficulties[day]})\n")
        sorted_tasks = sorted(days[day], key=lambda t: t["difficulty"])
        for task in sorted_tasks:
            f.write(f"  - {task['chore']} (difficulty {task['difficulty']})\n")
        f.write("\n")

    if unplaced_tasks:
        f.write("Unplaced Tasks (could not be scheduled due to difficulty or duplicates):\n")
        for task in sorted(unplaced_tasks, key=lambda t: t["difficulty"]):
            f.write(f"  - {task['chore']} (difficulty {task['difficulty']})\n")

print("✅ Schedule saved with tidy + individual dusting tasks grouped separately")
