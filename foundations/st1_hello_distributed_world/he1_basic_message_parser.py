#!/usr/bin/env python3
import sys
import json

def main():
    # TODO: Read JSON messages from stdin
    # Each line is a complete JSON message
    # Parse and print: PARSED: src|dest|body_type
    # Log details to stderr for debugging

    for line in sys.stdin:
        if line!="\n":
            try:
                json_line = json.loads(line)
                # Your code here
                source = json_line.get('src', 'unknown')
                dest = json_line.get('dest', 'unknown')
                body  = json_line.get('body', {})
                msg_type = body.get('type', 'unknown')
                print(f"PARSED: {source}|{dest}|{msg_type}")
            except json.JSONDecodeError as e:
                print("Malformed json at line: ",line, file= sys.stderr )
        else:
            print("Empty Line at line: ",line, file= sys.stderr)

if __name__ == "__main__":
    main()

#{ "src": "c1", "dest": "n1", "body": {"type": "echo", "msg_id": 1, "echo": "hello"}}