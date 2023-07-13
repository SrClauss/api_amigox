import os
import sys


def define_sys_path():
    """
    Define the system path.

    This function is responsible for defining the system path. It gets the directory of the current file and the parent directory of the current file using the `os.path` module. Then, it inserts the parent directory at the beginning of the system path using the `sys.path.insert()` function.

    Parameters:
        None

    Returns:
        None
    """

 
    current_file_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_file_dir)
    sys.path.insert(0, parent_dir)
