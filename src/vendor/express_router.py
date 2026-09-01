from dataclasses import dataclass
from fastapi import APIRouter, Depends

class FastExpressRouter(APIRouter):

    def get(self, path, endpoint, dependency=None):
        self.add_api_route(
            path=path,
            endpoint=endpoint,
            methods=["GET"],
            dependencies=[dependency] if dependency else None
        )

    def post(self, path, endpoint, dependency=None):
        self.add_api_route(
                    path=path,
                    endpoint=endpoint,
                    methods=["POST"],
                    dependencies=[dependency] if dependency else None
                )

    def put(self, path, endpoint, dependency=None):
        self.add_api_route(
                    path=path,
                    endpoint=endpoint,
                    methods=["PUT"],
                    dependencies=[dependency] if dependency else None
                )

    def patch(self, path, endpoint, dependency=None):
        self.add_api_route(
                    path=path,
                    endpoint=endpoint,
                    methods=["PATCH"],
                    dependencies=[dependency] if dependency else None
                )

    def delete(self, path, endpoint, dependency=None):
        self.add_api_route(
                    path=path,
                    endpoint=endpoint,
                    methods=["DELETE"],
                    dependencies=[dependency] if dependency else None
                )
