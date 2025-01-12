import matplotlib.pyplot as plt
import pandas as pd

def calculate_statistics(big_data):
    """
    Calculate average, min, and max statistics for the entire dataset.
    
    Parameters:
        big_data (list of dicts): Each dict represents data with keys as time steps and values as used beds.
    
    Returns:
        time_steps (list): Sorted list of all time steps.
        average_used_beds (list): Average used beds at each time step.
        min_used_beds (list): Minimum used beds at each time step.
        max_used_beds (list): Maximum used beds at each time step.
    """
    # Create dictionaries to store sums and counts for each key (time step)
    sums = {}
    counts = {}
    min_values = {}
    max_values = {}

    # Iterate through each dictionary in big_data
    for data in big_data:
        for key, value in data.items():
            if key not in sums:
                sums[key] = value
                counts[key] = 1
                min_values[key] = value
                max_values[key] = value
            else:
                sums[key] += value
                counts[key] += 1
                min_values[key] = min(min_values[key], value)
                max_values[key] = max(max_values[key], value)

    # Calculate averages by dividing sums by counts
    averages = {key: sums[key] / counts[key] for key in sums}

    # Sort time steps for consistent plotting
    time_steps = sorted(averages.keys())
    average_used_beds = [averages[key] for key in time_steps]
    min_used_beds = [min_values[key] for key in time_steps]
    max_used_beds = [max_values[key] for key in time_steps]

    return time_steps, average_used_beds, min_used_beds, max_used_beds

def create_plot(department, big_data, y_label, title_suffix):
    """
    Creates a plot with average and range using error bars.
    
    Parameters:
        department (str): Name of the department.
        big_data (list of dicts): Data to be plotted.
        y_label (str): Label for the y-axis.
        title_suffix (str): Suffix for the plot title.
    """
    # Calculate statistics
    time_steps, average_used_beds, min_used_beds, max_used_beds = calculate_statistics(big_data)

    # Calculate error bars (range from average to min and max)
    error_bars = [[average_used_beds[i] - min_used_beds[i], max_used_beds[i] - average_used_beds[i]] 
                  for i in range(len(time_steps))]

    # Transpose error bars for plotting
    error_bars = list(zip(*error_bars))
    overall_average = sum(average_used_beds) / len(average_used_beds)

    # Create the plot
    plt.figure(figsize=(12, 6))
    plt.errorbar(time_steps, average_used_beds, yerr=error_bars, fmt='-', ecolor='lightblue', capsize=5, 
                 label='Average with Range', linewidth=2)
    # for ploting the average
    #plt.axhline(y=overall_average, color='red', linestyle='--', linewidth=2, label=f'Overall Average = {overall_average:.2f}', zorder=2)
    
    # Add labels, title, and legend
    plt.xlabel('Step', fontsize=12)
    plt.ylabel(y_label, fontsize=12)
    plt.title(f'{title_suffix} of {department} per Step', fontsize=14)
    plt.legend(fontsize=10)
    plt.grid(True, linestyle='--', alpha=0.7)

    plt.tight_layout()
    plt.show()

def create_queue_plot(department, big_data):
    """
    Creates a queue plot with error bars showing average and range.
    """
    create_plot(department, big_data, y_label='Queue length', title_suffix='Queue length')

def create_bed_plot(department, big_data):
    """
    Creates a bed plot with error bars showing average and range.
    """
    create_plot(department, big_data, y_label='Busy beds', title_suffix='Busy beds')
