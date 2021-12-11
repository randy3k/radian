from radian import main
import sys

# this file is used when radian is called with `python -m radian`

if __name__ == '__main__':

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

    main(cleanup=cleanup)
