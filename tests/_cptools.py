
class Tool(object):
    """A registered function for use with CherryPy request-processing hooks.

    help(tool.callable) should give you more information about this Tool.
    """

    namespace = "tools"

    def __init__(self, point, callable, name=None, priority=50):
        self._point = point
        self.callable = callable
        self._name = name
        self._priority = priority
        self.__doc__ = self.callable.__doc__

    def _get_on(self):
        raise AttributeError(_attr_error)
    def _set_on(self, value):
        raise AttributeError(_attr_error)
    on = property(_get_on, _set_on)

    def _setargs(self):
        pass

    def _merged_args(self, d=None):
        """Return a dict of configuration entries for this Tool."""
        if d:
            conf = d.copy()
        else:
            conf = {}

        tm = cherrypy.serving.request.toolmaps[self.namespace]
        if self._name in tm:
            conf.update(tm[self._name])

        if "on" in conf:
            del conf["on"]

        return conf

    def __call__(self, *args, **kwargs):
        """Compile-time decorator (turn on the tool in config).

        For example::

            @tools.proxy()
            def whats_my_base(self):
                return cherrypy.request.base
            whats_my_base.exposed = True
        """
        if args:
            raise TypeError("The %r Tool does not accept positional "
                            "arguments; you must use keyword arguments."
                            % self._name)
        def tool_decorator(f):
            if not hasattr(f, "_cp_config"):
                f._cp_config = {}
            subspace = self.namespace + "." + self._name + "."
            f._cp_config[subspace + "on"] = True
            for k, v in kwargs.items():
                f._cp_config[subspace + k] = v
            return f
        return tool_decorator

    def _setup(self):
        """Hook this tool into cherrypy.request.

        The standard CherryPy request object will automatically call this
        method when the tool is "turned on" in config.
        """
        conf = self._merged_args()
        p = conf.pop("priority", None)
        if p is None:
            p = getattr(self.callable, "priority", self._priority)
        cherrypy.serving.request.hooks.attach(self._point, self.callable,
                                              priority=p, **conf)


class HandlerTool(Tool):
    """Tool which is called 'before main', that may skip normal handlers.

    If the tool successfully handles the request (by setting response.body),
    if should return True. This will cause CherryPy to skip any 'normal' page
    handler. If the tool did not handle the request, it should return False
    to tell CherryPy to continue on and call the normal page handler. If the
    tool is declared AS a page handler (see the 'handler' method), returning
    False will raise NotFound.
    """

    def __init__(self, callable, name=None):
        Tool.__init__(self, 'before_handler', callable, name)

    def handler(self, *args, **kwargs):
        """Use this tool as a CherryPy page handler.

        For example::

            class Root:
                nav = tools.staticdir.handler(section="/nav", dir="nav",
                                              root=absDir)
        """
        def handle_func(*a, **kw):
            handled = self.callable(*args, **self._merged_args(kwargs))
            if not handled:
                raise cherrypy.NotFound()
            return cherrypy.serving.response.body
        handle_func.exposed = True
        return handle_func

    def _wrapper(self, **kwargs):
        if self.callable(**kwargs):
            cherrypy.serving.request.handler = None

    def _setup(self):
        """Hook this tool into cherrypy.request.

        The standard CherryPy request object will automatically call this
        method when the tool is "turned on" in config.
        """
        conf = self._merged_args()
        p = conf.pop("priority", None)
        if p is None:
            p = getattr(self.callable, "priority", self._priority)
        cherrypy.serving.request.hooks.attach(self._point, self._wrapper,
                                              priority=p, **conf)

class SessionAuthTool(HandlerTool):

    def _setargs(self):
        pass


_session_auth = SessionAuthTool(lambda x:x)
