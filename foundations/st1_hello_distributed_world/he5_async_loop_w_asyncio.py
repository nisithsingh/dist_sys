#!/usr/bin/env python3
import sys
import json
import asyncio

class Node:
    def __init__(self):
        self.node_id = None
        self.node_ids = []
        self.next_msg_id = 0

    async def send(self, dest, body):
        body["msg_id"] = self.next_msg_id
        self.next_msg_id += 1
        log(json.dumps({"src": self.node_id, "dest": dest, "body": body}))

    async def reply(self, request, body):
        body["in_reply_to"] = request["body"]["msg_id"]
        await self.send(request["src"], body)

    async def process_message(self, message):
        log("Processing New Message")
        body = message["body"]
        msg_type = body["type"]
        if msg_type == "init":
            self.node_id = body["node_id"]
            self.node_ids = body["node_ids"]
            await self.reply(message, {"type": "init_ok"})
        elif msg_type == "echo":
            await self.reply(message, {"type": "echo_ok", "echo": body["echo"]})

def log(*args, **kwargs):
    task = asyncio.current_task()
    print(f"[{task.get_name()}]", *args, file=sys.stderr, **kwargs)

async def main():
    node = Node()
    worker_count = 0
    for line in sys.stdin:
        message = json.loads(line)
        worker_count = worker_count + 1
        asyncio.create_task(node.process_message(message), name=f"Task {worker_count}")
        await asyncio.sleep(0)

if __name__ == "__main__":
    asyncio.run(main())

    #{"src":"c0","dest":"n1","body":{"type":"init","msg_id":1,"node_id":"n1","node_ids":["n1","n2"]}}    
    #{"src":"c1","dest":"n1","body":{"type":"echo","msg_id":2,"echo":"hello"}}