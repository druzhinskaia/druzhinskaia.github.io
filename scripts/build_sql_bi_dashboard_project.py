"""Rebuild from the author's existing data; preserve raw records."""
from pathlib import Path
import subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
PROJECT=ROOT/'portfolio-projects/04-sql-bi-dashboard'
if __name__=='__main__':
    subprocess.run([sys.executable,str(PROJECT/'scripts/build.py'),'--project-root',str(PROJECT)],check=True)
