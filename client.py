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
import status_pb2
import status_pb2_grpc as rpc4
import send_commander_index_pb2
import send_commander_index_pb2_grpc as rpc5
import game_over_pb2
import game_over_pb2_grpc as rpc6
from colorama import Fore, Back, Style



take_shelter_lock = multiprocessing.Lock()


manager = multiprocessing.Manager()
missile_queue = manager.Queue()
servers = []
global_missile_count = multiprocessing.Value('i',0)

static_soldier_count = multiprocessing.Value('i',0)
commander_index = multiprocessing.Value('i',-1)
dynamic_soldier_count = multiprocessing.Value('i',0)

all_taken_shelter_queue = manager.Queue()
take_shelter_request_queue = manager.Queue()
take_shelter_response_queue = manager.Queue()
N, M = None, None

is_game_over_2 = multiprocessing.Value('i', 0)
is_game_over = False

def get_params():
    global N, M
    with grpc.insecure_channel('[::]:50052') as channel:
        stub = get_params_client_pb2_grpc.Get_Params_ClientStub(channel)
        response = stub.get_params_client(get_params_client_pb2.params_request())

        N = response.N
        M = response.M


def valid_position_getter(available_pos):
    with grpc.insecure_channel('[::]:50051') as channel:
        stub = get_valid_position_pb2_grpc.Get_Valid_PositionStub(channel)

        available_pos_list = []
        for position in available_pos:
            available_pos_list.append(get_valid_position_pb2.available_positions(x_pos = position[0], y_pos = position[1], id = position[2]))
        response = stub.get_valid_position(available_pos_list.__iter__())
        return (response.valid_x_pos, response.valid_y_pos)

def take_shelter(soldier_num, x_pos, y_pos, speed, missile_x_pos, missile_y_pos, missile_capacity):
            
        print ("Soldier {} initial position is {} ".format(soldier_num, (x_pos, y_pos)))
        print()

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

            start_row = max(0, x_pos - (speed))
            end_row = min(N - 1, x_pos + (speed))
            start_col = max(0, y_pos - (speed))
            end_col = min(N - 1, y_pos + (speed))

            available_pos = [(x_pos, y_pos, soldier_num)]
            for i in range(start_row, end_row + 1):
                for j in range(start_col, end_col + 1):
                    if missile_impact_grid[i][j] != 0:
                        available_pos.append((i, j, soldier_num)) # available options for soldier to take shelter

            # if len(available_pos) == 1:
            #     # soldier cannot save himself and thus gets killed
            #     return (-1, -1)

            # print("Before calling valid position getter")
            new_pos_x, new_pos_y = valid_position_getter(available_pos)
            # print("AFter valid position getter")
            # take_shelter_request_queue.put((soldier_num, available_pos))

            return (new_pos_x, new_pos_y)
        
        else:
            return (x_pos,y_pos) # soldier is safe


def soldier_code(soldier_num, x_pos, y_pos, speed, take_shelter_lock, global_missile_count, static_soldier_count, dynamic_soldier_count, all_taken_shelter_queue, missile_queue, take_shelter_request_queue, take_shelter_response_queue, commander_index, is_game_over_2):
    
    local_missile_count = 0
    print("Soldier {} created and currently situated at {}".format(soldier_num, (x_pos, y_pos)))
    print()
    
    break_out_while = False
    while True:

        with is_game_over_2.get_lock():
            if is_game_over_2.value == 1:
                with static_soldier_count.get_lock():
                    static_soldier_count.value -= 1
                    with dynamic_soldier_count.get_lock():
                        dynamic_soldier_count.value = static_soldier_count.value
                break_out_while = True

        if break_out_while:
            break

        with commander_index.get_lock():
            if commander_index.value == soldier_num:
                print("Soldier {} is elected as the Commander !".format(soldier_num))
                print()
                with static_soldier_count.get_lock():
                    static_soldier_count.value -= 1
                    with dynamic_soldier_count.get_lock():
                        # dynamic_soldier_count.value -= 1
                        dynamic_soldier_count.value = static_soldier_count.value
                break_out_while = True
        
        if break_out_while:
            break

        with global_missile_count.get_lock():
            local_copy_global_missile_count = global_missile_count.value
        
        # if chota_timer == None or time.time() - chota_timer >= 1:
        #     print(local_copy_global_missile_count, local_missile_count)
        #     chota_timer = time.time()
        
        with is_game_over_2.get_lock():
            local_copy_game_over = is_game_over_2.value

        if missile_queue.empty() != True and local_copy_global_missile_count - 1 == local_missile_count and local_copy_game_over != 1:
            with commander_index.get_lock():
                if commander_index.value == soldier_num:
                    continue
            
            continue_while = False
            with is_game_over_2.get_lock():
                if is_game_over_2.value == 1:
                    continue_while = True

            if continue_while:
                continue

            # print("acquiring lock on missile count")
            all_taken_shelter_queue.put(soldier_num)

            take_shelter_lock.acquire()
            missile_x_pos, missile_y_pos, hit_time, missile_type = missile_queue.get()
            missile_capacity = {"M1" : 1, "M2" : 2, "M3" : 3, "M4" : 4}[missile_type]
            take_shelter_request_queue.put([soldier_num, x_pos, y_pos, speed, missile_x_pos, missile_y_pos, missile_capacity])
            
            # take_shelter_lock.acquire() # so that only 1 soldier executes take_shelter() at a time

            # print("Soldier {} is taking shelter...".format(soldier_num))

            local_missile_count += 1

            # new_position = take_shelter(soldier_num, x_pos, y_pos, speed, missile_x_pos, missile_y_pos, missile_capacity)
            
            while True:
                
                if take_shelter_response_queue.empty() != True:
                    local_response = take_shelter_response_queue.get()
                    
                    x_pos, y_pos = local_response[1]
                    break

                    # if local_response[0] != soldier_num:
                    #     take_shelter_response_queue.put(local_response)
                        
                    # else:
                    #     x_pos, y_pos = local_response[1]
                    #     break
            

            if x_pos == -1:
                with static_soldier_count.get_lock():
                    static_soldier_count.value -= 1

            with dynamic_soldier_count.get_lock():
                dynamic_soldier_count.value -= 1
                local_dynamic_temp = dynamic_soldier_count.value

            if local_dynamic_temp != 0:
                missile_queue.put((missile_x_pos, missile_y_pos, hit_time, missile_type))
            else:
                # local_static_temp = static_soldier_count.get()
                with static_soldier_count.get_lock():
                    with dynamic_soldier_count.get_lock():
                        dynamic_soldier_count.value = static_soldier_count.value
                # static_soldier_count.put(local_static_temp)

            # all_taken_shelter_queue.get()  # soldier has completed its take_shelter
            take_shelter_lock.release()
            if x_pos != -1:
                print ("Soldier {} has taken shelter at {} ".format(soldier_num, (x_pos, y_pos)))
                print()
            
                
            # take_shelter_lock.release()

            all_taken_shelter_queue.get()  # soldier has completed its take_shelter
            if x_pos == -1 :
                print(Fore.RED + "Soldier {} cannot evade Missile and will be killed".format(soldier_num))
                print(Style.RESET_ALL, end="", sep="")
                print()
                break

def create_servers():

    for i in range(len(rpc_list)):
        servers.append(grpc.server(futures.ThreadPoolExecutor(max_workers=5)))


    for i, j in enumerate(rpc_list):
        obj, port, rpc_name  = j[0], j[1], j[2]
        rpc_name(obj, servers[i])
        servers[i].add_insecure_port(port)
        servers[i].start()
        
    print("All client side request servers started")


class Send_Commander_Index(rpc5.Send_Commander_IndexServicer):
    def send_commander_index(self, request, context):
        
        with commander_index.get_lock():
            commander_index.value = request.commander_index

        return send_commander_index_pb2.commander_details()

class All_Taken_Shelter(rpc3.All_Taken_ShelterServicer):
    def all_taken_shelter(self, request, context):
        with static_soldier_count.get_lock():
            # print(missile_queue.empty(), all_taken_shelter_queue.empty(), take_shelter_request_queue.empty())
            response = all_taken_shelter_pb2.taken_shelter_response(taken_shelter = True if (missile_queue.empty() and  all_taken_shelter_queue.empty() and take_shelter_request_queue.empty()) else False, live_soldier_count = static_soldier_count.value)
        return response

class Missile_Approaching(rpc2.Missile_ApproachingServicer):
    def missile_approaching(self, request, context):
        print (Back.RED + Fore.WHITE+"Missile Incoming at {} !".format((request.x_pos, request.y_pos)), end="")
        print(Style.RESET_ALL, end="", sep="")
        print()
        
        with global_missile_count.get_lock():
            global_missile_count.value += 1
        with static_soldier_count.get_lock():
            if static_soldier_count.value == 0:
                return missile_approaching_pb2.missile_status()
            
        missile_queue.put((request.x_pos, request.y_pos, request.hit_time, request.missile_type))

        response = missile_approaching_pb2.missile_status()
        return response

soldier_list = []

class Create_Soldier(rpc1.Create_SoldierServicer):

    def create_soldiers(self, request_iterator, context):
        for soldier in request_iterator:
            temp = multiprocessing.Process(target=soldier_code, args=(soldier.soldier_number, soldier.x_pos, soldier.y_pos, soldier.speed_capacity, take_shelter_lock,global_missile_count, static_soldier_count, dynamic_soldier_count, all_taken_shelter_queue, missile_queue, take_shelter_request_queue, take_shelter_response_queue, commander_index, is_game_over_2))
            soldier_list.append(temp)
            temp.start()

        response = create_soldier_pb2.soldier_output(msg="Soldiers Created on Client Side")
        
        return response

class Status(rpc4.StatusServicer):
    def status(self, request, context):
        return status_pb2.status_response(alive = alive_map[request.soldier_id])

class Game_Over(rpc6.Game_OverServicer):
    def game_over(self, request, context):
        global is_game_over
        is_game_over = True  # game ended
        with is_game_over_2.get_lock():
            is_game_over_2.value = 1
        return game_over_pb2.game_over_response(client_game_over = True)

rpc_list = [(Create_Soldier(), '[::]:40051', rpc1.add_Create_SoldierServicer_to_server), (Missile_Approaching(), '[::]:40052', rpc2.add_Missile_ApproachingServicer_to_server),(All_Taken_Shelter(),'[::]:40053',rpc3.add_All_Taken_ShelterServicer_to_server), (Status(), '[::]:40054', rpc4.add_StatusServicer_to_server), (Send_Commander_Index(), '[::]:40055', rpc5.add_Send_Commander_IndexServicer_to_server), (Game_Over(), '[::]:40056', rpc6.add_Game_OverServicer_to_server)]

if __name__ == '__main__':
    create_servers()

    get_params()
    alive_map = {}
    for i in range(M):
        alive_map[i] = True

    with static_soldier_count.get_lock():
        static_soldier_count.value = M - 1

    with dynamic_soldier_count.get_lock():
        dynamic_soldier_count.value = M - 1

    # print("Before checking take shelter request queue")

    while not(is_game_over):
        
        if take_shelter_request_queue.empty() != True:
        
            local_request = take_shelter_request_queue.get()
            
            # print (local_request)
            x, y = take_shelter(*local_request)
            if x == -1:
                alive_map[local_request[0]] = False
            shelter_response = (local_request[0], (x, y),)
            # print(shelter_response)
            take_shelter_response_queue.put(shelter_response)
    
    # time.sleep(3)
    for i in soldier_list:
        # i.join()
        i.terminate()

    time.sleep(4)   # so that game_over rpc response reaches commander and client.py does not end before that
    print("GAME OVER !")
