def object_tool(function=None, *, icon=None, name=None, description=None, http_method='get', post_param_title=None):
    """
    :http_method get | post. if http method is post, button will be place in submit row
    :post_param_title Only affect if http method is post. Use when you want sumit form with one param.
    """

    def decorator(func):
        func.icon = icon
        func.name = name
        func.description = description
        func.http_method = http_method
        func.post_param_title = post_param_title

        return func

    if function is None:
        return decorator
    return decorator(function)
