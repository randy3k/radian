from .runtime import Rinstance
from .repl import create_r_repl
from . import interface
from . import api


class RoleApplication(object):

    def run(self):
        rinstance = Rinstance()

        # to make api work
        api.rinstance = rinstance

        # show warnings as they appear
        interface.reval("options(warn=1)")

        application = create_r_repl()
        application.run()
