#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan  1 00:17:27 2025

@author: vibhor
"""

import inspect
import os

def get_current_file_path():
    """Returns the absolute path of the calling file."""
    frame = inspect.stack()[1]
    module = inspect.getmodule(frame[0])
    if module:
        return os.path.abspath(module.__file__)
    return None

def print_file_path():
    """Prints the absolute file path."""
    file_path = get_current_file_path()
    if file_path:
        print(f"The absolute path of the file is: {file_path}")
    else:
        print("The file path could not be determined (likely running in a notebook).")


print(print_file_path())

# import json
# import urllib.request
# from jupyter_server import serverapp

# def get_notebook_path():
#     """Finds the path of the currently running Jupyter Notebook."""
#     # Get all running Jupyter servers
#     servers = list(serverapp.list_running_servers())
#     for server in servers:
#         try:
#             sessions_url = server['url'] + 'api/sessions'
#             with urllib.request.urlopen(sessions_url) as response:
#                 sessions = json.load(response)
#                 for session in sessions:
#                     if session['kernel']['id'] == os.environ['JPY_PARENT_PID']:  # Match by environment variable (this approach links to the Jupyter kernel process)
#                         relative_path = session['notebook']['path']
#                         return os.path.join(server['notebook_dir'], relative_path)
#         except Exception as e:
#             print(f"Could not connect to Jupyter server: {e}")
#     return None

# # Get the notebook's path
# notebook_path = get_notebook_path()
# if notebook_path:
#     print(f"The notebook's absolute path is: {notebook_path}")
# else:
#     print("Unable to determine notebook path.")


