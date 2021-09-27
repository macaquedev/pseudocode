from typing import List
import os
import difflib
from .executor import PSCodeExecutor


def similar(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a, b).ratio()


def get_similar_files(filename: str) -> List[str]:
    dirname = os.path.dirname(os.path.abspath(filename))

    paths = [os.path.join(dirname, i) for i in os.listdir(dirname) if i.endswith(".psc")]

    for directory in [i for i in os.listdir(dirname) if os.path.isdir(i)]:
        paths.extend([
            os.path.join(dirname, directory, i) for i in os.listdir(os.path.abspath(directory)) if i.endswith(".psc")
        ])

    paths.sort(key=lambda x: similar(x, os.path.abspath(filename)), reverse=True)
    return paths


def repl():
    executor = PSCodeExecutor()
    print("PSCode Version 0.1.0")
    print("Created by macaquedev\n")
    while True:
        code = input("pscode >>> ")
        executor.execute("<repl>", code, [])


def exec_file(filename: str, args: List[str]):
    try:
        with open(filename) as f:
            code = f.read()
            executor = PSCodeExecutor()
            executor.execute(filename, code, args)

    except FileNotFoundError:
        print(f"pscode > ERROR:"
              f"Can't open file \"{os.path.abspath(filename)}\", no such file found.")
        files = get_similar_files(filename)
        if len(files) > 5:
            files = files[:5]
            print("Showing only top 5 results as more than 5 .psc files found.")
        elif len(files) == 0:
            print("No .psc files found in directory. Have you given your file the correct file extension?")
            return
        print("Did you mean: ")
        length = max([len(i) for i in files]) + 5
        for file in files:
            print(f"    pscode {file.ljust(length)} "
                  f"Similarity: "
                  f"{round(similar(os.path.abspath(filename), file) * 100, 2)}%")
