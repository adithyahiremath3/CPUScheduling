from flask import Flask, render_template, request
import matplotlib.pyplot as plt
import io
import base64
import os

app = Flask(__name__)

# Utility functions for scheduling algorithms
def calculate_average_times(processes, n):
    total_turnaround_time = sum(p['turnaround_time'] for p in processes)
    total_weighted_turnaround_time = sum(p['turnaround_time'] / p['burst_time'] for p in processes)
    avg_turnaround_time = total_turnaround_time / n
    avg_weighted_turnaround_time = total_weighted_turnaround_time / n
    return avg_turnaround_time, avg_weighted_turnaround_time

def fcfs(processes):
    processes.sort(key=lambda x: x['arrival_time'])
    time_elapsed = 0
    for p in processes:
        p['start_time'] = max(time_elapsed, p['arrival_time'])
        p['completion_time'] = p['start_time'] + p['burst_time']
        time_elapsed = p['completion_time']
        p['turnaround_time'] = p['completion_time'] - p['arrival_time']
    return calculate_average_times(processes, len(processes))

def sjf(processes):
    processes.sort(key=lambda x: (x['arrival_time'], x['burst_time']))
    time_elapsed = 0
    completed = []
    while processes:
        ready_queue = [p for p in processes if p['arrival_time'] <= time_elapsed]
        if ready_queue:
            current = min(ready_queue, key=lambda x: x['burst_time'])
            processes.remove(current)
            current['start_time'] = time_elapsed
            current['completion_time'] = current['start_time'] + current['burst_time']
            time_elapsed = current['completion_time']
            current['turnaround_time'] = current['completion_time'] - current['arrival_time']
            completed.append(current)
        else:
            time_elapsed += 1
    return calculate_average_times(completed, len(completed))

def lcn(processes):
    processes.sort(key=lambda x: x['arrival_time'])
    time_elapsed = 0
    completed = []
    while processes:
        ready_queue = [p for p in processes if p['arrival_time'] <= time_elapsed]
        if ready_queue:
            current = max(ready_queue, key=lambda x: x['completion_time'] if 'completion_time' in x else 0)
            processes.remove(current)
            current['start_time'] = time_elapsed
            current['completion_time'] = current['start_time'] + current['burst_time']
            time_elapsed = current['completion_time']
            current['turnaround_time'] = current['completion_time'] - current['arrival_time']
            completed.append(current)
        else:
            time_elapsed += 1
    return calculate_average_times(completed, len(completed))

def round_robin(processes, quantum):
    queue = processes.copy()
    time_elapsed = 0
    while queue:
        current = queue.pop(0)
        if 'remaining_time' not in current:
            current['remaining_time'] = current['burst_time']
        if current['remaining_time'] > quantum:
            time_elapsed += quantum
            current['remaining_time'] -= quantum
            queue.append(current)
        else:
            time_elapsed += current['remaining_time']
            current['completion_time'] = time_elapsed
            current['turnaround_time'] = current['completion_time'] - current['arrival_time']
    return calculate_average_times(processes, len(processes))

# Function to determine the best algorithm based on avg turnaround time and waiting time
def get_best_algorithm(results):
    best_algorithm = None
    min_avg_tat = float('inf')
    min_avg_wt = float('inf')
    
    for algorithm, data in results.items():
        if data['avg_tat'] < min_avg_tat and data['avg_wt'] < min_avg_wt:
            best_algorithm = algorithm
            min_avg_tat = data['avg_tat']
            min_avg_wt = data['avg_wt']
    
    return best_algorithm

# Function to generate the plot
def generate_plot(results):
    algorithms = list(results.keys())
    avg_tat = [results[algo]['avg_tat'] for algo in algorithms]
    avg_wt = [results[algo]['avg_wt'] for algo in algorithms]

    fig, ax = plt.subplots(figsize=(10, 6))
    bar_width = 0.35
    index = range(len(algorithms))

    ax.bar(index, avg_tat, bar_width, label='Avg Turnaround Time', color='b')
    ax.bar([i + bar_width for i in index], avg_wt, bar_width, label='Avg Waiting Time', color='g')

    ax.set_xlabel('Algorithms')
    ax.set_ylabel('Time (ms)')
    ax.set_title('Comparison of CPU Scheduling Algorithms')
    ax.set_xticks([i + bar_width / 2 for i in index])
    ax.set_xticklabels(algorithms)
    ax.legend()

    # Save the plot as a PNG image in memory
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode('utf-8')
    plt.close()
    return plot_url

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/schedule', methods=['POST'])
def schedule():
    processes = request.form.getlist('process')
    burst_times = list(map(int, request.form.getlist('burst_time')))
    arrival_times = list(map(int, request.form.getlist('arrival_time')))
    quantum = int(request.form['quantum'])

    # Prepare process list
    process_list = [
        {'process': processes[i], 'arrival_time': arrival_times[i], 'burst_time': burst_times[i]} for i in range(len(processes))
    ]

    # Perform scheduling
    fcfs_avg_tat, fcfs_avg_wt = fcfs(process_list.copy())
    sjf_avg_tat, sjf_avg_wt = sjf(process_list.copy())
    lcn_avg_tat, lcn_avg_wt = lcn(process_list.copy())
    rr_avg_tat, rr_avg_wt = round_robin(process_list.copy(), quantum)

    results = {
        'First Come First Serve': {'avg_tat': fcfs_avg_tat, 'avg_wt': fcfs_avg_wt},
        'Shortest Job First': {'avg_tat': sjf_avg_tat, 'avg_wt': sjf_avg_wt},
        'Longest Completion Next': {'avg_tat': lcn_avg_tat, 'avg_wt': lcn_avg_wt},
        'Round Robin': {'avg_tat': rr_avg_tat, 'avg_wt': rr_avg_wt}
    }

    best_algorithm = get_best_algorithm(results)
    plot_url = generate_plot(results)

    return render_template('results.html', results=results, best_algorithm=best_algorithm, plot_url=plot_url)

# Run server
if __name__ == '__main__':
    app.run(debug=True)
