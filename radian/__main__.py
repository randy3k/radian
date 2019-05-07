from radian import main
import sys

if __name__ == '__main__':
    if "--coverage" in sys.argv:
        import coverage
        cov = coverage.Coverage()
        cov.start()

        def cleanup(x):
            cov.stop()
            cov.save()
    else:
        cleanup = None

    try:
        main(cleanup)
    finally:
        if cleanup:
            cleanup(None)
