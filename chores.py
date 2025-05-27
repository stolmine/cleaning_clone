import csv
from collections import defaultdict
from math import floor
from itertools import cycle

# Load chores from CSV
chore_data = {}
with open("updated_chore_schedule.csv", newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        chore_data[row["chore"]] = {
            "difficulty": int(row["difficulty"]),
            "frequency": int(row["frequency_per_month"])
        }

# Define grouped chores
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

# Create grouped tasks and track used chores
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

# Add remaining ungrouped chores
for chore, info in chore_data.items():
    if info["frequency"] > 0:
        for _ in range(info["frequency"]):
            grouped_tasks.append({
                "chore": chore,
                "difficulty": info["difficulty"]
            })

# Group tasks by chore for spacing
tasks_by_chore = defaultdict(list)
for task in grouped_tasks:
    tasks_by_chore[task["chore"]].append(task)

# Initialize schedule
days = defaultdict(list)
day_difficulties = [0] * 30
unplaced_tasks = []

# Check if a chore already exists today or the day before/after
def is_valid_day(day, chore):
    today = {t["chore"] for t in days[day]}
    prev_day = {t["chore"] for t in days[day - 1]} if day > 0 else set()
    next_day = {t["chore"] for t in days[day + 1]} if day < 29 else set()
    return chore not in today and chore not in prev_day and chore not in next_day

# Assign tasks at even intervals and smooth difficulty
for chore, chore_tasks in tasks_by_chore.items():
    freq = len(chore_tasks)
    if freq == 0:
        continue
    interval = 30 / freq
    offsets = [floor(i * interval) for i in range(freq)]
    attempts = cycle(range(30))

    for i, task in enumerate(chore_tasks):
        placed = False
        base_day = offsets[i]

        # Try preferred day and shift forward if needed
        for delta in range(30):
            day = (base_day + delta) % 30
            if is_valid_day(day, task["chore"]) and day_difficulties[day] + task["difficulty"] <= 15:
                days[day].append(task)
                day_difficulties[day] += task["difficulty"]
                placed = True
                break

        if not placed:
            for day in range(30):
                if task["chore"] not in [t["chore"] for t in days[day]] and day_difficulties[day] + task["difficulty"] <= 15:
                    days[day].append(task)
                    day_difficulties[day] += task["difficulty"]
                    placed = True
                    break

        if not placed:
            unplaced_tasks.append(task)

# Sort tasks by ascending difficulty per day and write to file
with open("monthly_chore_schedule.txt", "w") as f:
    for day in range(30):
        sorted_tasks = sorted(days[day], key=lambda x: x["difficulty"])
        total_difficulty = sum(t["difficulty"] for t in sorted_tasks)
        f.write(f"Day {day + 1} (Total difficulty: {total_difficulty})\n")
        for task in sorted_tasks:
            f.write(f"  - {task['chore']} (difficulty {task['difficulty']})\n")
        f.write("\n")

    if unplaced_tasks:
        f.write("Unplaced Tasks (could not be scheduled due to constraints):\n")
        for task in sorted(unplaced_tasks, key=lambda t: t["difficulty"]):
            f.write(f"  - {task['chore']} (difficulty {task['difficulty']})\n")

print("✅ Balanced and spaced schedule written to 'monthly_chore_schedule.txt'")
