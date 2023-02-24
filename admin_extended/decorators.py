def object_tool(function=None, *, icon=None, name=None, description=None):
    def decorator(func):
        func.icon = icon
        func.name = name
        func.description = description

        return func
    
    if function is None:
        return decorator
    return decorator(function)
