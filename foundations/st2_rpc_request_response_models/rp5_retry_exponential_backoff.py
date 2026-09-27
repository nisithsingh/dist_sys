#!/usr/bin/env python3
import sys
import json
import time
import random

class Node:
    def __init__(self):
        self.node_id = None
        self.node_ids = []
        self.next_msg_id = 0

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

    def compute_backoff_delay(self, attempt, base_delay=0.1, max_delay=2.0):
        # TODO: Calculate exponential backoff delay with jitter
        # attempt starts at 0
        # Return delay in seconds
        delay = 0
        delay = base_delay * 2**attempt
        delay += random.uniform(0, delay * 0.1) 
        delay = min(delay,max_delay)
        return delay

    def get_delay_schedule(self, max_retries=5, base_delay=0.1, max_delay=2.0):
        # TODO: Return list of delays for each retry attempt
        # Each delay should use compute_backoff_delay
        delay_result = 0
        for atmpt in range(max_retries):
            delay_result += self.compute_backoff_delay(atmpt, base_delay, max_delay)
        return delay_result * 100
    
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
        elif msg_type == "compute_backoff":
            # Return the delay schedule for visualization
            # TODO: Compute and return the schedule
            max_retries = body["max_retries"]
            base_delay = body["base_delay"]
            total_delay = node.get_delay_schedule(max_retries, base_delay)
            node.reply(message, {"type": "compute_backoff_ok", "attempts": max_retries, "total_delay_ms": total_delay})

if __name__ == "__main__":
    main()

# TODO: Write a comment explaining why exponential backoff helps under high load
# (at least 100 words)
{"src":"c0","dest":"n1","body":{"type":"init","msg_id":1,"node_id":"n1","node_ids":["n1"]}}
{"src":"c1","dest":"n1","body":{"type":"compute_backoff","msg_id":2,"max_retries":3,"base_delay":0.1}}