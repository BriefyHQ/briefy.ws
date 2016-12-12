"""Loadbalancer heartbeat view.

ref: https://github.com/mozilla-services/cliquet/blob/master/cliquet/views/heartbeat.py
"""
from pyramid.request import Request
from pyramid.security import NO_PERMISSION_REQUIRED

from cornice import Service

lbheartbeat = Service(
    name="lbheartbeat",
    path='/__lbheartbeat__',
    description="Web head health"
)


@lbheartbeat.get(permission=NO_PERMISSION_REQUIRED)
def get_lbheartbeat(request: Request) -> dict:
    """Return successful healthy response.

    If the load-balancer tries to access this URL and fails, this means the
    Web head is not operational and should be dropped.
    """
    status = {}
    return status
