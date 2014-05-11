#####################################################################################
##                                  INFORMATION
#####################################################################################
##
##  Developed by: Coty Sutherland
##
##  Last Updated: 5/11/2014
##
##  Description: Based on the idea by Steven Johnson, this application deletes
##       Video content that has been marked as a one start, allowing you to
##       automatically remove bad/old content from Plex easily.
##
##  Required Configurations:
##      - Host     (Hostname or IP  | Blank = 127.0.0.1)
##      - Port     (Port  |  Blank = 32400)
##      - Section  (Section aka Library 1 2 3 varies on your system  |  Blank = 1)
##      - Delete   (True = Delete  |  Blank = False (For Testing or Review))
##      - Shows    ( ["Show1","Show2"] keeps Show1 and Show2 OR [] to DEL ALL SHOWS )
##
#####################################################################################
#####################################################################################

import os
import re
import logging
from cleanup_plex.utils.settings import cleanup_plex_config, console


class RemoveUnwanted:

    # defaults
    ToBeDeleted = []

    # set counters
    FileCount = 0
    DeleteCount = 0
    FlaggedCount = 0
    OnDeckCount = 0
    ShowsCount = 0

    def __init__(self, Host="localhost", Port="32400", Section="1", Delete=False, Shows=[], DeleteDir=False):
        self.log = logging.getLogger(name='RemoveUnwanted')
        self.log.setLevel(cleanup_plex_config['logging_level'])
        self.log.addHandler(console)

        self.log.info("----------------------------------------------------------------------------")
        self.log.info("                         Script Starting                                    ")
        self.log.info("----------------------------------------------------------------------------")

        self.URL = ("http://" + Host + ":" + Port + "/library/sections/" + Section + "/recentlyViewed")
        self.Delete = Delete
        self.Shows = Shows
        self.DeleteDir = DeleteDir

        self.log.debug("Settings:")
        self.log.debug("Host: " + Host)
        self.log.debug("Port: " + Port)
        self.log.debug("Section: " + Section)
        self.log.debug("URL: " + self.URL)

        NoDelete = " | "
        ShowCount = len(self.Shows)

        self.log.debug("Show Count: " + str(ShowCount))

        for Show in self.Shows:
            Show = re.sub('[^A-Za-z0-9 ]+', '', Show).strip()
            if Show == "":
                NoDelete += "(None Listed) | "
                ShowCount -= 1
            else:
                NoDelete += Show + " | "

        self.log.debug("Number of Shows Detected For Keeping: " + str(ShowCount))
        self.log.debug("Shows to Keep:" + NoDelete)

        ###################################################################################
        ##  Checking Delete
        ####################################################################################
        if self.Delete:
            self.log.debug("Delete: ***Enabled***")
        else:
            self.log.debug("Delete: Disabled - Flagging Only")

    def start(self):
        self.iterateAndMatch()
        self.remove()
        self.printFooter()

    def iterateAndMatch(self):
        # make request to get the document
        import requests
        html_doc = requests.get(self.URL).text

        from BeautifulSoup import BeautifulSoup
        soup = BeautifulSoup(html_doc)

        for vid in soup.findAll('video'):
            # increment total file count
            self.FileCount += 1

            try:
                # check userRating to see if its a 1 star or not. 1 star = 2 pts.
                if int(vid['userrating']) == 2:
                    self.addToList(vid)
            except KeyError:
                # do nothing
                pass

    def addToList(self, vid):
        title = vid['title']
        filePath = vid.media.part['file']

        # using the filePath we can pull out the dirPath
        dirPath = re.sub('/[a-zA-Z0-9\s*]+\.[a-zA-Z]+$', '', filePath)

        if title in self.Shows:
            saveVideo = True
        else:
            saveVideo = False

        self.ToBeDeleted.append({'title': title, 'dir': dirPath, 'file': filePath, 'save': saveVideo})

    def remove(self):
        for video in self.ToBeDeleted:
            title = video['title']
            dir = video['dir']
            file = video['file']
            save = video['save']

            if self.DeleteDir:
                path = dir
            else:
                path = file

            if save:
                self.log.info("[KEEPING] [" + title + "] " + path)
                self.ShowsCount += 1
            else:
                if self.Delete:
                    self.log.info("**[DELETING] " + path)
                    if os.path.exists(path):
                        import shutil
                        try:
                            shutil.rmtree(path)
                            self.log.info("**[DELETED] " + path)
                            self.DeleteCount += 1
                        except:
                            self.log.error("There was a problem deleting " + path)
                    else:
                        self.log.info("##[NOT FOUND] " + path)
                else:
                    self.log.testing("**[FLAGGED] " + title)
                    self.FlaggedCount += 1

    def printFooter(self):
        self.log.info("")
        self.log.info("----------------------------------------------------------------------------")
        self.log.info("----------------------------------------------------------------------------")
        self.log.info("                Summary -- Script Completed Successfully                    ")
        self.log.info("----------------------------------------------------------------------------")
        self.log.info("")
        self.log.info("  Total File Count  " + str(self.FileCount))
        self.log.info("  Kept Show Files   " + str(self.ShowsCount))
        self.log.info("  Deleted Files     " + str(self.DeleteCount))
        self.log.info("  Flagged Files     " + str(self.FlaggedCount))
        self.log.info("")
        self.log.info("----------------------------------------------------------------------------")
        self.log.info("----------------------------------------------------------------------------")

if __name__ == '__main__':
    test = RemoveUnwanted()
    test.start()

