# crawler/metric.py

def calculate_streak_metric(update_times: list, visit_times: list) -> float:
    """
    Calculates the 'Sum of Squared Lengths' metric.
    Goal: Alternating updates (u) and visits (v).
    """
    if not update_times and not visit_times: return 0.0

    # Merge events
    events = []
    for t in update_times: events.append((t, 'u'))
    for t in visit_times: events.append((t, 'v'))
    events.sort(key=lambda x: x[0]) # Sort by time

    if not events: return 0.0

    streaks = []
    current_type = events[0][1]
    current_length = 0
    
    for _, event_type in events:
        if event_type == current_type:
            current_length += 1
        else:
            streaks.append(current_length)
            current_type = event_type
            current_length = 1
    streaks.append(current_length) # Last one
    
    # Metric: Average of (Streak_Length^2)
    score = sum(L**2 for L in streaks) / len(events)
    return score