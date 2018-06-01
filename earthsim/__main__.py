"""
Prototype of a param script that can set global_params via the
appropriate environment variable to execute an arbitrary command.

Example usage:

param -cmd 'jupyter nbconvert --execute GSSHA_Workflow_Batched_Example2.ipynb' -p rain_intensity=25 -p rain_duration=3600
"""

import os
import sys
import json
import argparse
import subprocess
from distutils import spawn

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-cmd',type=str)
    parser.add_argument("-p", nargs=1, action='append')
    args = parser.parse_args()
    if args.p is None:
        print('Please supply parameters using the -p flag')
        sys.exit(1)

    if args.cmd is None:
        print('Please supply a command string using the -cmd flag')
        sys.exit(1)

    execute(args)

def execute(args):
    split_strings = dict(el[0].split('=') for el in args.p)
    json_dict = {k:eval(v) for k,v in split_strings.items()}
    env = os.environ.copy() # Required on windows
    env['PARAM_JSON_INIT'] = json.dumps(json_dict)
    cmd = args.cmd.split()
    p = subprocess.Popen(cmd, env=env,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()

if __name__ == "__main__":
    main()
