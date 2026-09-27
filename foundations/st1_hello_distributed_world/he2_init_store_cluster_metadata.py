#!/usr/bin/env python3
import sys
import json

class Node:
    def __init__(self):
        self.node_id = None
        self.node_ids = []
        self.next_msg_id = 0
    
    def send(self, dest, body):
        # TODO: Implement message sending
        response = {}
        response["src"] = self.node_id
        response["dest"] = dest
        response["body"] = body
        print(json.dumps(response))
    
    def reply(self, request, body):
        # TODO: Implement reply with in_reply_to
        reply_body = {}
        reply_body['type'] = "init_ok"
        reply_body['in_reply_to'] = request['msg_id']
        reply_body['msg_id'] = self.next_msg_id        
        self.next_msg_id = self.next_msg_id+ 1
        return reply_body


def main():
    node = Node()
    
    for line in sys.stdin:
        message = json.loads(line)
        body = message["body"]
        msg_type = body["type"]
        
        if msg_type == "init":
            # TODO: Handle init message
            # 1. Store node_id and node_ids
            # 2. Reply with init_ok
            node.node_ids = body.get("node_ids",[])
            node.node_id = body.get("node_id",[])
            reply_body = node.reply(body, None)
            node.send(message['src'],reply_body)

if __name__ == "__main__":
    main()

    # {"src":"c0","dest":"n1","body":{"type":"init","msg_id":1,"node_id":"n1","node_ids":["n1"]}}
