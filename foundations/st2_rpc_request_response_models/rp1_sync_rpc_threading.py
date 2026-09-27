#!/usr/bin/env python3
import sys
import json
import threading

def log(*args, **kwargs):
    thread = threading.current_thread()
    print(f"[{thread.name}]", *args, file=sys.stderr, **kwargs)

class Node:
    def __init__(self):
        self.node_id = None
        self.node_ids = []
        self.next_msg_id = 0
        self.lock = threading.Lock()
        self.stdout_lock = threading.Lock()
        self.pending = {}  # msg_id -> {"event": Event, "reply": None}

    def send(self, dest, body):
        with self.lock:
            body["msg_id"] = self.next_msg_id
            msg_id = self.next_msg_id
            self.next_msg_id += 1
        message = {"src": self.node_id, "dest": dest, "body": body}
        with self.stdout_lock:
            log(json.dumps(message))
        return msg_id

    def reply(self, request, body):
        body["in_reply_to"] = request["body"]["msg_id"]
        self.send(request["src"], body)

    def sync_rpc(self, dest, body, timeout=10.0):
        msg_id = self.send(dest, body)

        event = threading.Event()
        with self.lock:
            self.pending[msg_id] = {"event": event, "reply": None}

        log(f"[DEBUG] Waiting for reply to msg_id={msg_id}")
        received = event.wait(timeout=timeout)

        if not received:
            log(f"[DEBUG] Timeout waiting for msg_id={msg_id}")
            with self.lock:
                self.pending.pop(msg_id, None)
            return None

        with self.lock:
            return self.pending.pop(msg_id)["reply"]

    def handle_reply(self, body):
        msg_id = body.get("in_reply_to")
        if msg_id is None:
            return
        with self.lock:
            pending = self.pending.get(msg_id)
        if pending:
            pending["reply"] = body
            pending["event"].set()  # unblocks sync_rpc
            log(f"[DEBUG] Reply received for msg_id={msg_id}")

    def handle_message(self, message):
        body     = message["body"]
        msg_type = body["type"]

        if msg_type == "init":
            self.node_id  = body["node_id"]
            self.node_ids = body["node_ids"]
            self.reply(message, {"type": "init_ok"})

        elif msg_type == "echo":
            self.reply(message, {"type": "echo_ok", "echo": body["echo"]})

        elif msg_type == "proxy":
            # runs in its own thread — blocks here without freezing main loop
            reply_body = self.sync_rpc(body["target"], body["inner"])
            if reply_body:
                self.reply(message, reply_body)
            else:
                self.reply(message, {"type": "error", "text": "timeout"})

        elif "in_reply_to" in body:
            # reply from another node — unblocks a waiting sync_rpc
            self.handle_reply(body)

def main():
    node = Node()
    worker_count = 0  # counter to name threads

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError as e:
            log(f"[ERROR] Invalid JSON: {e}")
            continue

        worker_count += 1
        t = threading.Thread(target=node.handle_message, args=(message,), daemon=True, name=f"Worker-{worker_count}")
        t.start()


if __name__ == "__main__":
    main()

    {"src":"c0","dest":"n1","body":{"type":"init","msg_id":1,"node_id":"n1","node_ids":["n1","n2"]}}
    {"src":"c1","dest":"n1","body":{"type":"proxy","msg_id":2,"target":"n2","inner":{"type":"echo","echo":"test"}}}
    {"src": "n2", "dest": "n1", "body": {"type": "echo_ok", "echo": "hello", "in_reply_to": 2, "msg_id": 1}}

    #{"src":"c1","dest":"n1","body":{"type":"echo","msg_id":2,"echo":"hello"}}