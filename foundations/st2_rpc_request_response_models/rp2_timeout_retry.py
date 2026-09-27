#!/usr/bin/env python3
import sys
import json
import threading
import time

class Node:
    def __init__(self):
        self.node_id = None
        self.node_ids = []
        self.next_msg_id = 0
        self.lock = threading.Lock()
        self.pending = {}
        self.replies = {}

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

    def sync_rpc(self, dest, body, timeout=0.5):
        event = threading.Event()
        msg_id = self.send(dest, dict(body))
        self.pending[msg_id] = event
        event.wait(timeout=timeout)
        result = self.replies.pop(msg_id, None)
        self.pending.pop(msg_id, None)
        return result

    def rpc_with_retry(self, dest, body, timeout=0.5, max_retries=3):
        # TODO: Implement retry loop around sync_rpc
        # Return (result, attempts) tuple
        for i in range(max_retries):
            result = self.sync_rpc(dest, body, timeout)
            #print(f"sync_rpc result in try {i+1}/{max_retries}: {result}")
            if result is not None:
                return result, i+1

    def handle_reply(self, body):
        reply_to = body.get("in_reply_to")
        if reply_to is not None and reply_to in self.pending:
            self.replies[reply_to] = body
            self.pending[reply_to].set()

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
        elif msg_type == "relay":
            # TODO: Use rpc_with_retry to forward payload to target
            node.rpc_with_retry(body["target"],body['payload'])
        else:
            node.handle_reply(body)

if __name__ == "__main__":
    main()
