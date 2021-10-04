from src.main import repl, exec_file

import argparse

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("filename", nargs="?", help="File that pscode should run")
    args, unknown_args = ap.parse_known_args()
    if args.filename:
        exec_file(args.filename, unknown_args)
    else:
        repl()

