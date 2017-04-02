from .runtime import Rinstance
from .prompt import create_r_repl_application, create_r_command_line_interface


def main():
    runtime = Rinstance()
    runtime.run()
    cli = create_r_command_line_interface()
    cli.run()
