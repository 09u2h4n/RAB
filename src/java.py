import shutil
import os
from pathlib import Path
from typing import Union
import subprocess
import re

class Java:
    def __init__(self) -> None:
        self.java_path = self.find_java_path()
        self.java_version = self.find_java_version()
        pass

    def find_java_path(self) -> Union[Path, None]:
        java_path_env = os.environ.get("JAVA_HOME")
        java_path_which = shutil.which("java")

        if java_path_env:
            return Path(java_path_env) / "bin" / "java"
        elif java_path_which:
            return Path(os.path.realpath((java_path_which)))
        else:
            print("Java 11 not found. Please install.")
            return None

    def find_java_version(self) -> str:
        if not self.java_path:
            raise FileNotFoundError("Java 11 not found. Please install.")
        cmd = [self.java_path, "--version"]
        results = subprocess.run(cmd, capture_output=True, text=True)
        java_version = re.findall(r"\d*\d\.\d*\d\.\d*\d", results.stdout.split("\n")[0])[0]
        if not java_version.startswith("11"):
            raise ValueError("Java version is not 11, Please install Java 11")
        return java_version

if __name__ == "__main__":
    j = Java()
    print("Java Path: "+str(j.find_java_path()))
    print("Java version: "+j.find_java_version())
