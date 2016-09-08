from pyramid.renderers import JSONP
from pyramid.renderers import JSONP_VALID_CALLBACK
from briefy.common.utils.transformers import to_serializable
from pyramid.interfaces import IJSONAdapter
from zope.interface import providedBy


from pyramid.httpexceptions import HTTPBadRequest


_marker = object()


class JSONRenderer(JSONP):

    def _make_default(self, request):
        def default(obj):
            if hasattr(obj, '__json__'):
                return obj.__json__(request)
            obj_iface = providedBy(obj)
            adapters = self.components.adapters
            result = adapters.lookup((obj_iface,), IJSONAdapter,
                                     default=_marker)
            if result is _marker:
                raise TypeError('%r is not JSON serializable' % (obj,))
            return result(obj, request)
        return default

    def __call__(self, info):
        """ Returns JSONP-encoded string with content-type
        ``application/javascript`` if query parameter matching
        ``self.param_name`` is present in request.GET; otherwise returns
        plain-JSON encoded string with content-type ``application/json``"""

        def _render(value, system):
            request = system.get('request')
            # default = self._make_default(request)
            val = self.serializer(value, default=to_serializable, **self.kw)
            ct = 'application/json'
            body = val
            if request is not None:
                callback = request.GET.get(self.param_name)

                if callback is not None:
                    if not JSONP_VALID_CALLBACK.match(callback):
                        raise HTTPBadRequest('Invalid JSONP callback function name.')

                    ct = 'application/javascript'
                    body = '/**/{0}({1});'.format(callback, val)
                response = request.response
                if response.content_type == response.default_content_type:
                    response.content_type = ct
            return body

        return _render

renderer_utility = JSONRenderer('json')
