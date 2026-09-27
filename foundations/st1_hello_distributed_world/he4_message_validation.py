#!/usr/bin/env python3
import sys
import json

class Node:
    def __init__(self):
        self.node_id = None
        self.node_ids = []
        self.next_msg_id = 0
    
    def send(self, dest, body):
        body["msg_id"] = self.next_msg_id
        self.next_msg_id += 1
        message = {"src": self.node_id, "dest": dest, "body": body}
        print(json.dumps(message), flush=True)
    
    def reply(self, request, body):
        body["in_reply_to"] = request["body"]["msg_id"]
        self.send(request["src"], body)
    
    def validate_message(self, message):
        # TODO: Validate message structure
        # Return True if valid, False otherwise
        # Log errors to stderr
        status = True
        src_present = 'src' in message.keys()
        if not src_present:
            status= False
            print("Key not present: src", file=sys.stderr)
        dest_present = 'dest' in message.keys()
        if not dest_present:
            status= False
            print("Key not present: dest_present", file=sys.stderr)
        msg_type_present = 'type' in message.get("body").keys()
        if not msg_type_present:
            status= False
            print("Key not present: msg_type_present", file=sys.stderr)
        msg_id_present = 'msg_id' in message.get("body").keys()
        if not msg_id_present:
            status= False
            print("Key not present: msg_id_present", file=sys.stderr)

        return status

def main():
    node = Node()
    
    for line in sys.stdin:
        try:
            message = json.loads(line)
        except json.JSONDecodeError as e:
            print(f"Invalid JSON: {e}", file=sys.stderr)
            continue
        
        if node.validate_message(message):
        
            body = message["body"]
            msg_type = body["type"]
            
            if msg_type == "init":
                node.node_id = body["node_id"]
                node.node_ids = body["node_ids"]
                node.reply(message, {"type": "init_ok"})
            elif msg_type == "echo":
                node.reply(message, {"type": "echo_ok", "echo": body["echo"]})
        else:
            print(f"Invalid Message Structure: ", file=sys.stderr)
if __name__ == "__main__":
    main()

    #{"src":"c0","dest":"n1","body":{"type":"init","msg_id":1,"node_id":"n1","node_ids":["n1"]}}
    # {"dest":"n1","body":{"type":"init","msg_id":1,"node_id":"n1","node_ids":["n1"]}}
