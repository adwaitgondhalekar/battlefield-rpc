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
import status_pb2, status_pb2_grpc
import send_commander_index_pb2, send_commander_index_pb2_grpc
import game_over_pb2, game_over_pb2_grpc
import logging

from concurrent import futures
from colorama import Fore, Back, Style

others_ip_addr = '172.17.84.247'
own_ip_addr = '172.17.84.246'

N, M, t, T, commander_index, missile_x_pos, missile_y_pos, missile_type= None, None, None, None, None, None, None, None
soldier_speed_list = []
liveness_list = []
battlefield = []
soldier_position_list = {}
missile_type_list = ["M1", "M2", "M3", "M4"]


servers = []
static_soldier_count = None
dynamic_take_shelter_count = None
dead_count_one_missile = 0
missile_fired = False
missile_impact_dict = {"M1" : 1, "M2" : 2, "M3" : 3, "M4" : 4}
missile_impact_grid = []
params_sent = False
is_client_game_over = False

class Get_Params_Client(rpc2.Get_Params_ClientServicer):
    def get_params_client(self, request, context):

        global params_sent
        params_sent = True
        return get_params_client_pb2.params_response(N = N, M = M)

class Get_Valid_Position(rpc1.Get_Valid_PositionServicer):

    def get_valid_position(self, request_iterator, context):
        global dynamic_take_shelter_count, dead_count_one_missile
        final_x_pos, final_y_pos = -1, -1

        i = 1
        old_x, old_y = -1, -1
        soldier_num = None
        for positions in request_iterator:
            if i == 1:
                old_x, old_y, soldier_num = positions.x_pos, positions.y_pos, positions.id
            x_pos, y_pos = positions.x_pos, positions.y_pos
            i += 1
            if battlefield[x_pos][y_pos] in [1, 3] :
                continue
            else:
                final_x_pos, final_y_pos = x_pos, y_pos
                # print("Inside valid pos")
                battlefield[final_x_pos][final_y_pos] = 1
                battlefield[old_x][old_y] = 0
                break
        
        if final_x_pos == -1:
            battlefield[old_x][old_y] = 2
        response = get_valid_position_pb2.valid_position(valid_x_pos = final_x_pos, valid_y_pos = final_y_pos)
        soldier_position_list[soldier_num] = (final_x_pos, final_y_pos)
        return response  # commander returning a valid position where soldier can take shelter

# rpc_list = [(Get_Valid_Position(), 'localhost:50051',rpc1.add_Get_Valid_PositionServicer_to_server), (Get_Params_Client(), 'localhost:50052', rpc2.add_Get_Params_ClientServicer_to_server)]
rpc_list = [(Get_Valid_Position(), own_ip_addr + ':50051',rpc1.add_Get_Valid_PositionServicer_to_server), (Get_Params_Client(), own_ip_addr + ':50052', rpc2.add_Get_Params_ClientServicer_to_server)]


def create_servers():

    for i in range(len(rpc_list)):
        servers.append(grpc.server(futures.ThreadPoolExecutor(max_workers=2)))


    for i, j in enumerate(rpc_list):
        obj, port, rpc_name  = j[0], j[1], j[2]
        rpc_name(obj, servers[i])
        servers[i].add_insecure_port(port)
        servers[i].start()
        print("server {} started".format(i))
        
    print("All server side request servers started")

def take_shelter(x, y, old_commander_index):

    global missile_impact_grid, soldier_speed_list, battlefield, liveness_list

    if missile_impact_grid[x][y] == 0:  #current commander position not safe

        start_row = max(0, x - (soldier_speed_list[old_commander_index]))
        end_row = min(N - 1, x + (soldier_speed_list[old_commander_index]))
        start_col = max(0, y - (soldier_speed_list[old_commander_index]))
        end_col = min(N - 1, y + (soldier_speed_list[old_commander_index]))

        available_pos = []
        for i in range(start_row, end_row + 1):
            for j in range(start_col, end_col + 1):
                if missile_impact_grid[i][j] != 0 and battlefield[i][j] != 1 :
                    available_pos.append((i, j)) # available options for soldier to take shelter

        if len(available_pos) == 0:
            # commander cannot save himself and will be killed
            battlefield[x][y] = 2
            liveness_list[old_commander_index] = 0 # marked soldier as dead
            print("Commander is dead !")
            logging.debug("Commander is dead !")
            # return (-1, -1)
            return


        random.seed(round(time.time()))
        random_shelter = random.randint(0, len(available_pos) - 1)
        new_pos_x, new_pos_y = available_pos[random_shelter]
        soldier_position_list[old_commander_index] = (new_pos_x, new_pos_y) # assigned new position to soldier

        battlefield[x][y] = 0
        battlefield[new_pos_x][new_pos_y] = 3 # marked soldier's new position in battlefield
        # print("commander old position = {}\ncommander new position = {}".format((x,y), (new_pos_x, new_pos_y)))
        # return (new_pos_x, new_pos_y)
        return
    
    else:
        return



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
    
    c = 0
    # assign random positions to each soldier, ensuring NO 2 soldiers at the same position 
    while len(soldier_position_list) < M:
        random.seed(round(time.time()))
        temp_x = random.randint(0, N - 1)
        temp_y = random.randint(0, N - 1)
        if (temp_x, temp_y) not in soldier_position_list.values():
            soldier_position_list[c] = (temp_x, temp_y)
            c += 1
    del temp_x, temp_y
    
    # marking soldiers position in the battlefield
    for it in soldier_position_list.values():
        battlefield[it[0]][it[1]] = 1 

def call_game_over():
    with grpc.insecure_channel(others_ip_addr + ':40056') as channel:
        global is_client_game_over
        stub = game_over_pb2_grpc.Game_OverStub(channel)
        response = stub.game_over(game_over_pb2.game_over_req())

        is_client_game_over = response.client_game_over


def elect_commander():

    global commander_index

    print("GOT REQUEST TO ELECT COMMANDER")
    logging.debug("GOT REQUEST TO ELECT COMMANDER")

    alive_index = []
    for soldier_index in range(len(liveness_list)):
        if liveness_list[soldier_index] == 1:
            alive_index.append(soldier_index)
    
    if len(alive_index) == 0: # no soldier is alive
        call_game_over()
        print("All Soldiers are Dead !")
        logging.debug("All Soldiers are Dead !")
        return

    soldier_position_list[commander_index] = (-1, -1)
    random.seed(round(time.time()))
    commander_index = random.choice(alive_index)

    print("Soldier {} is elected as new commander".format(commander_index))
    logging.debug("Soldier {} elected as the commander".format(commander_index))
    x, y = soldier_position_list[commander_index][0], soldier_position_list[commander_index][1]
    battlefield[x][y] = 3   # marked commander in the battlefield
    
def send_new_commander():
    with grpc.insecure_channel(others_ip_addr + ':40055') as channel:
        stub = send_commander_index_pb2_grpc.Send_Commander_IndexStub(channel)
        response = stub.send_commander_index(send_commander_index_pb2.new_commander_index(commander_index = commander_index))

def create_soldier_process():
    with grpc.insecure_channel(others_ip_addr + ':40051') as channel:
        stub = create_soldier_pb2_grpc.Create_SoldierStub(channel)

        soldier_list = []
        for i in range(M):

            if i == commander_index:
                continue
            else:
                soldier_list.append(create_soldier_pb2.soldier_details(soldier_number = i, x_pos = soldier_position_list[i][0], y_pos = soldier_position_list[i][1], speed_capacity = soldier_speed_list[i]))
        response = stub.create_soldiers(soldier_list.__iter__())
        print(response.msg)
        logging.debug("All sodliers created")

def can_fire_missile():
    with grpc.insecure_channel(others_ip_addr + ':40053') as channel:
        stub = all_taken_shelter_pb2_grpc.All_Taken_ShelterStub(channel)
        response = stub.all_taken_shelter(all_taken_shelter_pb2.taken_shelter_query())
        return response

def status_all():
    for i in range(M):
        if i == commander_index:
            continue
        with grpc.insecure_channel(others_ip_addr + ':40054') as channel:
            stub = status_pb2_grpc.StatusStub(channel)
            response = stub.status(status_pb2.status_request(soldier_id = i))
        liveness_list[i] = 1 if response.alive else 0

def print_missile_area():

    for i in range(N):
        # print("————" * N)
        # print("{:—^{width}s}".format("", width = 8*N))
        for j in range(N):
            # print("|" ,end="",sep="")
            # print(i, j)
            print("", end="", sep="")
            if battlefield[i][j] == 0 and missile_impact_grid[i][j] == 0 and (i, j) == (missile_x_pos, missile_y_pos):
                print(Back.RED + Fore.WHITE + '{:^7}'.format("M"), end="",sep="")
                print(Style.RESET_ALL, end="", sep="")
            elif battlefield[i][j] == 0 and missile_impact_grid[i][j] == 0:
                print(Back.RED + '{:^7}'.format("-"), end="",sep="")
                print(Style.RESET_ALL, end="", sep="")
            elif battlefield[i][j] == 0:
                print('{:^7}'.format("-"), end="",sep="")

            elif battlefield[i][j] == 1 and missile_impact_grid[i][j] == 0 and (i, j) == (missile_x_pos, missile_y_pos):
                print(Back.RED + Fore.WHITE+ '{:^7}'.format("M"), end="",sep="")
                print(Style.RESET_ALL, end="", sep="")

            elif battlefield[i][j] == 1 and missile_impact_grid[i][j] == 0:
                temp2 = None
                for temp in range(M):
                    if soldier_position_list[temp] == (i, j):
                        temp2 = temp
                        break
                soldier = 'S'+str(temp2)
                print(Back.RED + Fore.GREEN + '{:^7}'.format(soldier), end="",sep="")
                print(Style.RESET_ALL, end="", sep="")
            elif battlefield[i][j] == 1:
                temp2 = None
                for temp in range(M):
                    if soldier_position_list[temp] == (i, j):
                        temp2 = temp
                        break
                soldier = 'S'+str(temp2)
                # print(Fore.GREEN + 'S{}'.format(temp2), end="", sep="")
                print(Fore.GREEN + '{:^7}'.format(soldier), end="", sep="")
                print(Style.RESET_ALL, end="", sep="")
            
            elif battlefield[i][j] == 3 and missile_impact_grid[i][j] == 0 and (i, j) == (missile_x_pos, missile_y_pos):
                print(Back.RED+ Fore.WHITE + '{:^7}'.format("M"), end="",sep="")
                print(Style.RESET_ALL, end="", sep="")
            elif battlefield[i][j] == 3 and missile_impact_grid[i][j] == 0:
                print(Back.RED+ Fore.CYAN+ '{:^7}'.format("C"), end="",sep="")
                print(Style.RESET_ALL, end="", sep="")
            elif battlefield[i][j] == 3:
                print(Fore.CYAN + '{:^7}'.format("C"), end="", sep="")
                print(Style.RESET_ALL, sep="", end="")

            elif battlefield[i][j] == 2 and missile_impact_grid[i][j] == 0 and (i, j) == (missile_x_pos, missile_y_pos):
                print(Fore.WHITE+ Back.RED + '{:^7}'.format("M"),end="", sep="")
                print(Style.RESET_ALL, end="", sep="")
            elif battlefield[i][j] == 2 and missile_impact_grid[i][j] == 0:
                print(Back.RED+ Fore.WHITE + '{:^7}'.format("X"),end="", sep="")
                print(Style.RESET_ALL, end="", sep="")
            elif battlefield[i][j] == 2:
                print(Fore.RED + '{:^7}'.format("X"),end="", sep="")
                print(Style.RESET_ALL, end="", sep="")
        # print("|")
        print("")
        print("")

def print_layout():
    
    for i in range(N):
        # print("————" * N)
        # print("{:—^{width}s}".format("", width = 8*N))
        for j in range(N):
            # print("|" ,end="",sep="")
            print("", end="", sep="")
            if battlefield[i][j] == 0:
                print('{:^7}'.format("-"), end="",sep="")
            elif battlefield[i][j] == 1:
                temp2 = None
                for temp in range(M):
                    if soldier_position_list[temp] == (i, j):
                        temp2 = temp
                        break
                soldier = 'S'+str(temp2)
                # print(Fore.GREEN + 'S{}'.format(temp2), end="", sep="")
                print(Fore.GREEN + '{:^7}'.format(soldier), end="", sep="")
                print(Style.RESET_ALL, end="", sep="")
            elif battlefield[i][j] == 3:
                print(Fore.CYAN + '{:^7}'.format("C"), end="", sep="")
                print(Style.RESET_ALL, sep="", end="")
            elif battlefield[i][j] == 2:
                print(Fore.RED + '{:^7}'.format("X"),end="", sep="")
                print(Style.RESET_ALL, end="", sep="")
        # print("|")
        print("")
        print("")
        # print()
    # print("————" * N)
    # print("{:—^{width}s}".format("", width = 8*N))

def display_game():
    casualty_count = 0
    print_layout()
    temp_list = []
    
    for dead_index in range(len(liveness_list)):
        if liveness_list[dead_index] == 0 and dead_index not in dead_list:
            temp_list.append(dead_index)
    
    temp_list_2 = []
    for i in temp_list:
        if i != commander_index:
            temp_list_2.append('S' + str(i))
        else:
            temp_list_2.append('C' + str(i))

    dead_list.extend(temp_list)
    for i in liveness_list:
        if i == 0:
            casualty_count += 1
    print("DEAD SOLDIERS :", temp_list_2)
    logging.debug("DEAD SOLDIERS :" + str(temp_list_2))
    print("TOTAL CASUALTY COUNT IS - {}".format(casualty_count))
    logging.debug("TOTAL CASUALTY COUNT IS - {}".format(casualty_count))
    temp_list.clear()
    print("")
    

def game_result():

    players_alive_count = 0
    player_percentage = None
    for live_status in liveness_list:
        if live_status == 1:
            players_alive_count += 1

    if players_alive_count == None:
        players_alive_count = 0
        
    player_percentage = players_alive_count/M * 100

    if player_percentage>50:
        print ("GAME WON AS {:.2f}% PLAYERS ALIVE !".format(player_percentage))
        logging.debug("GAME WON AS {:.2f}% PLAYERS ALIVE !".format(player_percentage))
    else:
        print ("GAME LOST AS {:.2f}% PLAYERS ALIVE !".format(player_percentage))
        logging.debug("GAME LOST AS {:.2f}% PLAYERS ALIVE !".format(player_percentage))

def log_live_soldiers():
    for i in range(len(liveness_list)):
        
        if soldier_position_list[i][0] != -1:
            logging.debug("Soldier {} is at {}".format(i, soldier_position_list[i]))
        else:
            logging.debug("Soldier {} is dead".format(i))

if __name__ == '__main__' :

    logging.basicConfig(filename='output.log', format='%(asctime)s %(message)s', level=logging.DEBUG)
    missile_one = False
    dead_list = []
    
    take_input()
    logging.debug("Input taken from user N={}, M={}".format(N, M))
    missile_impact_grid = [[1 for i in range(N)] for j in range(N)]
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
    
    game_timestamp = 0

    print("Initial State")
    display_game()
    while game_timestamp <= T:
    # while time.time() - start_timestamp <= T:

        if last_missile_timestamp != None and time.time() - last_missile_timestamp < t:
            # print(round(time.time() - last_missile_timestamp))
            continue
        
        can_fire_missile_response = can_fire_missile()
        if can_fire_missile_response.taken_shelter == False:
            continue
        # time.sleep(1)
        # create logical timer
        logging.debug("Time elapsed {} seconds".format(game_timestamp))
        print("Time elapsed {} seconds".format(game_timestamp))
        game_timestamp += t
        
        status_all()
        if can_fire_missile_response.live_soldier_count != 0 and missile_one == True:
            print("After Evasion !")
            log_live_soldiers()
            display_game()
        
        create_missile()
        missile_one = True

        if can_fire_missile_response.live_soldier_count != 0:
            print("Before Evasion")
            log_live_soldiers()
            print_missile_area()
        # commander re-election

        if liveness_list[commander_index] == 0:     #commander is dead
            elect_commander()
            if liveness_list[commander_index] == 0:
                break
            send_new_commander()
        
        take_shelter(soldier_position_list[commander_index][0], soldier_position_list[commander_index][1], commander_index) # first commander tries to take shelter
        
        # rpc call to missile_approaching
        if can_fire_missile_response.live_soldier_count != 0:
            with grpc.insecure_channel(others_ip_addr + ':40052') as channel:
                stub = missile_approaching_pb2_grpc.Missile_ApproachingStub(channel)
                stub.missile_approaching(missile_approaching_pb2.missile(x_pos = missile_x_pos, y_pos = missile_y_pos, hit_time = round(time.time() - start_timestamp), missile_type = missile_type))
                print("Missile Fired !")
                logging.debug("Missile Fired !")
                last_missile_timestamp = time.time()
        
    logging.debug("Time elapsed {} seconds".format(game_timestamp))
    print("Time elapsed {} seconds".format(game_timestamp))

    if can_fire_missile_response.live_soldier_count != 0:
        status_all()
    display_game()

log_live_soldiers()
call_game_over()

while not(is_client_game_over):
    pass
time.sleep(5)    # so that game over rpc request reaches client and server.py closes after that

game_result()
print("GAME OVER !")
logging.debug("GAME OVER !")
