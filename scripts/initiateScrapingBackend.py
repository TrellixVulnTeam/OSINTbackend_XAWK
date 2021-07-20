#!/usr/bin/python3

try:
    # For if the user wants verbose output
    from __main__ import debugMessages
except:
    debugMessages = True

# Used for creating a connection to the database
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

import os
from pathlib import Path
import requests
import json
# For decompressing the geckodriver that comes compressed in the .tar.gz format when downloading it
import tarfile

from OSINTmodules import OSINTdatabase
from OSINTmodules.OSINTmisc import printDebug

postgresqlPassword = ""

def createFolder(folderName, purpose):
    if not os.path.isdir(Path("./" + folderName)):
        try:
            os.mkdir(Path("./" + folderName))
        except:
            # This shoudln't ever be reached, as it would imply that the folder doesn't exist, but the script also is unable to create it. Could possibly be missing read permissions if the scripts catches this exception
            raise Exception("The folder needed for {} couldn't be created, exiting".format(purpose))

# Mozilla will have an api endpoint giving a lot of information about the latest releases for the geckodriver, from which the url for the linux 64 bit has to be extracted
def extractDriverURL():
    driverDetails = json.loads(requests.get("https://api.github.com/repos/mozilla/geckodriver/releases/latest").text)

    for platformRelease in driverDetails['assets']:
        if platformRelease['name'].endswith("linux64.tar.gz"):
            return platformRelease['browser_download_url']

# Downloading and extracting the .tar.gz file the geckodriver is stored in into the tools directory
def downloadDriver(driverURL):
    driverContents = requests.get(driverURL, stream=True)
    with tarfile.open(fileobj=driverContents.raw, mode='r|gz') as driverFile:
        driverFile.extractall(path=Path("./tools/"))

def main():

    printDebug("Downloading and extracting the geckodriver...")

    downloadDriver(extractDriverURL())

    printDebug("Creating the folders for storing the scraped articles and logs...")

    createFolder('articles', 'storing the markdown files representing the articles')
    createFolder('logs', 'storing the logs')

    printDebug("Creating the \"osinter\" postgresql database...")

    # Connecting to the database
    conn = psycopg2.connect("user=postgres password=" + postgresqlPassword)

    # Needed ass create database cannot be run within transaction
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

    # Creating a new database
    with conn.cursor() as cur:
        try:
            cur.execute("CREATE DATABASE osinter;")
            printDebug("Database created.")
        except psycopg2.errors.DuplicateDatabase:
            printDebug("Database already exists, skipping.")

    conn.close()

    # Connecting to the newly created database
    conn = psycopg2.connect("dbname=osinter user=postgres password=" + postgresqlPassword)

    printDebug("Creating the needed \"article\" table...")
    # Making sure the database has gotten the needed table(s)
    if OSINTdatabase.initiateArticleTable(conn):
        printDebug("The \"article\" table has been created.")
    else:
        printDebug("The \"article\" table already exists, skipping.")

if __name__ == "__main__":
    main()