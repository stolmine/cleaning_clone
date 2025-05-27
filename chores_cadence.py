import csv
from collections import defaultdict
import hashlib

# Define how many times per month each interval represents
INTERVALS_PER_MONTH = {
    'daily': 30,
    'every_other': 15,
    'twice_weekly': 8,
    'weekly': 4,
    'biweekly': 2,
    'monthly': 1,
}

NUM_DAYS = 30

# Load chores from CSV
chore_intervals = {}
chore_intervals_raw = {}  # keep raw interval string for logic
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

# Create schedule containers
schedule = defaultdict(list)

# Hash chore name into a starting offset for staggering
def get_stagger_offset(chore, spacing):
    h = int(hashlib.md5(chore.encode()).hexdigest(), 16)
    return h % int(spacing) if spacing >= 1 else 0

# Check that same chore isn't on an adjacent day (only if not daily)
def is_safe_to_schedule(day, chore):
    # If chore is daily, no adjacency rule
    if chore_intervals_raw.get(chore, "") == "daily":
        return True
    # Otherwise, check adjacent days
    return all(
        chore not in schedule[d % NUM_DAYS]
        for d in [day - 1, day, day + 1]
    )

# Main scheduling loop
for chore, freq in chore_intervals.items():
    spacing = NUM_DAYS / freq if freq else NUM_DAYS
    offset = get_stagger_offset(chore, spacing)
    placed = 0
    attempts = 0

    while placed < freq and attempts < NUM_DAYS * 2:
        day = int(round(offset + spacing * placed)) % NUM_DAYS

        # Try up to NUM_DAYS days to find safe placement
        for _ in range(NUM_DAYS):
            if is_safe_to_schedule(day, chore):
                schedule[day].append(chore)
                placed += 1
                break
            day = (day + 1) % NUM_DAYS

        attempts += 1

    if placed < freq:
        print(f"⚠️ Could only place {placed}/{freq} for chore '{chore}'.")

# Write the final schedule
with open("interval_chore_schedule.txt", "w") as f:
    for day in range(NUM_DAYS):
        f.write(f"Day {day + 1}:\n")
        chores = sorted(schedule[day])
        if chores:
            for chore in chores:
                f.write(f"  - {chore}\n")
        else:
            f.write("  (no chores)\n")
        f.write("\n")

print("✅ Interval-based chore schedule saved to 'interval_chore_schedule.txt'")
