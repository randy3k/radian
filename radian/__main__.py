import optparse
import os
import sys

from packaging.version import parse as parse_version
from rchitect.utils import get_rhome, maybe_reexec, rversion

from radian import __version__


def parse_args(argv=None):
    parser = optparse.OptionParser("usage: radian")
    parser.add_option(
        "-v", "--version", action="store_true", dest="version", help="Get version"
    )
    parser.add_option("--r-binary", dest="r", help="Path to R binary")
    parser.add_option(
        "--profile",
        dest="profile",
        help="Path to .radian_profile, ignore both global and local profiles",
    )
    parser.add_option(
        "-q",
        "--quiet",
        "--silent",
        action="store_true",
        dest="quiet",
        help="Don't print startup message",
    )
    parser.add_option(
        "--no-environ",
        action="store_true",
        dest="no_environ",
        help="Don't read the site and user environment files",
    )
    parser.add_option(
        "--no-site-file",
        action="store_true",
        dest="no_site_file",
        help="Don't read the site-wide Rprofile",
    )
    parser.add_option(
        "--no-init-file",
        action="store_true",
        dest="no_init_file",
        help="Don't read the user R profile",
    )
    parser.add_option(
        "--local-history",
        action="store_true",
        dest="local_history",
        help="Force using local history file",
    )
    parser.add_option(
        "--global-history",
        action="store_true",
        dest="global_history",
        help="Force using global history file",
    )
    parser.add_option(
        "--no-history",
        action="store_true",
        dest="no_history",
        help="Don't load any history files",
    )
    parser.add_option(
        "--vanilla",
        action="store_true",
        dest="vanilla",
        help="Combine --no-history --no-environ --no-site-file --no-init-file",
    )
    parser.add_option(
        "--save",
        action="store_true",
        dest="save",
        help="Do save workspace at the end of the session",
    )
    parser.add_option(
        "--ask-save", action="store_true", dest="ask_save", help="Ask to save R data"
    )
    parser.add_option(
        "--restore-data",
        action="store_true",
        dest="restore_data",
        help="Restore previously saved objects",
    )
    parser.add_option("--debug", action="store_true", dest="debug", help="Debug mode")
    parser.add_option(
        "--coverage", action="store_true", dest="coverage", help=optparse.SUPPRESS_HELP
    )
    parser.add_option(
        "--cprofile", action="store_true", dest="cprofile", help=optparse.SUPPRESS_HELP
    )

    # we accept these options, but never check them
    parser.add_option(
        "--no-save", action="store_true", dest="no_save", help=optparse.SUPPRESS_HELP
    )
    parser.add_option(
        "--no-restore-data",
        action="store_true",
        dest="no_restore_data",
        help=optparse.SUPPRESS_HELP,
    )
    parser.add_option(
        "--no-restore-history",
        action="store_true",
        dest="no_restore_history",
        help=optparse.SUPPRESS_HELP,
    )
    parser.add_option(
        "--no-restore",
        action="store_true",
        dest="no_restore",
        help=optparse.SUPPRESS_HELP,
    )
    parser.add_option(
        "--no-readline",
        action="store_true",
        dest="no_readline",
        help=optparse.SUPPRESS_HELP,
    )
    parser.add_option(
        "--interactive",
        action="store_true",
        dest="interactive",
        help=optparse.SUPPRESS_HELP,
    )

    return parser.parse_args(argv)


def _print_version(r_home):
    if r_home:
        r_binary = os.path.normpath(os.path.join(r_home, "bin", "R"))
        r_version = rversion(r_home)
    else:
        r_binary = "NA"
        r_version = "NA"
    print("radian version: {}".format(__version__))
    print("r executable: {}".format(r_binary))
    print("r version: {}".format(r_version))
    print("python executable: {}".format(sys.executable))
    print(
        "python version: {:d}.{:d}.{:d}".format(
            sys.version_info.major, sys.version_info.minor, sys.version_info.micro
        )
    )


def _setup_profiler(options):
    if options.coverage:
        import coverage

        cov = coverage.Coverage()
        cov.start()

        def cleanup(x):
            cov.stop()
            cov.save()

        return cleanup

    if options.cprofile:
        import cProfile
        import pstats

        pr = cProfile.Profile()
        pr.enable()

        def cleanup(x):
            pr.disable()
            ps = pstats.Stats(pr).sort_stats("cumulative")
            ps.print_stats(10)

        return cleanup

    return None


def main(cleanup=None):
    options, _ = parse_args()

    if options.r:
        os.environ["R_BINARY"] = options.r

    if not options.version:
        maybe_reexec(module="radian")

    r_home = get_rhome()

    if options.version:
        _print_version(r_home)
        return

    if not r_home:
        raise RuntimeError("Cannot find R binary. Expose it via the `PATH` variable.")

    if rversion(r_home) < parse_version("4.2.0"):
        raise RuntimeError("R >= 4.2.0 is required.")

    if cleanup is None:
        cleanup = _setup_profiler(options)

    os.environ["RADIAN_VERSION"] = __version__
    os.environ["RADIAN_COMMAND_ARGS"] = " ".join(
        ["--" + k.replace("_", "-") for k, v in options.__dict__.items() if v]
    )

    from .app import RadianApplication

    RadianApplication(r_home, ver=__version__).run(options, cleanup=cleanup)


if __name__ == "__main__":
    main()
