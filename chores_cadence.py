import csv
from collections import defaultdict
import hashlib

INTERVALS_PER_MONTH = {
    'daily': 30,
    'every_other': 15,
    'twice_weekly': 8,
    'weekly': 4,
    'biweekly': 2,
    'monthly': 1,
}

NUM_DAYS = 30

# Load chores and intervals
chore_intervals = {}
chore_intervals_raw = {}
with open("chore_schedule_by_interval.csv", newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        chore = row["chore"].strip()
        interval_raw = row["interval"].strip().lower()
        chore_intervals_raw[chore] = interval_raw
        if interval_raw in INTERVALS_PER_MONTH:
            chore_intervals[chore] = INTERVALS_PER_MONTH[interval_raw]
        else:
            print(f"⚠️ Unknown interval '{interval_raw}' for chore '{chore}' — skipping.")

schedule = defaultdict(list)

def get_stagger_offset(chore, spacing):
    h = int(hashlib.md5(chore.encode()).hexdigest(), 16)
    return h % int(spacing) if spacing >= 1 else 0

def is_safe_to_schedule(day, chore, schedule):
    chores_today = schedule[day]
    # No duplicate chores on the same day
    if chore in chores_today:
        return False
    # Daily chores can repeat any day
    if chore_intervals_raw.get(chore, "") == "daily":
        return True
    # For others, avoid adjacent duplicate chores
    for d in [day - 1, day + 1]:
        if chore in schedule[d % NUM_DAYS]:
            return False
    return True

def dusting_this_week(day, schedule):
    # Check if any dusting chore already scheduled this week (7-day window)
    week_start = day - (day % 7)
    for d in range(week_start, week_start + 7):
        if d >= NUM_DAYS:
            break
        for chore in schedule[d]:
            if chore.startswith("dust "):
                return True
    return False

# Initial scheduling
for chore, freq in chore_intervals.items():
    spacing = NUM_DAYS / freq if freq else NUM_DAYS
    offset = get_stagger_offset(chore, spacing)
    placed = 0
    attempts = 0

    while placed < freq and attempts < NUM_DAYS * 2:
        day = int(round(offset + spacing * placed)) % NUM_DAYS

        for _ in range(NUM_DAYS):
            # Dusting constraints:
            if chore.startswith("dust "):
                # Only one dust chore per week
                if dusting_this_week(day, schedule):
                    day = (day + 1) % NUM_DAYS
                    continue
                # Dusting requires tidy on same day
                if "tidy" not in schedule[day]:
                    # Try to schedule tidy first if safe
                    if is_safe_to_schedule(day, "tidy", schedule):
                        schedule[day].append("tidy")
                    else:
                        day = (day + 1) % NUM_DAYS
                        continue

            # Mop requires sweep on same day (and schedules sweep if needed)
            if chore == "mop":
                if "sweep" not in schedule[day]:
                    if is_safe_to_schedule(day, "sweep", schedule):
                        schedule[day].append("sweep")
                    else:
                        day = (day + 1) % NUM_DAYS
                        continue

            if is_safe_to_schedule(day, chore, schedule):
                schedule[day].append(chore)
                placed += 1
                break

            day = (day + 1) % NUM_DAYS

        attempts += 1

    if placed < freq:
        print(f"⚠️ Could only place {placed}/{freq} for chore '{chore}'.")

# Redistribution step to balance chores per day
MAX_ITERATIONS = 100
for _ in range(MAX_ITERATIONS):
    day_counts = {day: len(tasks) for day, tasks in schedule.items()}
    max_day = max(day_counts, key=day_counts.get)
    min_day = min(day_counts, key=day_counts.get)

    if day_counts[max_day] - day_counts[min_day] <= 1:
        break

    moved = False
    for chore in schedule[max_day]:
        # Dusting constraints during move:
        if chore.startswith("dust "):
            # Only move if min_day has no dust chore this week and tidy can be scheduled if missing
            if dusting_this_week(min_day, schedule):
                continue
            if "tidy" not in schedule[min_day]:
                if not is_safe_to_schedule(min_day, "tidy", schedule):
                    continue

        # Mop/sweep pairing during move
        if chore == "mop":
            if "sweep" not in schedule[min_day]:
                if is_safe_to_schedule(min_day, "sweep", schedule):
                    schedule[min_day].append("sweep")
                    schedule[max_day].remove("sweep")
                else:
                    continue
        elif chore == "sweep":
            if "mop" in schedule[max_day]:
                if is_safe_to_schedule(min_day, "mop", schedule):
                    schedule[min_day].append("mop")
                    schedule[max_day].remove("mop")
                else:
                    continue

        if is_safe_to_schedule(min_day, chore, schedule):
            schedule[min_day].append(chore)
            schedule[max_day].remove(chore)
            # Add tidy if dust chore moved and tidy missing on min_day
            if chore.startswith("dust ") and "tidy" not in schedule[min_day]:
                schedule[min_day].append("tidy")
            moved = True
            break

    if not moved:
        break

# Write final balanced schedule
with open("interval_chore_schedule_balanced.txt", "w") as f:
    for day in range(NUM_DAYS):
        f.write(f"Day {day + 1}:\n")
        chores = sorted(schedule[day])
        if chores:
            for chore in chores:
                f.write(f"  - {chore}\n")
        else:
            f.write("  (no chores)\n")
        f.write("\n")

print("✅ Balanced interval-based chore schedule saved to 'interval_chore_schedule_balanced.txt'")
