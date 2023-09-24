import os, random, time, grpc
import create_soldier_pb2
import create_soldier_pb2_grpc
import get_valid_position_pb2
import get_valid_position_pb2_grpc as rpc1
import missile_approaching_pb2
import missile_approaching_pb2_grpc
import get_params_client_pb2
import get_params_client_pb2_grpc as rpc2
import all_taken_shelter_pb2
import all_taken_shelter_pb2_grpc

from concurrent import futures




N, M, t, T, commander_index, missile_x_pos, missile_y_pos, missile_type= None, None, None, None, None, None, None, None
soldier_speed_list = []
liveness_list = []
battlefield = []
soldier_position_list = []
missile_type_list = ["M1", "M2", "M3", "M4"]

no_of_rpc = 2
servers = []
static_soldier_count = None
dynamic_take_shelter_count = None
dead_count_one_missile = 0
commander_x_pos, commander_y_pos = None, None
missile_fired = False
missile_impact_dict = {"M1" : 1, "M2" : 2, "M3" : 3, "M4" : 4}
missile_impact_grid = []
params_sent = False

class Get_Params_Client(rpc2.Get_Params_ClientServicer):
    def get_params_client(self, request, context):

        global params_sent
        params_sent = True
        return get_params_client_pb2.params_response(N = N, M = M)

class Get_Valid_Position(rpc1.Get_Valid_PositionServicer):

    def get_valid_position(self, request_iterator, context):
        global dynamic_take_shelter_count, dead_count_one_missile
        final_x_pos, final_y_pos = -1, -1
        for positions in request_iterator:
            x_pos, y_pos = positions.x_pos, positions.y_pos

            if battlefield[x_pos][y_pos] in [1, 3] :
                continue
            else:
                final_x_pos, final_y_pos = x_pos, y_pos
                print("INside valid pos")
                break
        
        
        response = get_valid_position_pb2.valid_position(valid_x_pos = final_x_pos, valid_y_pos = final_y_pos)
        return response  # commander returning a valid position where soldier can take shelter
    
    



rpc_list = [(Get_Valid_Position(), '[::]:50051',rpc1.add_Get_Valid_PositionServicer_to_server), (Get_Params_Client(), '[::]:50052', rpc2.add_Get_Params_ClientServicer_to_server)]


def create_servers():

    for i in range(no_of_rpc):
        servers.append(grpc.server(futures.ThreadPoolExecutor(max_workers=1)))


    for i, j in enumerate(rpc_list):
        obj, port, rpc_name  = j[0], j[1], j[2]
        rpc_name(obj, servers[i])
        servers[i].add_insecure_port(port)
        servers[i].start()
        
    print("All server side request servers started")

def take_shelter(x, y, soldier_index):

    global missile_impact_grid, soldier_speed_list, battlefield, liveness_list

    if missile_impact_grid[x][y] == 0:  #current soldier position not safe

        start_row = max(0, x - (soldier_speed_list[soldier_index] - 1))
        end_row = min(N - 1, x + (soldier_speed_list[soldier_index] - 1))
        start_col = max(0, y - (soldier_speed_list[soldier_index] - 1))
        end_col = min(N - 1, y + (soldier_speed_list[soldier_index] - 1))

        available_pos = []
        for i in range(start_row, end_row + 1):
            for j in range(start_col, end_col + 1):
                if missile_impact_grid[i][j] != 0 and battlefield[i][j] != 1 :
                    available_pos.append((i, j)) # available options for soldier to take shelter

        if len(available_pos) == 0:
            # soldier cannot save himself and thus gets killed
            battlefield[x][y] = 2
            liveness_list[soldier_index] = 0 # marked soldier as dead
            return (-1, -1)


        random.seed(round(time.time()))
        random_shelter = random.randint(0, len(available_pos) - 1)
        new_pos_x, new_pos_y = available_pos[random_shelter]
        soldier_position_list[soldier_index] = (new_pos_x, new_pos_y) # assigned new position to soldier

        battlefield[x][y] = 0
        battlefield[new_pos_x][new_pos_y] = 1 # marked soldier's new position in battlefield
        return (new_pos_x, new_pos_y)
    
    else:
        return (x,y)



def create_missile():

    global missile_type, missile_x_pos, missile_y_pos, missile_type_list, missile_impact_grid

    random.seed(round(time.time()))
    missile_x_pos = random.randint(0, N-1)
    missile_y_pos = random.randint(0, N-1)
    missile_type = random.choice(missile_type_list)

    # marking area of impact of missile
    start_row = max(0, missile_x_pos - (missile_impact_dict[missile_type] - 1))
    end_row = min(N - 1, missile_x_pos + (missile_impact_dict[missile_type] - 1))
    start_col = max(0, missile_y_pos - (missile_impact_dict[missile_type] - 1))
    end_col = min(N - 1, missile_y_pos + (missile_impact_dict[missile_type] - 1))

    missile_impact_grid = [[1 for i in range(N)] for j in range(N)]
    for i in range(start_row, end_row + 1):
        for j in range(start_col, end_col + 1):
            missile_impact_grid[i][j] = 0 # area where missile will impact and soldiers die
    

def take_input():

    global N, M, t, T, soldier_speed_list

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


def assign_initial_state():

    global liveness_list, battlefield, soldier_position_list

    battlefield = [[0 for i in range(N)] for j in range(N)]
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
    

def elect_commander():

    global commander_index, commander_x_pos, commander_y_pos

    print("GOT REQUEST TO ELECT COMMANDER")

    alive_index = []
    for i in range(len(liveness_list)):
        if liveness_list[i] == 1:
            alive_index.append(i)
    
    random.seed(round(time.time()))
    commander_index = random.choice(alive_index)
    x, y = soldier_position_list[commander_index][0], soldier_position_list[commander_index][1]
    battlefield[x][y] = 3   # marked commander in the battlefield

    commander_x_pos = soldier_position_list[commander_index][0]
    commander_y_pos = soldier_position_list[commander_index][1]

def create_soldier_process():
    with grpc.insecure_channel('[::]:40051') as channel:
        stub = create_soldier_pb2_grpc.Create_SoldierStub(channel)

        soldier_list = []
        for i in range(M):

            if i == commander_index:
                continue
            else:
                soldier_list.append(create_soldier_pb2.soldier_details(soldier_number = i, x_pos = soldier_position_list[i][0], y_pos = soldier_position_list[i][1], speed_capacity = soldier_speed_list[i]))
        response = stub.create_soldiers(soldier_list.__iter__())
        print(response.msg)

def can_fire_missile():
    with grpc.insecure_channel('[::]:40053') as channel:
        stub = all_taken_shelter_pb2_grpc.All_Taken_ShelterStub(channel)

        response = stub.all_taken_shelter(all_taken_shelter_pb2.taken_shelter_query())

        return response.taken_shelter

if __name__ == '__main__' :

    take_input()
    static_soldier_count = M - 1
    dynamic_take_shelter_count = 0
    assign_initial_state()      # initializing the grid with soldier position, commander not elected yet
    elect_commander()
    create_servers()
    while params_sent == False:
        pass
    time.sleep(2)
    create_soldier_process()
    
    start_timestamp = time.time()
    last_missile_timestamp = None
    while time.time() - start_timestamp <= T:

        if last_missile_timestamp != None and time.time() - last_missile_timestamp < t:
            # print(round(time.time() - last_missile_timestamp))
            continue
        
        if can_fire_missile() == False:
            continue
        # time.sleep(1)
        create_missile()
        
        new_x, new_y = take_shelter(commander_x_pos, commander_y_pos, commander_index) # first commander tries to take shelter
        
        # rpc call to missile_approaching
        with grpc.insecure_channel('[::]:40052') as channel:
            stub = missile_approaching_pb2_grpc.Missile_ApproachingStub(channel)
            stub.missile_approaching(missile_approaching_pb2.missile(x_pos = missile_x_pos, y_pos = missile_y_pos, hit_time = round(time.time() - start_timestamp), missile_type = missile_type))
            last_missile_timestamp = time.time()
        if new_x == -1:
            elect_commander()




