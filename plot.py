import matplotlib.pyplot as plt
import pandas as pd  # For rolling averages

def calculate_statistics(big_data, time_steps):
    """
    Calculate average, min, and max statistics for the entire dataset.
    """
    used_beds = [[data.get(key, None) for key in time_steps] for data in big_data]

    average_used_beds = []
    min_used_beds = []
    max_used_beds = []
    for i in range(len(time_steps)):
        values = [beds[i] for beds in used_beds if beds[i] is not None]
        average_used_beds.append(sum(values) / len(values) if len(values)!=0 else 0)
        min_used_beds.append(min(values))
        max_used_beds.append(max(values))

    return average_used_beds, min_used_beds, max_used_beds

def create_plot(department, big_data, y_label, title_suffix, smoothing_window=50):
    """
    Creates a cleaner plot by using rolling averages and shaded variance.
    """
    # Get all unique keys
    all_keys = set()
    for data in big_data:
        all_keys.update(data.keys())
    time_steps = sorted(all_keys)

    # Calculate overall statistics
    average_used_beds, min_used_beds, max_used_beds = calculate_statistics(big_data, time_steps)

    # Apply rolling average to smooth the data
    average_smoothed = pd.Series(average_used_beds).rolling(window=smoothing_window, min_periods=1).mean()
    min_smoothed = pd.Series(min_used_beds).rolling(window=smoothing_window, min_periods=1).mean()
    max_smoothed = pd.Series(max_used_beds).rolling(window=smoothing_window, min_periods=1).mean()

    # Create the plot
    plt.figure(figsize=(12, 6))

    # Plot the shaded area (smoothed min/max range)
    plt.fill_between(
        time_steps,
        min_smoothed,
        max_smoothed,
        color='lightblue',
        alpha=0.5,
        label='Smoothed Min/Max Range'
    )

    # Plot the smoothed average line
    plt.plot(time_steps, average_smoothed, color='steelblue', label='Smoothed Average', linewidth=2)

    # Add labels and legend
    plt.xlabel('Step', fontsize=12)
    plt.ylabel(y_label, fontsize=12)
    plt.title(f'{title_suffix} of {department} per Step', fontsize=14)
    plt.legend(fontsize=10)

    plt.tight_layout()
    plt.show()

def create_queue_plot(department, big_data, smoothing_window=50):
    """
    Creates a cleaner queue plot with rolling averages and variance.
    """
    create_plot(department, big_data, y_label='Queue length', title_suffix='Queue length', smoothing_window=smoothing_window)

def create_bed_plot(department, big_data, smoothing_window=50):
    """
    Creates a cleaner bed plot with rolling averages and variance.
    """
    create_plot(department, big_data, y_label='Busy beds', title_suffix='Busy beds', smoothing_window=smoothing_window)
