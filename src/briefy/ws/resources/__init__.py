"""Webservice resources."""
from briefy.ws.resources.base import BaseResource  # noQA
from briefy.ws.resources.workflow import WorkflowAwareResource  # noQA
from briefy.ws.resources.history import HistoryService  # noQA
from briefy.ws.resources.sqlquery import SQLQueryService  # noQA
from briefy.ws.resources.resource import RESTService  # noQA
from briefy.ws.resources.versions import VersionsService  # noQA
