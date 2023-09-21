import grpc
import elect_commander_pb2
import elect_commander_pb2_grpc



def start_exec():

    # calling elect_commander in game_soldier.py

    with grpc.insecure_channel('localhost:50051') as channel:
        stub = elect_commander_pb2_grpc.ElectorStub(channel)


        response = stub.elect_commander(elect_commander_pb2.request(dummy=10))


        print ("ELECTED COMMANDER {}, X={}, Y={}, SPEED={}".format(response.soldier_number, response.x_pos, response.y_pos, response.speed_capacity))
    


if __name__ == '__main__':

    start_exec()