"""Versions service."""
from briefy.ws.resources import BaseResource
from cornice.resource import view
from pyramid.httpexceptions import HTTPNotFound as NotFound


class VersionsService(BaseResource):
    """Versions service for SQLAlchemy Continuum models."""

    model = None
    """This must be provided by subclass."""

    @property
    def friendly_name(self) -> str:
        """Return friendly name from the model class."""
        return self.model.__name__

    @view(validators='_run_validators')
    def collection_get(self) -> dict:
        """Return the payload with list of versions for this object."""
        id_ = self.request.matchdict.get('id', '')
        obj = self.get_one(id_)
        raw_versions = obj.versions
        versions = []
        for version_id, version in enumerate(raw_versions):
            versions.append({'id': version_id, 'updated_at': version.updated_at})

        return {'versions': versions, 'total': obj.version + 1}

    @view(validators='_run_validators')
    def get(self) -> dict:
        """Return a version for this object."""
        id_ = self.request.matchdict.get('id', '')
        obj = self.get_one(id_)
        version_id = self.request.matchdict.get('version_id', 0)
        try:
            version_id = int(version_id)
            version = obj.versions[version_id]
        except (ValueError, IndexError):
            raise NotFound(f'{self.friendly_name} with version: {version_id} not found.')

        data = version.to_dict()
        add_metadata_attrs = ('_title', '_slug', '_description')
        for attr_name in add_metadata_attrs:
            if hasattr(version, attr_name):
                value = data.pop(attr_name, None)
                if not value:
                    value = getattr(version, attr_name)
                data[attr_name[1:]] = value

        return data
