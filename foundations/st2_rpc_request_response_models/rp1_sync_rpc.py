#!/usr/bin/env python3
import sys
import json
import threading

class Node:
    def __init__(self):
        self.node_id = None
        self.node_ids = []
        self.next_msg_id = 0
        self.lock = threading.Lock()
        self.pending = {}  # msg_id -> threading.Event

    def send(self, dest, body):
        with self.lock:
            body["msg_id"] = self.next_msg_id
            msg_id = self.next_msg_id
            self.next_msg_id += 1
        message = {"src": self.node_id, "dest": dest, "body": body}
        print(json.dumps(message), flush=True)
        return msg_id

    def reply(self, request, body):
        body["in_reply_to"] = request["body"]["msg_id"]
        self.send(request["src"], body)

    def sync_rpc(self, dest, body, timeout=10.0):
        # TODO: Send a message and block until a reply arrives
        # 1. Send the message and record its msg_id
        # 2. Create a threading.Event and store it in self.pending
        # 3. Wait for the event with the given timeout
        # 4. Return the reply body or None on timeout
        proxy_msg_id = self.send(dest, body)
        event = threading.Event()
        self.pending[proxy_msg_id] = {"event": event, "reply": None}
        print(f"Starting to wait now for {timeout} secs")
        received = event.wait(timeout=timeout)
        print("Stopping to wait now")
        if not received:
            del self.pending[proxy_msg_id]  # clean up
            return None

        return self.pending.pop(proxy_msg_id)["reply"]


    def handle_reply(self, body):
        # TODO: Check if this is a reply to a pending RPC
        # Match using in_reply_to field
        msg_id = body['in_reply_to']
        if msg_id in self.pending:
            self.pending[msg_id]["reply"] = body
            self.pending[msg_id]["event"].set()  # unblocks send_and_wait


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
        elif msg_type == "proxy":
            # TODO: Forward inner message to target using sync_rpc
            reply_body = node.sync_rpc(body['target'], body['inner'])
            if reply_body:
                node.reply(message, reply_body)
               
            node.handle_reply(body)

if __name__ == "__main__":
    main()

    {"src":"c0","dest":"n1","body":{"type":"init","msg_id":1,"node_id":"n1","node_ids":["n1","n2"]}}
    {"src":"c1","dest":"n1","body":{"type":"proxy","msg_id":2,"target":"n2","inner":{"type":"echo","echo":"test"}}}

    #{"src":"c1","dest":"n1","body":{"type":"echo","msg_id":2,"echo":"hello"}}

    {"src": "n2", "dest": "n1", "body": {"type": "echo_ok", "echo": "hello", "in_reply_to": 2, "msg_id": 1}}
