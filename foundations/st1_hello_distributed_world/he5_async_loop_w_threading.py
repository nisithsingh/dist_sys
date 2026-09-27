#!/usr/bin/env python3
import sys
import json
import threading
from queue import Queue

class Node:
    def __init__(self):
        self.node_id = None
        self.node_ids = []
        self.next_msg_id = 0
        self.lock = threading.Lock()
    
    def send(self, dest, body):
        with self.lock:
            body["msg_id"] = self.next_msg_id
            self.next_msg_id += 1
        message = {"src": self.node_id, "dest": dest, "body": body}
        # TODO: Thread-safe output
        print(json.dumps(message), flush=True)
    
    def reply(self, request, body):
        body["in_reply_to"] = request["body"]["msg_id"]
        self.send(request["src"], body)

    def process_message(self, message):
        body = message["body"]
        msg_type = body["type"]
        if msg_type == "init":
            self.node_id = body["node_id"]
            self.node_ids = body["node_ids"]
            self.reply(message, {"type": "init_ok"})
        elif msg_type == "echo":
            # TODO: Handle echo message
            # Reply with echo_ok containing the same echo value
            self.reply(message, {"type": "echo_ok", "echo": body['echo']})

    def handle_message(self, message):
        # TODO: Handle message in separate thread
        t = threading.Thread(target=self.process_message, args=(message,))
        t.start()
        

def main():
    node = Node()
    
    # TODO: Implement concurrent message handling
    # 1. Read messages in main thread
    # 2. Dispatch to handlers concurrently
    
    for line in sys.stdin:
        message = json.loads(line)
        # Currently synchronous - make this concurrent
        node.handle_message(message)

if __name__ == "__main__":
    main()

    {"src":"c0","dest":"n1","body":{"type":"init","msg_id":1,"node_id":"n1","node_ids":["n1","n2"]}}    
    {"src":"c1","dest":"n1","body":{"type":"echo","msg_id":2,"echo":"hello"}}
