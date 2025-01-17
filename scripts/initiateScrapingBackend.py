#!/usr/bin/python3

import os
from pathlib import Path
import requests
import json

# For decompressing the geckodriver that comes compressed in the .tar.gz format when downloading it
import tarfile

import sqlite3

from modules import elastic
from scripts import configOptions

# Mozilla will have an api endpoint giving a lot of information about the latest releases for the geckodriver, from which the url for the linux 64 bit has to be extracted
def extractDriverURL():
    driverDetails = json.loads(
        requests.get(
            "https://api.github.com/repos/mozilla/geckodriver/releases/latest"
        ).text
    )

    for platformRelease in driverDetails["assets"]:
        if platformRelease["name"].endswith("linux64.tar.gz"):
            return platformRelease["browser_download_url"]


# Downloading and extracting the .tar.gz file the geckodriver is stored in into the tools directory
def downloadDriver(driverURL):
    driverContents = requests.get(driverURL, stream=True)
    with tarfile.open(fileobj=driverContents.raw, mode="r|gz") as driverFile:
        def is_within_directory(directory, target):
            
            abs_directory = os.path.abspath(directory)
            abs_target = os.path.abspath(target)
        
            prefix = os.path.commonprefix([abs_directory, abs_target])
            
            return prefix == abs_directory
        
        def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
        
            for member in tar.getmembers():
                member_path = os.path.join(path, member.name)
                if not is_within_directory(path, member_path):
                    raise Exception("Attempted Path Traversal in Tar File")
        
            tar.extractall(path, members, numeric_owner=numeric_owner) 
            
        
        safe_extract(driverFile, path=Path("./tools/"))


def main():

    configOptions.logger.info("Downloading and extracting the geckodriver...")

    downloadDriver(extractDriverURL())

    configOptions.logger.info("Configuring elasticsearch")
    elastic.configureElasticsearch(configOptions)


if __name__ == "__main__":
    main()
