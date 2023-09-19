import multiprocessing
import time
import random
import os

missile_incoming = None # shared missile queue containing current missile
soldier_speed_list = []
battlefield = [] # N*N grid representing the soldier positions on the battlefield
soldier_position_list = []
missile_impact_map = {"M1" : 1, "M2" : 2, "M3" : 3, "M4" : 4}
missile_impact_grid = []

N, M, t, T = None, None, None, None

class Missile:
    def __init__(self, pos, hit_time, missile_type):
        self.pos = pos
        self.hit_time = hit_time
        self.missile_type = missile_type

def take_shelter(soldier_num):
    x, y = soldier_position_list[soldier_num] # querying soldier position

    start_row = max(0, x - (soldier_speed_list[soldier_num] - 1))
    end_row = min(N - 1, x + (soldier_speed_list[soldier_num] - 1))
    start_col = max(0, y - (soldier_speed_list[soldier_num] - 1))
    end_col = min(N - 1, y + (soldier_speed_list[soldier_num] - 1))

    available_pos = []
    for i in range(start_row, end_row + 1):
        for j in range(start_col, end_col + 1):
            if missile_impact_grid[i][j] != 0 and battlefield[i][j] != 1 :
                available_pos.append((i, j)) # available options for soldier to take shelter

    if len(available_pos) == 0:
        # kill the soldier process
        battlefield[x][y] = 2
        return


    random.seed(round(time.time()))
    random_shelter = random.randint(0, len(available_pos) - 1)
    new_pos_x, new_pos_y = available_pos[random_shelter]
    soldier_position_list[soldier_num] = (new_pos_x, new_pos_y) # assigned new position to soldier

    battlefield[x][y] = 0
    battlefield[new_pos_x][new_pos_y] = 1 # marked soldier's new position in battlefield

def soldier(soldier_num, lock):
    global misslie_queue
    
    while True:

        x, y = soldier_position_list[soldier_num]
        if battlefield[x][y] == 2:
            break

        while missile_incoming == None:
            pass
        
        lock.acquire()
        take_shelter(soldier_num)
        lock.release()
    
def missile_approaching(pos, hit_time, missile_type):
    global missile_incoming
    missile = Missile(pos, hit_time, missile_type)
    
    # marking area of impact of missile
    x, y = pos
    start_row = max(0, x - (missile_impact_map[missile_type] - 1))
    end_row = min(N - 1, x + (missile_impact_map[missile_type] - 1))
    start_col = max(0, y - (missile_impact_map[missile_type] - 1))
    end_col = min(N - 1, y + (missile_impact_map[missile_type] - 1))



    for i in range(start_row, end_row + 1):
        for j in range(start_col, end_col + 1):
            missile_impact_grid[i][j] = 0 # area where missile will impact and soldiers die

    missile_incoming = missile

def status(soldier_ID): # does not return any value
    # check bitmap whether soldier was hit
    true_flag = 
    was_hit(soldier_ID, true_flag) # written at server side

def start_exec():
    global N, M, t, T
    global soldier_speed_list, soldier_position_list, battlefield, missile_impact_grid, soldier_list
    
    N, M, t, T = os.sys.argv[0], os.sys.argv[1], os.sys.argv[2], os.sys.argv[3]
    soldier_speed_list = [os.sys.arg(i + 4) for i in range(M)]
    battlefield = [[0 for i in range(N)] for j in range(N)]
    missile_impact_grid = [[1 for i in range(N)] for j in range(N)]
    
    # assign random positions to each soldier, ensuring NO 2 soldiers at the same position 
    while len(soldier_position_list) < M:
        random.seed(round(time.time()))
        temp_x = random.randint(0, N - 1)
        temp_y = random.randint(0, N - 1)
        if (temp_x, temp_y) not in soldier_position_list:
            soldier_position_list.add((temp_x, temp_y))
    del temp_x, temp_y
    
    for it in soldier_position_list:
        battlefield[it[0]][it[1]] = 1 # marking soldiers position in the battlefield 

    # elect commander
    random.seed(round(time.time()))
    commander = random.randint(0, M - 1)
    
    matrix_read_lock = multiprocessing.Lock()
    
    # list containing all processes and simultaneously status whether alive or not
    soldier_list = [multiprocessing.Process(target = soldier, args = (i, matrix_read_lock)) if i != commander else None for i in range(M)]
    
if __name__ == "__main__":
    
    proc1.start()
    proc2.start()
    
    
    proc1.join()
    proc2.join()

    print("Both Processes Completed!")
    
