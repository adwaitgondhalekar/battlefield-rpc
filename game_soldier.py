import multiprocessing
import time
import random
import os

missile_queue = [] # shared missile queue containing current missile
soldier_speed_list = []
battlefield = []
soldier_position_list = []
N, M, t, T = None, None, None, None

class Missile:
    def __init__(self, pos, hit_time, missile_type):
        self.pos = pos
        self.hit_time = hit_time
        self.missile_type = missile_type
        
def prnt_cu(n):
    
    shared_fn("Cube: {}".format(n * n * n), 3)

def shared_fn(arg, t):
    while True:
        print(arg)
        time.sleep(t)

def prnt_squ(n):
    global shared_list
    
    shared_fn("Square: {}".format(n * n), 2)

def take_shelter(soldier_num):
    

def soldier(soldier_num, lock):
    global misslie_queue
    
    while len(missile_queue) == 0:
        pass
    
    lock.acquire()
    take_shelter(soldier_num)
    lock.release()
    
def missile_approaching(pos, hit_time, missile_type):
    missile = Missile(pos, hit_time, missile_type)
    missile_queue.append(missile)

def status(soldier_ID): # does not return any value
    # check bitmap whether soldier was hit
    return was_hit(soldier_ID, true_flag)

def start_exec():
    global N, M, t, T
    global soldier_speed_list, soldier_position_list, battlefield
    
    N, M, t, T = os.sys.argv[0], os.sys.argv[1], os.sys.argv[2], os.sys.argv[3]
    soldier_speed_list = [os.sys.arg(i + 4) for i in range(M)]
    battlefield = [[0 for i in range(N)] for j in range(N)]
    
    # assign random positions to each soldier, ensuring NO 2 soldiers at the same position 
    while len(soldier_position_list) < M:
        random.seed(round(time.time()))
        temp_x = random.randint(0, N - 1)
        temp_y = random.randint(0, N - 1)
        if (temp_x, temp_y) not in soldier_position_list:
            soldier_position_list.add((temp_x, temp_y))
    del temp_x, temp_y
    
    # elect commander
    random.seed(round(time.time()))
    commander = random.randint(0, M - 1)
    
    matrix_read_lock = multiprocessing.Lock()
    
    # list containing all processes
    soldier_list = [multiprocessing.Process(target = soldier, args = (i, matrix_read_lock)) if i != commander else None for i in range(M)]
    
if __name__ == "__main__":
    
    proc1.start()
    proc2.start()
    
    
    proc1.join()
    proc2.join()

    print("Both Processes Completed!")
    
