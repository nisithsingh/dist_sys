#!/usr/bin/env python3
import sys
import json

class MessageBody:
    def __init__(self, msg_type, msg_id=None, in_reply_to=None, **extra):
        self.type = msg_type
        self.msg_id = msg_id
        self.in_reply_to = in_reply_to
        self.extra = extra

    def to_dict(self):
        d = {"type": self.type}
        if self.msg_id is not None:
            d["msg_id"] = self.msg_id
        if self.in_reply_to is not None:
            d["in_reply_to"] = self.in_reply_to
        d.update(self.extra)
        return d

    @classmethod
    def from_dict(cls, data):
        if 'type' not in data:
            return None
        
        known_keys = {'type', 'msg_id', 'in_reply_to'}
        extra = {k: v for k, v in data.items() if k not in known_keys}
        
        return cls(
            data['type'],
            msg_id=data.get('msg_id'),
            in_reply_to=data.get('in_reply_to'),
            **extra
        )

class Message:
    def __init__(self, src, dest, body):
        self.src = src
        self.dest = dest
        self.body = body

    def to_json(self):
        # TODO: Serialize to JSON string
        json_message = {}
        json_message["src"] = self.src
        json_message["dest"] = self.dest
        json_message["body"] = self.body.to_dict() 
        return json.dumps(json_message)

    @classmethod
    def from_json(cls, json_str):
        # TODO: Deserialize from JSON string
        # Validate required fields: src, dest, body, body.type
        msg = json.loads(json_str)
        return Message(msg["src"], msg["dest"], MessageBody.from_dict(msg["body"]))

class Node:
    def __init__(self):
        self.node_id = None
        self.node_ids = []
        self.next_msg_id = 0

    def send(self, dest, body_dict):
        body_dict["msg_id"] = self.next_msg_id
        self.next_msg_id += 1
        msg = Message(self.node_id, dest, MessageBody.from_dict(body_dict))
        print(msg.to_json(), flush=True)

    def reply(self, request_msg, body_dict):
        body_dict["in_reply_to"] = request_msg.body.msg_id
        self.send(request_msg.src, body_dict)

def main():
    node = Node()

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = Message.from_json(line)
        except (ValueError, KeyError) as e:
            print(f"Invalid message: {e}", file=sys.stderr)
            continue

        if msg.body.type == "init":
            node.node_id = msg.body.extra["node_id"]
            node.node_ids = msg.body.extra["node_ids"]
            node.reply(msg, {"type": "init_ok"})
        elif msg.body.type == "echo":
            node.reply(msg, {"type": "echo_ok", "echo": msg.body.extra["echo"]})
        elif msg.body.type == "validate":
            # TODO: Parse the payload and report found fields
            fields = []
            valid = True
            if 'src' in  json.loads(msg.body.to_dict().get('payload')):
                fields.append('src') 
            if 'dest' in json.loads(msg.body.to_dict().get('payload')):
                fields.append('dest') 
            if 'body' in  json.loads(msg.body.to_dict().get('payload')):
                if 'type' in json.loads(msg.body.to_dict().get('payload')).get('body'):
                    fields.append('body.type') 
            if len(fields) < 3:
                valid = False

            node.reply(msg, {"type": "validate_ok", "valid": valid , "fields": fields})

if __name__ == "__main__":
    main()

    {"src":"c0","dest":"n1","body":{"type":"init","msg_id":1,"node_id":"n1","node_ids":["n1"]}}
    {"src":"c1","dest":"n1","body":{"type":"validate","msg_id":2,"payload":"{\"src\":\"a\",\"dest\":\"b\",\"body\":{\"type\":\"x\"}}"}}

    {"src":"c1","dest":"n1","body":{"type":"validate","msg_id":2,"payload":"{\"dest\":\"b\",\"body\":{\"type\":\"x\"}}"}}
