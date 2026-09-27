#!/usr/bin/env python3
import sys
import json
import time

class Node:
    def __init__(self):
        self.node_id = None
        self.node_ids = []
        self.next_msg_id = 0
        self.callbacks = {}      # msg_id -> callback
        self.callback_times = {} # msg_id -> registration timestamp
        self.reap_threshold = 20.0  # seconds

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
        msg_id = self.send(dest, body)
        self.callbacks[msg_id] = callback
        self.callback_times[msg_id] = time.time()

    def handle_reply(self, body):
        reply_to = body.get("in_reply_to")
        if reply_to is not None and reply_to in self.callbacks:
            print("Before clearing: ",len(self.callbacks))
            callback_to_call = self.callbacks.pop(reply_to)
            self.callback_times.pop(reply_to, None)
            callback_to_call(body)
            print("After clearing: ",len(self.callbacks))

    def reap_expired_callbacks(self):
        # TODO: Find and remove callbacks older than self.reap_threshold
        # Invoke each expired callback with None to signal timeout
        # Return the number of reaped callbacks
        current_time = time.time()
        expired_ids = [
        msg_id for msg_id, t in self.callback_times.items()
        if current_time - t > self.reap_threshold
        ]
        for msg_id in expired_ids:
            callback = self.callbacks.pop(msg_id)
            self.callback_times.pop(msg_id)
            callback(None)
        return len(expired_ids)


def callback_log(body):
        if body is None:
            print("Callback Execution Timing out")
        else:    
            print("Callback execution: ",body)

def main():
    node = Node()

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        message = json.loads(line)
        body = message["body"]
        msg_type = body["type"]

        # Reap before processing each message
        node.reap_expired_callbacks()

        if msg_type == "init":
            node.node_id = body["node_id"]
            node.node_ids = body["node_ids"]
            node.reply(message, {"type": "init_ok"})
        elif msg_type == "echo":
            node.reply(message, {"type": "echo_ok", "echo": body["echo"]})
        elif msg_type == "pending_count":
            # TODO: Return count of pending callbacks
            node.reply(message, {"type": "pending_count_ok", "count": len(node.callbacks)})
        elif msg_type == "send_fire_forget":
            # TODO: Send async RPC with a no-op callback, reply with pending count
            node.async_rpc(body["target"],body['payload'], callback_log)
            node.reply(message, {"type": "send_fire_forget_ok", "pending": len(node.callbacks)})
        else:
            node.handle_reply(body)

if __name__ == "__main__":
    main()

    {"src":"c0","dest":"n1","body":{"type":"init","msg_id":1,"node_id":"n1","node_ids":["n1","n2"]}}
    {"src":"c1","dest":"n1","body":{"type":"send_fire_forget","msg_id":2,"target":"n2","payload":{"type":"echo","echo":"lost"}}}

    {"src": "n2", "dest": "n1", "body": {"type": "echo_ok", "echo": "lost", "in_reply_to": 1, "msg_id": 1}}
    