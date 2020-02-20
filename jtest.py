#!/usr/bin/python3
import subprocess
import shlex
def main():
    args = ["nproc", "--all"]
    out = subprocess.check_output(args)
    print(out)
    out = out.strip()
    print(out)
    nproc = "".join(chr(x) for x in out)
    nproc = "-j" + nproc
    print(nproc)
    rawargs = 'git log --pretty=oneline --grep "CORE-[0-9][0-9]"'

    args = shlex.split(rawargs)
    print(args)
    out = subprocess.check_output(args)
    print(out)
    notes = out.split(b"\n")
    print(notes)
    with open("release-notes.txt", "w") as rn:
        for x in notes:
            print(x, file=rn)

if __name__ == '__main__':
    main()
