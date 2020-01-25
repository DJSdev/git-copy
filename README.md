# git-copy

A utility to copy "Index of /.git" directories from webservers over HTTP/S. After the .git objects are downloaded, the git cli is run to reverse the git repo back into source code.

There are cleaner ways to mirror .git directories from web servers. For example, *wget* utility would give you much cleaner and reliable results. While this technically can be used for copying *any* files out of directory listings, the sole intention was to do .git directories.

This requires that the git cli client be installed. If you can run "git --version" and the terminal/cmd window doesn't complain, you should be good. If not try adding the git installation folder to your environment variables/PATH.

Install instructions instructions:
`pip install requirements.txt`

Run instructions:
`python gitcopy.py -r https://mywebsite.com/.git -l C:\Users\Me\Documents\Repo`

Libraries used:

	asn1crypto==0.24.0
	beautifulsoup4==4.8.2
	brotlipy==0.7.0
	bs4==0.0.1
	certifi==2019.11.28
	cffi==1.12.3
	chardet==3.0.4
	cryptography==2.7
	gitdb2==2.0.6
	GitPython==3.0.5
	idna==2.8
	pycparser==2.19
	pywin32==224
	requests==2.22.0
	six==1.12.0
	smmap2==2.0.5
	soupsieve==1.9.5
	urllib3==1.25.7

Only a few supported web servers:
- Apache (some older versions too)
- Nginx
- Unsupproted webserver may produce strange results

Still some TODOs:
1. Optimizations such as multithreading since there is a lot of waiting on requests I/O
2. More testing for stability. Lots of webservers still don't work properly and produce weird errors
    -Find a better way to parse links for directory/files. Maybe just use wget to recursively clone the directories instead of requests and beautifulsoup4. But for real though, where's the fun in that?
3. Swap out the subprocess module for the actual gitPython module would be cool 😎
