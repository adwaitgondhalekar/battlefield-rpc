# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

import missile_approaching_pb2 as missile__approaching__pb2


class Missile_ApproachingStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.missile_approaching = channel.unary_unary(
                '/Missile_Approaching/missile_approaching',
                request_serializer=missile__approaching__pb2.missile.SerializeToString,
                response_deserializer=missile__approaching__pb2.missile_status.FromString,
                )


class Missile_ApproachingServicer(object):
    """Missing associated documentation comment in .proto file."""

    def missile_approaching(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_Missile_ApproachingServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'missile_approaching': grpc.unary_unary_rpc_method_handler(
                    servicer.missile_approaching,
                    request_deserializer=missile__approaching__pb2.missile.FromString,
                    response_serializer=missile__approaching__pb2.missile_status.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'Missile_Approaching', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class Missile_Approaching(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def missile_approaching(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/Missile_Approaching/missile_approaching',
            missile__approaching__pb2.missile.SerializeToString,
            missile__approaching__pb2.missile_status.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
