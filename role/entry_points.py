import os
import sys
deps_path = os.path.join(os.path.dirname(__file__), "deps")
sys.path.insert(1, deps_path)


from .application import RoleApplication


def main():
    RoleApplication().run()
