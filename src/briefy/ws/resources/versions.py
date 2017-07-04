"""Versions service."""
from briefy.ws.resources import BaseResource
from cornice.resource import view
from pyramid.httpexceptions import HTTPNotFound as NotFound


class VersionsService(BaseResource):
    """Versions service for continuum models."""

    model = None
    """This must be provided by subclass."""

    @property
    def friendly_name(self):
        """Return friendly name from the model class."""
        return self.model.__name__

    @view(validators='_run_validators')
    def collection_get(self):
        """Return the list of versions for this object."""
        id_ = self.request.matchdict.get('id', '')
        obj = self.get_one(id_)
        raw_versions = obj.versions
        versions = []
        for version_id, version in enumerate(raw_versions):
            versions.append(
                {
                    'id': version_id,
                    'updated_at': version.updated_at
                }
            )
        response = {
            'versions': versions,
            'total': obj.version + 1
        }
        return response

    @view(validators='_run_validators')
    def get(self):
        """Return a version for this object."""
        id_ = self.request.matchdict.get('id', '')
        obj = self.get_one(id_)
        version_id = self.request.matchdict.get('version_id', 0)
        try:
            version_id = int(version_id)
            version = obj.versions[version_id]
        except (ValueError, IndexError):
            raise NotFound(
                '{friendly_name} with version: {id} not found.'.format(
                    friendly_name=self.friendly_name,
                    id=version_id
                )
            )
        return version.__class__.to_dict(obj)
