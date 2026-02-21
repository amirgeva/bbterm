#!/usr/bin/env python3
import argh
from bbterm.main import run_terminal

def main(host: str, port: int):
	run_terminal(host, port)

if __name__ == '__main__':
    argh.dispatch_command(main)

