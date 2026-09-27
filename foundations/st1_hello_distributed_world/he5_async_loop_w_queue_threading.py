#!/usr/bin/env python3
import sys
import json
import threading
from queue import Queue

NUM_WORKERS = 4  # fixed thread pool size

class Node:
    def __init__(self):
        self.node_id = None
        self.node_ids = []
        self.next_msg_id = 0
        self.lock = threading.Lock()
        self.stdout_lock = threading.Lock()
        self.queue = Queue()  # shared message queue

    def send(self, dest, body):
        with self.lock:
            body["msg_id"] = self.next_msg_id
            self.next_msg_id += 1
        message = {"src": self.node_id, "dest": dest, "body": body}
        with self.stdout_lock:
            print(json.dumps(message), flush=True)

    def reply(self, request, body):
        body["in_reply_to"] = request["body"]["msg_id"]
        self.send(request["src"], body)

    def handle_init(self, message):
        body = message["body"]
        self.node_id  = body["node_id"]
        self.node_ids = body["node_ids"]
        print(f"[DEBUG] Node initialized: id={self.node_id} peers={self.node_ids}", file=sys.stderr)
        self.reply(message, {"type": "init_ok"})

    def handle_message(self, message):
        msg_type = message["body"].get("type")
        print(f"[DEBUG] Handling message type={msg_type}", file=sys.stderr)
        if msg_type == "init":
            self.handle_init(message)
        else:
            print(f"[WARN] Unknown message type: {msg_type}", file=sys.stderr)

    def worker(self):
        # each worker loops forever, pulling messages from the queue
        while True:
            message = self.queue.get()
            print("[worker] Queue length: ",self.queue.qsize())       # blocks until a message is available
            try:
                self.handle_message(message)
            except Exception as e:
                print(f"[ERROR] Handler failed: {e}", file=sys.stderr)
            finally:
                self.queue.task_done()       # signal that this message is done


def main():
    node = Node()

    # spin up fixed pool of worker threads once
    for _ in range(NUM_WORKERS):
        t = threading.Thread(target=node.worker, daemon=True)
        t.start()

    # main thread just reads and enqueues — never blocks on handling
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
            node.queue.put(message)          # hand off to a worker
            print("[main] Queue length: ",node.queue.qsize())
        except json.JSONDecodeError as e:
            print(f"[ERROR] Invalid JSON: {e}", file=sys.stderr)

    node.queue.join()   # wait for all queued messages to be processed before exit


if __name__ == "__main__":
    main()

# {"src":"c0","dest":"n1","body":{"type":"init","msg_id":1,"node_id":"n1","node_ids":["n1"]}}
# {"src":"c1","dest":"n1","body":{"type":"echo","msg_id":2,"echo":"test1"}}
{"src":"c2","dest":"n1","body":{"type":"echo","msg_id":3,"echo":"test2"}}

