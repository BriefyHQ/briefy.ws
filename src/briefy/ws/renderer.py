"""Custom JSONRenderer."""
from briefy.common.utils.transformers import to_serializable
from pyramid.interfaces import IJSONAdapter
from pyramid.renderers import JSON
from pyramid.request import Request
from zope.interface import providedBy

import typing as t


_marker = object()


class JSONRenderer(JSON):
    """JSON renderer that inject to_serializable as default for json or simplejson dumps call."""

    def _make_default(self, request: Request):
        """Make default function is not used anymore, just here to explicit it."""
        def default(obj):
            if hasattr(obj, '__json__'):
                return obj.__json__(request)
            obj_iface = providedBy(obj)
            adapters = self.components.adapters
            result = adapters.lookup((obj_iface,), IJSONAdapter, default=_marker)
            if result is _marker:
                obj_repr = repr(obj)
                raise TypeError(f'{obj_repr} is not JSON serializable')
            return result(obj, request)
        return default

    def __call__(self, info) -> t.Callable:
        """Return a plain JSON-encoded string with content-type ``application/json``.

        The content-type may be overridden by setting ``request.response.content_type``.
        """
        def _render(value, system):
            request = system.get('request')
            if request is not None:
                response = request.response
                ct = response.content_type
                if ct == response.default_content_type:
                    response.content_type = 'application/json'
            # do not use _make_default, just pass to_serializable
            return self.serializer(value, default=to_serializable, **self.kw)

        return _render
