import multiprocessing
import time
import random
import os
import grpc
import elect_commander_pb2 
import elect_commander_pb2_grpc as rpc1
import get_position_pb2
import get_position_pb2_grpc as rpc2
import get_hyperparameters_pb2
import get_hyperparameters_pb2_grpc as rpc3
from concurrent import futures

class Missile:
    def __init__(self, pos, hit_time, missile_type):
        self.pos = pos
        self.hit_time = hit_time
        self.missile_type = missile_type

class Soldier:
    def __init__(self, soldier_id : int, x_pos : int, y_pos : int) -> None:
        self.soldier_id = soldier_id
        self.x_pos = x_pos
        self.y_pos = y_pos

class Get_HyperParams(rpc3.Get_HyperParamsServicer):
    def get_hyperparams(self, request, context):
        return get_hyperparameters_pb2.hyperparams(N = N, M = M, t = t, T = T)

class Get_Position(rpc2.Get_PositionServicer):
    def get_position(self, request, context):
        for i in range(M):
            yield get_position_pb2.Soldier(soldier_num = i, x_pos = soldier_position_list[i][0], y_pos = soldier_position_list[i][1])

class Elector(rpc1.ElectorServicer):
    def elect_commander(self, request, context): # rpc # returns commander position and speed
        global commander

        print("GOT REQUEST TO ELECT COMMANDER")
        alive_index = []
        for i in range(len(liveness_list)):
            if liveness_list[i] == 1:
                alive_index.append(i)
        
        random.seed(round(time.time()))
        commander = random.choice(alive_index)
        
        return elect_commander_pb2.elected_commander(soldier_number = commander, x_pos =  soldier_position_list[commander][0], y_pos = soldier_position_list[commander][1], speed_capacity = soldier_speed_list[commander])

missile_incoming = None # shared missile queue containing current missile
soldier_speed_list = []
battlefield = [] # N*N grid representing the soldier positions on the battlefield -> 0 = empty, 1 = soldier/commander, 2 = dead soldier/commander
soldier_position_list = []
soldier_object_list = []
missile_impact_map = {"M1" : 1, "M2" : 2, "M3" : 3, "M4" : 4}
missile_impact_grid = []
commander = None
liveness_list = [] # 1 = ailve, 0 = dead
N, M, t, T = None, None, None, None
servers = []
no_of_rpc = 3
rpc_list = [(Elector(), '[::]:50051', rpc1.add_ElectorServicer_to_server), (Get_Position(), '[::]:50052', rpc2.add_Get_PositionServicer_to_server), (Get_HyperParams(), '[::]:50053', rpc3.add_Get_HyperParamsServicer_to_server)]
game_start_time = None

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
        liveness_list[soldier_num] = 0 # mark soldier as dead
        return


    random.seed(round(time.time()))
    random_shelter = random.randint(0, len(available_pos) - 1)
    new_pos_x, new_pos_y = available_pos[random_shelter]
    soldier_position_list[soldier_num] = (new_pos_x, new_pos_y) # assigned new position to soldier

    battlefield[x][y] = 0
    battlefield[new_pos_x][new_pos_y] = 1 # marked soldier's new position in battlefield

def soldier(soldier_num, lock):
    global battlefield, soldier_position_list, missile_incoming, T, game_start_time
    print("soldier executing " + str(soldier_num))
    while True:
        x, y = soldier_position_list[soldier_num]
        if battlefield[x][y] == 2 or soldier_num == commander or time.time() - game_start_time >= T:
            print("soldier terminating " + str(soldier_num))
            break

        if missile_incoming != None:
            lock.acquire()
            take_shelter(soldier_num)
            lock.release()
    
def missile_approaching(pos, hit_time, missile_type): # rpc 
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

def status(soldier_ID): # rpc # does not return any value
    # check bitmap whether soldier was hit
    true_flag = liveness_list[soldier_ID] == 0
    #was_hit(soldier_ID, true_flag) # written at server side

def start_exec():
    global N, M, t, T
    global soldier_speed_list, soldier_position_list, battlefield, missile_impact_grid, soldier_list, commander, liveness_list, game_start_time, soldier_object_list
    
    # input hyperparameters
    N, M, t, T = int(os.sys.argv[1]), int(os.sys.argv[2]), int(os.sys.argv[3]), int(os.sys.argv[4])
    soldier_speed_list = [int(os.sys.argv[i + 5]) for i in range(M)]

    #verifying input
    try:
        assert N > 0 and M in range(0, N * N + 1) and t > 0 and T >= t
        for i in range(M):
            assert soldier_speed_list[i] in range(0, 4 + 1)
    except AssertionError:
        print("WRONG HYPERPARAMETERS !\nRUN PROGRAM AGAIN")
        #terminate program

    # starting the game
    game_start_time = time.time()

    battlefield = [[0 for i in range(N)] for j in range(N)]
    missile_impact_grid = [[1 for i in range(N)] for j in range(N)]
    liveness_list = [1 for i in range(M)]
    
    # assign random positions to each soldier, ensuring NO 2 soldiers at the same position 
    while len(soldier_position_list) < M:
        random.seed(round(time.time()))
        temp_x = random.randint(0, N - 1)
        temp_y = random.randint(0, N - 1)
        if (temp_x, temp_y) not in soldier_position_list:
            soldier_position_list.append((temp_x, temp_y))
    del temp_x, temp_y
    
    # marking soldiers position in the battlefield
    for it in soldier_position_list:
        battlefield[it[0]][it[1]] = 1 
    
    matrix_read_lock = multiprocessing.Lock()
    
    soldier_object_list = [Soldier(i, soldier_position_list[i][0], soldier_position_list[i][1]) for i in range(M)]
    for i in soldier_object_list:
        print("SOLDIER NUMBER = {}, X={}, Y={}".format(i.soldier_id, i.x_pos, i.y_pos))

    # list containing all processes and simultaneously status whether alive or not
    soldier_list = [multiprocessing.Process(target = soldier, args = (i, matrix_read_lock)) for i in range(M)]
    for i in soldier_list:
        i.start()

    for i in range(no_of_rpc):
        servers.append(grpc.server(futures.ThreadPoolExecutor(max_workers=2)))

    for i, j in enumerate(rpc_list):
        obj, port, rpc_name  = j[0], j[1], j[2]
        rpc_name(obj, servers[i])
        servers[i].add_insecure_port(port)
        servers[i].start()
        print("Hello I am here")

    while time.time() - game_start_time < T:
        pass

    print('game over')
    for i in servers:
        i.stop(None)
        # i.wait_for_termination()

    print("servers stopped")
    for i in soldier_list:
        i.join()
    
if __name__ == "__main__":
    
    try:
        start_exec()
    except KeyboardInterrupt:
        pass
    print("program end")
