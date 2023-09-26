import multiprocessing, grpc, random, time
from concurrent import futures
import create_soldier_pb2
import create_soldier_pb2_grpc as rpc1
import missile_approaching_pb2
import missile_approaching_pb2_grpc as rpc2
import get_valid_position_pb2
import get_valid_position_pb2_grpc
import get_params_client_pb2
import get_params_client_pb2_grpc
import all_taken_shelter_pb2
import all_taken_shelter_pb2_grpc as rpc3
import is_valid_position_pb2
import is_valid_position_pb2_grpc
import game_start_pb2
import game_start_pb2_grpc

take_shelter_lock = multiprocessing.Lock()
global_missile_count_lock = multiprocessing.Lock()
missile_queue = multiprocessing.Queue()
no_of_rpc = 3
servers = []
global_missile_count = multiprocessing.Queue()
global_missile_count.put(0)

take_shelter_queue = multiprocessing.Queue()

static_soldier_count = multiprocessing.Queue()
dynamic_soldier_count = multiprocessing.Queue()

'''
channel_list = {'get hyperparameters' : grpc.insecure_channel('[::]:50052'), 'single position query' : grpc.insecure_channel('[::]:50055'), 'multiple position query' : grpc.insecure_channel('[::]:50051')}
stub_list = {'get hyperparameters' : get_params_client_pb2_grpc.Get_Params_ClientStub(channel_list["get hyperparameters"]), 'single position query' : is_valid_position_pb2_grpc.Is_Valid_PositionStub(channel_list["single position query"]), 'multiple position query' : get_valid_position_pb2_grpc.Get_Valid_PositionStub(channel_list['multiple position query'])}
'''

port_list = {'game start' : '[::]:50054', 'get hyperparameters' : '[::]:50052', 'single position query' : '[::]:50053', 'multiple position query' : '[::]:50051'}
stub_list = {'game start' : game_start_pb2_grpc.Game_StartStub, 'get hyperparameters' : get_params_client_pb2_grpc.Get_Params_ClientStub, 'single position query' : is_valid_position_pb2_grpc.Is_Valid_PositionStub, 'multiple position query' : get_valid_position_pb2_grpc.Get_Valid_PositionStub}

# rpc to server to get a single valid position out of available positions for a soldier
def valid_position_getter(available_pos):
    with grpc.insecure_channel(port_list["multiple position query"]) as channel:
        stub = stub_list["multiple position query"](channel)

        available_pos_list = []
        for position in available_pos:
            available_pos_list.append(get_valid_position_pb2.available_positions(x_pos = position[0], y_pos = position[1]))
        print("rpc call to commander to get_valid_position() abc")
        response = stub.get_valid_position(available_pos_list.__iter__())
    return (response.valid_x_pos, response.valid_y_pos)

def start_game():
    with grpc.insecure_channel(port_list["game start"]) as channel:
        stub = stub_list["game start"](channel)
        print("GAME START")
        response = stub.start_game(game_start_pb2.game_start_request())
        print("GAME START 2")

def check_valid_position(x, y) -> bool :
    with grpc.insecure_channel(port_list["single position query"]) as channel:
        stub = stub_list["single position query"](channel)
        print("rpc call to commander to check_valid_position() abc")
        response = stub.is_valid_position(is_valid_position_pb2.soldier_escape_position(x_pos = x, y_pos = y))
    return response.is_safe

def get_hyperparameters():
    global N, M
    with grpc.insecure_channel(port_list["get hyperparameters"]) as channel:
        stub = stub_list["get hyperparameters"](channel)
        response = stub.get_params_client(get_params_client_pb2.params_request())
        N = response.N
        M = response.M
        print("got hyperparameters inside function", N, M)

def take_shelter(soldier_num, x_pos, y_pos, speed, missile_x_pos, missile_y_pos, missile_capacity):

    print ("Soldier {} old position {} ".format(soldier_num, (x_pos, y_pos)))

    missile_impact_grid = [[1 for i in range(N)] for j in range(N)]
    # marking area of impact of missile
    start_row = max(0, missile_x_pos - (missile_capacity - 1))
    end_row = min(N - 1, missile_x_pos + (missile_capacity - 1))
    start_col = max(0, missile_y_pos - (missile_capacity - 1))
    end_col = min(N - 1, missile_y_pos + (missile_capacity - 1))

    for i in range(start_row, end_row + 1):
        for j in range(start_col, end_col + 1):
            missile_impact_grid[i][j] = 0 # area where missile will impact and soldiers die
    
    if missile_impact_grid[x_pos][y_pos] == 0:  #current soldier position not safe

        start_row = max(0, x_pos - (speed - 1))
        end_row = min(N - 1, x_pos + (speed - 1))
        start_col = max(0, y_pos - (speed - 1))
        end_col = min(N - 1, y_pos + (speed - 1))

        available_pos = []
        for i in range(start_row, end_row + 1):
            for j in range(start_col, end_col + 1):
                if missile_impact_grid[i][j] != 0:
                    available_pos.append((i, j)) # available options for soldier to take shelter

        if len(available_pos) == 0:
            # soldier cannot save himself and thus gets killed
            print("returning from take shelter")
            return (-1, -1)

        # new_pos_x, new_pos_y = valid_position_getter(available_pos)

        new_pos_x, new_pos_y = -1, -1
        for i in available_pos:
            get_hyperparameters()
            if check_valid_position(i[0], i[1]):
                new_pos_x, new_pos_y = i
                break
        
        print("returning from take shelter")
        return (new_pos_x, new_pos_y)
    
    else:
        print("returning from take shelter")
        return (x_pos,y_pos) # soldier is safe


def soldier_code(soldier_num, x_pos, y_pos, speed, take_shelter_lock, global_missile_count, global_missile_count_lock, static_soldier_count, dynamic_soldier_count, take_shelter_queue):
    
    local_missile_count = 0
    print("soldier executing " + str(soldier_num) + "at ",(x_pos,y_pos))

    while True:
        
        
        global_missile_count_lock.acquire()
        local_copy_global_missile_count = global_missile_count.get()
        global_missile_count.put(local_copy_global_missile_count)
        global_missile_count_lock.release()

        if missile_queue.empty() != True and local_copy_global_missile_count - 1 == local_missile_count :

            take_shelter_lock.acquire() # so that only 1 soldier executes take_shelter() at a time

            take_shelter_queue.put(soldier_num)
            local_missile_count += 1
            missile_x_pos, missile_y_pos, hit_time, missile_type = missile_queue.get()
            missile_capacity = {"M1" : 1, "M2" : 2, "M3" : 3, "M4" : 4}[missile_type]

            new_position = take_shelter(soldier_num, x_pos, y_pos, speed, missile_x_pos, missile_y_pos, missile_capacity)
            x_pos, y_pos = new_position

            if x_pos == -1:
                static_soldier_count.put(static_soldier_count.get() - 1)

            dynamic_soldier_count.put(dynamic_soldier_count.get() - 1)

            local_dynamic_temp = dynamic_soldier_count.get()

            if local_dynamic_temp != 0:
                missile_queue.put((missile_x_pos, missile_y_pos, hit_time, missile_type))
                dynamic_soldier_count.put(local_dynamic_temp)
            else:
                local_static_temp = static_soldier_count.get()
                dynamic_soldier_count.put(local_static_temp)
                static_soldier_count.put(local_static_temp)

            print ("Taking shelter - Soldier {} new position {} ".format(soldier_num, (x_pos, y_pos)))
            take_shelter_queue.get()

            take_shelter_lock.release()

            if x_pos == -1 :
                print("soldier killed, terminating target function " + str(soldier_num))
                break
        
    
def create_servers():

    for i in range(no_of_rpc):
        servers.append(grpc.server(futures.ThreadPoolExecutor(max_workers=10)))


    for i, j in enumerate(rpc_list):
        obj, port, rpc_name  = j[0], j[1], j[2]
        rpc_name(obj, servers[i])
        servers[i].add_insecure_port(port)
        servers[i].start()
        
    print("All client side request servers started")


class All_Taken_Shelter(rpc3.All_Taken_ShelterServicer):
    def all_taken_shelter(self, request, context):
        
        response = all_taken_shelter_pb2.taken_shelter_response(taken_shelter = True if take_shelter_queue.empty() else False)
        
        return response

missile_number = 1
class Missile_Approaching(rpc2.Missile_ApproachingServicer):
    def missile_approaching(self, request, context):
        global missile_number
        print ("MISSILE {} INCOMING at {}!".format(missile_number,(request.x_pos,request.y_pos)))
        missile_number += 1
        global_missile_count.put(global_missile_count.get() + 1) #incrementing global missile count
        missile_queue.put((request.x_pos, request.y_pos, request.hit_time, request.missile_type))

        response = missile_approaching_pb2.missile_status()
        return response

class Create_Soldier(rpc1.Create_SoldierServicer):

    def create_soldiers(self, request_iterator, context):

        for soldier in request_iterator:
            multiprocessing.Process(target=soldier_code, args=(soldier.soldier_number, soldier.x_pos, soldier.y_pos, soldier.speed_capacity, take_shelter_lock,global_missile_count, global_missile_count_lock, static_soldier_count, dynamic_soldier_count, take_shelter_queue)).start()

        response = create_soldier_pb2.soldier_output(msg="Soldiers Created")
        
        return response

rpc_list = [(Create_Soldier(), '[::]:40051', rpc1.add_Create_SoldierServicer_to_server), (Missile_Approaching(), '[::]:40052', rpc2.add_Missile_ApproachingServicer_to_server),(All_Taken_Shelter(),'[::]:40053',rpc3.add_All_Taken_ShelterServicer_to_server)]

if __name__ == '__main__':

    create_servers()
    get_hyperparameters()
    print("got hyperparameters", N, M)
    get_hyperparameters()
    print("got hyperparameters", N, M)

    static_soldier_count.put(M - 1)
    dynamic_soldier_count.put(M - 1)

    #start_game()

    while True:
        pass
