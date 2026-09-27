#!/usr/bin/env python3
import sys
import json
import threading
import time

def log(*args, **kwargs):
    thread = threading.current_thread()
    print(f"[{thread.name}]", *args, file=sys.stderr, **kwargs)

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
        log(json.dumps(message))
        return msg_id

    def reply(self, request, body):
        body["in_reply_to"] = request["body"]["msg_id"]
        self.send(request["src"], body)

    def sync_rpc(self, dest, body, timeout=5):
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

            result = self.sync_rpc(dest, body)
            log(f"sync_rpc result in try {i+1}/{max_retries}: {result}")
            if result is not None:
                return result, i+1

    def handle_reply(self, body):
        reply_to = body.get("in_reply_to")
        if reply_to is not None and reply_to in self.pending:
            self.replies[reply_to] = body
            self.pending[reply_to].set()
            log(f"[DEBUG] Reply received for msg_id={reply_to}")

    def handle_message(self, message):
        body = message["body"]
        msg_type = body["type"]

        if msg_type == "init":
            self.node_id = body["node_id"]
            self.node_ids = body["node_ids"]
            self.reply(message, {"type": "init_ok"})
        elif msg_type == "echo":
            self.reply(message, {"type": "echo_ok", "echo": body["echo"]})
        elif msg_type == "relay":
            # TODO: Use rpc_with_retry to forward payload to target
            self.rpc_with_retry(body["target"],body)
        else:
            self.handle_reply(body)

def main():
    node = Node()
    worker_count = 0
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        message = json.loads(line)


        worker_count += 1
        t = threading.Thread(target=node.handle_message, args=(message,), daemon=True, name=f"Worker-{worker_count}")
        t.start()

        

if __name__ == "__main__":
    main()

    {"src":"c0","dest":"n1","body":{"type":"init","msg_id":1,"node_id":"n1","node_ids":["n1","n2"]}}
    {"src":"c1","dest":"n1","body":{"type":"relay","msg_id":2,"target":"n2","payload":{"type":"read"}}}
    {"src":"n2","dest":"n1","body":{"type":"relay_ok","in_reply_to":2}}