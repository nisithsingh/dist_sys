#!/usr/bin/env python3
import sys
import json
import asyncio
import time

def log(*args, **kwargs):
    task = asyncio.current_task()
    print(f"[{task.get_name()}]", *args, file=sys.stderr, **kwargs)

class Node:
    def __init__(self):
        self.node_id = None
        self.node_ids = []
        self.next_msg_id = 0
        #self.lock = threading.Lock()
        self.pending = {}
        self.replies = {}

    async def send(self, dest, body):
        #with self.lock:
        body["msg_id"] = self.next_msg_id
        msg_id = self.next_msg_id
        self.next_msg_id += 1
        message = {"src": self.node_id, "dest": dest, "body": body}
        log(json.dumps(message))
        return msg_id

    async def reply(self, request, body):
        body["in_reply_to"] = request["body"]["msg_id"]
        await self.send(request["src"], body)

    async def sync_rpc(self, dest, body, timeout=5):
        msg_id = await self.send(dest, dict(body))
        event = asyncio.Event()
        self.pending[msg_id] = event          # register before sleeping
        try:
            await asyncio.wait_for(event.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            pass
        result = self.replies.pop(msg_id, None)
        self.pending.pop(msg_id, None)
        return result

    async def handle_reply(self, body):
        reply_to = body.get("in_reply_to")
        if reply_to is not None and reply_to in self.pending:
            self.replies[reply_to] = body
            self.pending[reply_to].set()      # unblocks event.wait() in sync_rpc
            log(f"Reply received for msg_id={reply_to}")

    async def rpc_with_retry(self, dest, body, timeout=0.5, max_retries=3):
        # TODO: Implement retry loop around sync_rpc
        # Return (result, attempts) tuple
        for i in range(max_retries):

            result = await self.sync_rpc(dest, body)
            log(f"sync_rpc result in try {i+1}/{max_retries}: {result}")
            if result is not None:
                return result, i+1

    async def handle_message(self, message):
        body = message["body"]
        msg_type = body["type"]

        if msg_type == "init":
            self.node_id = body["node_id"]
            self.node_ids = body["node_ids"]
            await self.reply(message, {"type": "init_ok"})
        elif msg_type == "echo":
            await self.reply(message, {"type": "echo_ok", "echo": body["echo"]})
        elif msg_type == "relay":
            # TODO: Use rpc_with_retry to forward payload to target
            await self.rpc_with_retry(body["target"],body)
        else:
            await self.handle_reply(body)

async def main():
    node = Node()
    worker_count = 0
    loop = asyncio.get_event_loop()

    while True:
        line = await loop.run_in_executor(None, sys.stdin.readline)
        if not line:
            break
        line = line.strip()
        if not line:
            continue
        message = json.loads(line)
        worker_count += 1
        asyncio.create_task(node.handle_message(message), name=f"Task {worker_count}")

        

if __name__ == "__main__":
    asyncio.run(main())
    
    {"src":"c0","dest":"n1","body":{"type":"init","msg_id":1,"node_id":"n1","node_ids":["n1","n2"]}}
    {"src":"c1","dest":"n1","body":{"type":"relay","msg_id":2,"target":"n2","payload":{"type":"read"}}}
    {"src":"n2","dest":"n1","body":{"type":"relay_ok","in_reply_to":2}}