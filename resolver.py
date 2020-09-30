import subprocess
import os

def resolve_dep(package):
    bashCommand = "pip3 install " + package
    process = subprocess.Popen(bashCommand.split(), stdout=open(os.devnull, 'wb'))
    process.wait()
