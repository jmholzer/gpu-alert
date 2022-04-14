import os


def generate_absolute_path(relative_path: str) -> str:
    """
    Generate an absolute path to a file.

    Arguments:
    relative_path -- path relative to current script.
    """
    path_to_script = os.path.dirname(os.path.abspath(__file__))
    return path_to_script + "/" + relative_path
