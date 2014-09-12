#!/usr/bin/env python3

from pprint import pprint
from robobrowser import RoboBrowser
import os, os.path
import re
import time
import shutil
from zipfile import ZipFile, BadZipFile

# list of regexes for matching urls
file_types = [
        ".pdf$",
        ".zip$",
]

# list of tuples (url, target_dir)
# page at url is fetched and all matching references are downloaded into
# target_dir
source_list = [
        ("https://www.kth.se/social/course/IL2206/subgroup/ht-2014-50315/page/lectures-67/",
                "lectures"),
        ("https://www.kth.se/social/course/IL2206/subgroup/ht-2014-50315/page/lectures-67://www.kth.se/social/course/IL2206/subgroup/ht-2014-50315/page/tutorials-21/",
                "tutorials"),
        ("https://www.kth.se/social/course/IL2206/subgroup/ht-2014-50315/page/laboratories-5/",
                "labs"),
        ("https://www.kth.se/social/course/IL2206/page/exercise-collection-2/",
                "exc"),
]

def credentials():
        """
        Provide credentials for logging into kth.se
        returns tuple(name, password)
        """
        name = input("name?:")
        pw = input("pw?:")
        return (name, pw)

def do_login(browser, credential_provider=credentials):
        """
        Perform a login to kth.se in the given browser session

        :param credential_provider: function that returns a tuple of (name,
                                    password) for logging in
        """
        r = browser

        r.open("https://login.kth.se")
        f = r.get_form()
        name, pw = credential_provider()
        f["username"] = name
        f["password"] = pw
        r.submit_form(f)
        if r.find("h2", text=re.compile(".*Försök igen.*")) is not None:
                raise ValueError("Wrong username or Password!")

def headers_for_file(url, path):
        try:
                t = os.path.getmtime(path)
                ts = time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(t))
                return {"if-modified-since": ts}
        except OSError as e:
                return {}

def extract_zip(path):
        zipdir = path[:-len(".zip")]

        # clean up
        shutil.rmtree(zipdir, ignore_errors=True)
        os.makedirs(zipdir, exist_ok=True)

        # extract all
        try:
                with ZipFile(path) as z:
                        z.extractall(zipdir)
        except BadZipFile as e:
                print("ERROR: Could not extract ", path)
                print("ERROR:", e)


def retrieve_links(browser, links, target_dir):
        """
        Downloads the given links into target_dir

        :param links: list of <a href="..."> tag-objects
        :param target_dir: path to local storage
        """
        r = browser
        for a in links:
                url = a["href"]
                path = os.path.join(target_dir, os.path.basename(url))

                headers = headers_for_file(url, path)
                r.follow_link(a, headers=headers)

                if r.response.status_code == 304: # "HTTP: Not Modified"
                        print("up to date: ",url)
                else:
                        print("downloaded: ",url)
                        try:
                                os.remove(path)
                        except OSError as e:
                                pass # no such file

                        with open(path, "wb") as f:
                                f.write(r.response.content)
                        if path.endswith(".zip"):
                                extract_zip(path)
                r.back()

def get_files(browser, pages, types):
        """
        downloads all files of "types" that are found on "pages"

        :param pages: list of tuples (url, target_dir)
        :param types: list of regex-strings to match file urls on all pages
        """
        r = browser
        for page,target_dir in pages:
                os.makedirs(target_dir, exist_ok=True)
                r.open(page)
                links = []
                for t in types:
                        links += browser.get_links(href=re.compile(t))
                retrieve_links(browser, links, target_dir)

def main(*args):
        r = RoboBrowser()
        do_login(r, credentials)
        get_files(r, source_list, file_types)

if __name__=='__main__':
        import sys
        main(*sys.argv)
