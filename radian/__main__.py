import sys

# this file is used when radian is called with `python -m radian`

if __name__ == '__main__':
    if not any(a in ("-v", "--version", "-h", "--help") for a in sys.argv[1:]):
        from rchitect.utils import maybe_reexec

        maybe_reexec(module="radian")

    if "--coverage" in sys.argv:
        import coverage
        cov = coverage.Coverage()
        cov.start()

        def cleanup(x):
            cov.stop()
            cov.save()

    elif "--cprofile" in sys.argv:
        import cProfile
        import pstats
        pr = cProfile.Profile()
        pr.enable()

        def cleanup(x):
            pr.disable()
            ps = pstats.Stats(pr).sort_stats('cumulative')
            ps.print_stats(10)

    else:
        cleanup = None

    from radian import main

    main(cleanup=cleanup)

