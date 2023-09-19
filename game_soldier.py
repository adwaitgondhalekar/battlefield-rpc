import multiprocessing
import time
import random

missile_queue = [] # shared missile queue containing current missile
soldier_speed_list = []
battlefield = []
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

def start_exec():
    global N, M, t, T
    global soldier_speed_list, battlefield
    
    N, M, t, T = sys.argv[0], sys.argv[1], sys.argv[2], sys.argv[3]
    soldier_speed_list = [sys.arg(i + 4) for i in range(M)]
    battlefield = [[0 for i in range(N)] for j in range(N)]
    
    temp_set = set()
    while len(temp_set)
    
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
    
