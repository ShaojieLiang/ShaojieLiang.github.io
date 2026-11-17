"""Build the complete personal website from the sources tracked in dev/."""
import argparse
import pathlib
import subprocess
import sys

ROOT=pathlib.Path(__file__).resolve().parent
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output',type=pathlib.Path,default=ROOT,help='Static output directory (defaults to repository root)')
args=parser.parse_args()
subprocess.run([sys.executable,str(ROOT/'dev/tools/build_mirror.py')],cwd=ROOT,check=True)
subprocess.run([sys.executable,str(ROOT/'dev/tools/export_pages.py'),str(args.output.resolve())],cwd=ROOT,check=True)
