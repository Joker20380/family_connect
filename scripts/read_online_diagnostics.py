"""Local operator readback by Support ID; not an unauthenticated HTTP debug API."""
import argparse
import json
import time
from pathlib import Path
from control.friends.diagnostics import read


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database',required=True,type=Path)
    parser.add_argument('--support-id',required=True)
    args=parser.parse_args()
    print(json.dumps(read(args.database,args.support_id,int(time.time())),indent=2))


if __name__=='__main__':main()
