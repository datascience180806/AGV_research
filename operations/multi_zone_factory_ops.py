from operations.base_router import BaseRouteController

class MultiZoneFactoryRouter(BaseRouteController):
    """Router implementing deterministic paths for the multi_zone_factory layout"""

    def get_orders(self) -> dict:
        map_id = self.layout["map_id"]
        
        # AGV_01 path: DOCK_IN_1 -> STORAGE_A1
        # Pickup at DOCK_IN_1, dropoff at STORAGE_A1
        agv01_order = {
            "orderId": "order_agv01_001",
            "orderUpdateId": 0,
            "nodes": [
                {
                    "nodeId": "DOCK_IN_1",
                    "sequenceId": 1,
                    "released": True,
                    "nodePosition": {"x": 10.0, "y": 10.0, "mapId": map_id},
                    "actions": [self._create_action("pickUp", "pickup_REQ_001")]
                },
                {
                    "nodeId": "STORAGE_A1",
                    "sequenceId": 3,
                    "released": True,
                    "nodePosition": {"x": 30.0, "y": 70.0, "mapId": map_id},
                    "actions": [self._create_action("dropOff", "dropoff_REQ_001")]
                }
            ],
            "edges": [
                {
                    "edgeId": "E01",
                    "sequenceId": 2,
                    "released": True,
                    "startNodeId": "DOCK_IN_1",
                    "endNodeId": "STORAGE_A1",
                    "actions": []
                }
            ]
        }

        # AGV_02 path: DOCK_IN_2 -> ASSEMBLY_B
        # Pickup at DOCK_IN_2, dropoff at ASSEMBLY_B
        agv02_order = {
            "orderId": "order_agv02_001",
            "orderUpdateId": 0,
            "nodes": [
                {
                    "nodeId": "DOCK_IN_2",
                    "sequenceId": 1,
                    "released": True,
                    "nodePosition": {"x": 10.0, "y": 30.0, "mapId": map_id},
                    "actions": [self._create_action("pickUp", "pickup_REQ_002")]
                },
                {
                    "nodeId": "ASSEMBLY_B",
                    "sequenceId": 3,
                    "released": True,
                    "nodePosition": {"x": 80.0, "y": 50.0, "mapId": map_id},
                    "actions": [self._create_action("dropOff", "dropoff_REQ_002")]
                }
            ],
            "edges": [
                {
                    "edgeId": "E05",
                    "sequenceId": 2,
                    "released": True,
                    "startNodeId": "DOCK_IN_2",
                    "endNodeId": "ASSEMBLY_B",
                    "actions": []
                }
            ]
        }

        return {
            "AGV_01": agv01_order,
            "AGV_02": agv02_order
        }
