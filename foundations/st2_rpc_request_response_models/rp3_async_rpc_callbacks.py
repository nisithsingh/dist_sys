#!/usr/bin/env python3
import sys
import json

def callback_log(body):
        print("Callback execution: ",body)

class Node:
    def __init__(self):
        self.node_id = None
        self.node_ids = []
        self.next_msg_id = 0
        self.callbacks = {}  # msg_id -> callback function

    def send(self, dest, body):
        body["msg_id"] = self.next_msg_id
        msg_id = self.next_msg_id
        self.next_msg_id += 1
        message = {"src": self.node_id, "dest": dest, "body": body}
        print(json.dumps(message), flush=True)
        return msg_id

    def reply(self, request, body):
        body["in_reply_to"] = request["body"]["msg_id"]
        self.send(request["src"], body)

    def async_rpc(self, dest, body, callback):
        # TODO: Send message and register callback for the reply
        # The callback should be called with the reply body when it arrives
        #event = threading.Event()
        
        msg_id = self.send(dest, dict(body))
        self.callbacks[msg_id] = callback
        #event.wait(timeout=timeout)
        # result = self.replies.pop(msg_id, None)
        # self.pending.pop(msg_id, None)
        # return result
        return

    def handle_reply(self, body):
        # TODO: Look up callback by in_reply_to and invoke it
        reply_to = body.get("in_reply_to")
        if reply_to is not None and reply_to in self.callbacks:
            self.callbacks[reply_to](body)
            self.callbacks.pop(reply_to)
            

def main():
    node = Node()

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        message = json.loads(line)
        body = message["body"]
        msg_type = body["type"]

        if msg_type == "init":
            node.node_id = body["node_id"]
            node.node_ids = body["node_ids"]
            node.reply(message, {"type": "init_ok"})
        elif msg_type == "echo":
            node.reply(message, {"type": "echo_ok", "echo": body["echo"]})
        elif msg_type == "batch_echo":
            # TODO: Send async echo RPCs for each value, collect results
            values = body['values']
            for val in values:
                body_val = {} 
                body_val['type'] = "echo"
                body_val['echo'] = val

                node.async_rpc(message['dest'], body_val, callback_log)
        else:
            node.handle_reply(body)

if __name__ == "__main__":
    main()

    {"src":"c0","dest":"n1","body":{"type":"init","msg_id":1,"node_id":"n1","node_ids":["n1"]}}
    #{"src":"c1","dest":"n1","body":{"type":"echo","msg_id":2,"echo":"async"}}

    {"src":"c1","dest":"n1","body":{"type":"batch_echo","msg_id":2,"values":["x"]}}

    {"src": "n1", "dest": "n1", "body": {"type": "echo_ok", "echo": "x", "in_reply_to": 1, "msg_id": 2}}