import uuid
from protocol.vda_2_0_0.vda5050_2_0_0_order import Order
from protocol.vda_2_0_0.vda5050_2_0_0_action import Action, BlockingType

class BaseRouteController:
    """Base route controller that defines standard VDA 5050 orders for AGVs"""
    def __init__(self, layout: dict, scenario: dict):
        self.layout = layout
        self.scenario = scenario
        self.nodes_by_id = {n["node_id"]: n for n in layout["nodes"]}
        
    def _create_action(self, action_type: str, action_id: str = None) -> dict:
        """Create a VDA 5050 action dict"""
        return {
            "actionId": action_id or str(uuid.uuid4())[:8],
            "actionType": action_type,
            "blockingType": "HARD",
            "actionParameters": []
        }

    def get_orders(self) -> dict:
        """Returns a dict of AGV serial numbers to VDA 5050 order dictionaries"""
        raise NotImplementedError
