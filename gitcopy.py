import requests
from bs4 import BeautifulSoup
import os
import re
import sys
import argparse
import subprocess


class GitCopier:

    _git_dir = ""
    _local_dir = ""
    files_folders = []

    def _checkUrl(self, url):
        '''Validate URL is valid
        '''
        if re.compile('^(?:http(s)?:\/\/)?[\w.-]+(?:\.[\w\.-]+)+[\w\-\._~:/?#[\]@!\$&\'\(\)\*\+,;=.]+$').match(url):
            return True
        else:
            return False

    def _checkForForwardSlash(self, url):
        '''Check if the URL contains a backslash at the end
        '''
        if re.compile('^.*\/$').match(url):
            return True
        else:
            return False

    def _checkForValidLocalWinDirectory(self, dir):
        '''Checks string for windows style directory listing. Ex C:\MyFolder, D:\MyFolder, etc
        '''
        if re.compile('^[\w]:[\\\](.*)[\\\]$').match(dir):
            return True
        else:
            return False

    def _checkForValidLocalUnixDirectory(self, dir):
        '''Checks string for double backslash
        '''
        if re.compile('^[\/\/].*').match(dir):
            return True
        else:
            return False
            
    def _checkForGitInstallation(self):
        '''Checks for a git installation by running "git --version" in commnd line. If this fails, then the user will need to install git and ensure it is runnable via command line
        '''
        try:
            completed_process = subprocess.run(["git", "--version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
            completed_process.check_returncode()
            return True
        except subprocess.CalledProcessError as cpe:
            print(cpe)
            return False
        except FileNotFoundError:
            raise FileNotFoundError("git installation not found")
            
    def _runGitResetHard(self):
        '''Runs command "git reset --hard" using subprocess to reverse the git repo back to actual files
        '''
        try:
            completed_process = subprocess.run(["git", "reset", "--hard"], check=True, cwd=self._local_dir.replace(".git\\", ""), stderr=subprocess.STDOUT)
            completed_process.check_returncode()
            return True
        except subprocess.CalledProcessError as cpe:
            print(cpe)
            return False
        except FileNotFoundError:
            raise FileNotFoundError("git installation not found")
        

    def __init__(self, git, local):
        """
        :param git:
        Ex: https://www.example.com/.git
        :param base:
        https://www.example.com/
        :param local:
        Ex: C:\\Users\\MyUser\\Documents\\NewGitDir\\
        """
        if self._checkForForwardSlash(git) and self._checkUrl(git):
            self._git_dir = git
            print(self._git_dir)
        elif self._checkForForwardSlash(git + "/") and self._checkUrl(git + "/"):
            self._git_dir = git + "/"
            print(self._git_dir)
        else:
            raise Exception("Directory {0} not valid. Did you forget a trailing forward slash? \n"
                            "Ex: https://www.exmaple.com/.git/".format(git))

        if self._checkForValidLocalWinDirectory(local) or self._checkForValidLocalUnixDirectory(local):
            self._local_dir = local + ".git\\"
        elif self._checkForValidLocalWinDirectory(local + "\\"):
            self._local_dir = local + "\\.git\\"
        else:
            raise Exception("Directory {0} not valid. Did you forget a trailing back slash? \n"
                            "Ex: //etc/var/log or C:\\TestDir\\".format(local))

        self.files_folders = self.get_dir_listing(self._git_dir)

    def write_file(self, file_list):
        '''Save files to the file system
        '''
        print("Copying files to filesystem...")
        for file in file_list:
            response = requests.get(self._git_dir + "/" + file)
            print("File " + file + " created")
            open(self._local_dir + file, "wb").write(response.content)

    def make_dir(self, dir_names):
        print("Making directories on filesystem...")
        for directory in dir_names:
            os.makedirs(self._local_dir + directory)
            print("Directory " + directory + " created")

    def sanitize_directories(self, dir_names):
        sanitized_names = []
        for i in dir_names:
            sanitized_names.append(i.replace(self._git_dir,""))
        return sanitized_names

    def get_all_hyperlinks_from_table(self, response):
        '''Scrape hyperlinks from page and trying to avoid non-git related links
        '''
        # Added blacklist due to older versions of Apache making it harder to parse links correctly
        blacklist = ["name","last modified", "size", "description"]
        parentTag = ["td", "li", "pre"] # Different Apaches version list links in <td> or <pre> tag. Nginx uses <li> tag. Might need more eventually idk
        soup = BeautifulSoup(response.text, "html.parser")
        return [str(tag["href"]) for tag in soup.find_all(name="a")
                if (tag.parent.name in parentTag) # Check parent tag to drill down to correct link
                and len(tag["href"]) > 1 # To avoid dead links such as the dreadful # sign
                and (tag.text.lower() not in blacklist) # Older versions of apache need blacklist
                and tag.text.strip() != "Parent Directory"]

    def check_for_directory(self, path):
        '''Check if the followed hyperlink is a folder. I found that folders do not return a content-type.
        '''
        response = requests.get(path)
        try:
            # Need to check for non-200 HTTP statuses to avoid hitting dead links
            if response.status_code != 200:
                return response.status_code

            # Apache and Nginx servers don't have content-type header for files (obviously)
            # Both servers return text/html in content-type for directories
            if (response.headers["content-type"] is not None) and (response.headers["content-type"] != "text/plain"):
                return True
            else:
                return False
        except:
            return False

    def get_dir_listing(self, remote):
        """
        Recursive function that returns a tuple of lists
        First list is of directory links
        Second list of file links

        Directory vs File is determined by the presence of a content-type header
        """
        response = requests.get(remote)

        directories = []
        file_list = []
        hyperlinks = self.get_all_hyperlinks_from_table(response)

        for ff in hyperlinks:
            dirBool = self.check_for_directory(remote + ff)
            if dirBool is True:
                directories.append(remote + ff)
                print(remote + ff)
                recursive_output = self.get_dir_listing(remote + ff) # Recursively check for more directories
                directories = directories + recursive_output[0]
                file_list = file_list + recursive_output[1]
            elif dirBool != False:
                print('Status code {0} returned'.format(dirBool))
            else:
                file_list.append(remote + ff)
                print(remote + ff)
        return directories, file_list
        
    def rebuild_source(self):
        '''Check for a git install and then run "git reset --hard" rebuild the git repo back into source code
        '''
        self._checkForGitInstallation()
        self._runGitResetHard()        


def run(remote, local):
    print("Indexing .git folder... ")
    print("This will take several minutes")
    # Recursively build directory structure and file paths
    GDC = GitCopier(remote, local)

    # Takes list of directories and creates on filesystem
    GDC.make_dir(GDC.sanitize_directories(GDC.files_folders[0]))

    # Takes files from memory and writes to filesystem
    GDC.write_file(GDC.sanitize_directories(GDC.files_folders[1]))
    
    # After the .git files/objects are written to the file system, and installed git client is used to rebuild the source code files
    GDC.rebuild_source()

if __name__=="__main__":
    sys.argv.pop(0)
    parser = argparse.ArgumentParser(description='Pull .git repo from web server using directory listing')
    parser.add_argument('-r', action="store", dest="remote", help='Remote URL of .git folder. Ex: https://www.example.com/.git/')
    parser.add_argument('-l', action="store", dest="local", help='Local directory to store .git folder')
    args = parser.parse_args(sys.argv)
    run(args.remote, args.local)

'''
TODO:
1. Optimizations such as multithreading since there is a lot of waiting on requests I/O
2. More testing for stability. Lots of webservers still don't work properly and produce weird errors
    -Find a better way to parse links for directory/files. Maybe just use wget to recursively clone the directories instead of requests and beautifulsoup4. But for real though, where's the fun in that?
3. Swap out the subprocess module for the actual gitPython module to be cool 😎
'''