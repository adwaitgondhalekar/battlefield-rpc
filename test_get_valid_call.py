from concurrent import futures
import grpc
import get_valid_position_pb2
import get_valid_position_pb2_grpc
import get_params_client_pb2, get_params_client_pb2_grpc
import create_soldier_pb2
import create_soldier_pb2_grpc as rpc1
import missile_approaching_pb2
import missile_approaching_pb2_grpc as rpc2
import all_taken_shelter_pb2
import all_taken_shelter_pb2_grpc as rpc3
import multiprocessing, threading


class Create_Soldier(rpc1.Create_SoldierServicer):
    def create_soldiers(self, request_iterator, context):
        print('create_soldiers')
        return create_soldier_pb2.soldier_output(msg="Soldiers Created")
        
class All_Taken_Shelter(rpc3.All_Taken_ShelterServicer):
    def all_taken_shelter(self, request, context):
        print('all_taken_shelter')
        return all_taken_shelter_pb2.taken_shelter_response(taken_shelter = True)
    
class Missile_Approaching(rpc2.Missile_ApproachingServicer):
    def missile_approaching(self, request, context):
        print('missile_approaching')
        return missile_approaching_pb2.missile_status()
    

rpc_list = [(Create_Soldier(), '[::]:40051', rpc1.add_Create_SoldierServicer_to_server), (Missile_Approaching(), '[::]:40052', rpc2.add_Missile_ApproachingServicer_to_server),(All_Taken_Shelter(),'[::]:40053',rpc3.add_All_Taken_ShelterServicer_to_server)]
servers = []
for i in range(len(rpc_list)):
    servers.append(grpc.server(futures.ThreadPoolExecutor(max_workers=2)))


for i, j in enumerate(rpc_list):
    obj, port, rpc_name  = j[0], j[1], j[2]
    rpc_name(obj, servers[i])
    servers[i].add_insecure_port(port)
    servers[i].start()

    
def target_fn():

    
    
    
    print("inside target fn")

    with grpc.insecure_channel('[::]:50052') as channel:
        print("first stub")
        stub = get_params_client_pb2_grpc.Get_Params_ClientStub(channel)
        print(stub.get_params_client(get_params_client_pb2.params_request()).N)
        channel.close()

    with grpc.insecure_channel('[::]:50051') as channel2:
        print("second stub")
        stub = get_valid_position_pb2_grpc.Get_Valid_PositionStub(channel2)

        available_pos = [(1,2),(3,4),(5,6)]
        avail_pos = []
        for x in available_pos:
            avail_pos.append(get_valid_position_pb2.available_positions(x_pos = x[0], y_pos = x[1]))

        response = stub.get_valid_position(avail_pos.__iter__())
        print (response.valid_x_pos, response.valid_y_pos)
        channel.close()

process_list = []

for i in range(1):
    # process_list.append(multiprocessing.Process(target=target_fn, args=()))
    process_list.append(threading.Thread(target=target_fn, args = ()))

for i in process_list:
    i.start()

# target_fn()

while True:
    pass
