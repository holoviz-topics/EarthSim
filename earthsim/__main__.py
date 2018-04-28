import sys

def main(args=None):
    try:
        import pvutil.cmd
    except ImportError:
        from . import _missing_cmd
        print(_missing_cmd())
        sys.exit(1)
    return pvutil.cmd.substitute_main('earthsim',args=args)

if __name__ == "__main__":
    main()
