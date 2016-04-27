from time import time

start_times=dict()
end_times=dict()

def start(tag):
    start_times[tag]=time()

def end(tag):
    end_times[tag]=time()

def end_and_start(tag_end,tag_start):
    t=time()
    start_times[tag_start]=t
    end_times[tag_end]=t

def print_results(tag):
    try:
        print("[",tag,"] Execution time:",end_times[tag]-start_times[tag])
    except KeyError:
        print("[",tag,"] tag error.")
def print_all(reset_all=True):
    for i in start_times:
        print_results(i)
    if reset_all:
        reset()

def reset():
    global start_times, end_times
    start_times=dict()
    end_times=dict()