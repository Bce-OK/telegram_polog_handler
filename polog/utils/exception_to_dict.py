def exception_to_dict(args_dict, exc):
    args_dict['exception'] = str(exc)
    args_dict['exception_type'] = type(exc).__name__