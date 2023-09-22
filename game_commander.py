import grpc
import elect_commander_pb2
import elect_commander_pb2_grpc
import get_position_pb2
import get_position_pb2_grpc
import get_hyperparameters_pb2
import get_hyperparameters_pb2_grpc

N, M, t, T = None, None, None, None
battlefield = []

def get_hyperparams():
    global N, M, t, T
    with grpc.insecure_channel('localhost:50053') as channel:
        stub = get_hyperparameters_pb2_grpc.Get_HyperParamsStub(channel)
        response = stub.get_hyperparams(get_hyperparameters_pb2.param_request())
        N, M, t, T = response.N, response.M, response.t, response.T

def get_positions():
    global battlefield
    for i in range(N):
        for j in range(N):
            battlefield[i][j] = 0

    with grpc.insecure_channel('localhost:50052') as channel:
        stub = get_position_pb2_grpc.Get_PositionStub(channel)
        response = stub.get_position(get_position_pb2.position_all_request())
        for i in response:
            print("SOLDIER NUMBER = {}, X={}, Y={}".format(i.soldier_num, i.x_pos, i.y_pos))
            battlefield[i.x_pos][i.y_pos] = 1

def get_commander():
    # calling elect_commander in game_soldier.py

    with grpc.insecure_channel('localhost:50051') as channel:
        stub = elect_commander_pb2_grpc.ElectorStub(channel)
        response = stub.elect_commander(elect_commander_pb2.request(dummy=10))
        print ("ELECTED COMMANDER {}, X={}, Y={}, SPEED={}".format(response.soldier_number, response.x_pos, response.y_pos, response.speed_capacity))
    

def start_exec():
    global battlefield

    get_hyperparams()
    battlefield = [[0 for i in range(N)] for j in range(N)]
    get_positions()
    print(battlefield)
    get_commander()


if __name__ == '__main__':

    start_exec()
