"""Data utilities for Briefy webservices."""
from colanderalchemy import SQLAlchemySchemaNode
from sqlalchemy.orm.properties import ColumnProperty

import ast
import colander


class BriefySchemaNode(SQLAlchemySchemaNode):
    """Colander schema validation for SQLAlchemy."""

    def _get_node(self, prop: ColumnProperty, overrides: dict, schema_method: str):
        """Get node wrapper that change node name when start with underscore.

        This is necessary to use the descriptor as getter and setter.
        """
        column_name = prop.key
        node_name = column_name[1:] if column_name.startswith('_') else column_name
        excludes = self.excludes
        to_exclude = column_name in excludes or node_name in excludes
        if to_exclude:
            return None
        parent_method = getattr(super(), schema_method)
        node = parent_method(prop, overrides)
        node.name = node_name
        return node

    def get_schema_from_column(self, prop: ColumnProperty, overrides: dict) -> colander.SchemaNode:
        """Build and return a :class:`colander.SchemaNode` for a given Column.

        This method uses information stored in the column within the ``info``
        that was passed to the Column on creation.  This means that
        ``Colander`` options can be specified declaratively in
        ``SQLAlchemy`` models using the ``info`` argument that you can
        pass to :class:`sqlalchemy.Column`.

        Arguments/Keywords

        prop
            A given :class:`sqlalchemy.orm.properties.ColumnProperty`
            instance that represents the column being mapped.
        overrides
            A dict-like structure that consists of schema attributes to
            override imperatively. Values provides as part of :attr:`overrides`
            will take precedence over all others.
        """
        return self._get_node(prop, overrides, 'get_schema_from_column')

    def get_schema_from_relationship(self, prop, overrides):
        """Build and return a :class:`colander.SchemaNode` for a relationship.

        The mapping process will translate one-to-many and many-to-many
        relationships from SQLAlchemy into a ``Sequence`` of ``Mapping`` nodes
        in Colander, and translate one-to-one and many-to-one relationships
        into a ``Mapping`` node in Colander.  The related class involved in the
        relationship will be recursively mapped by ColanderAlchemy as part of
        this process, following the same mapping process.

        This method uses information stored in the relationship within
        the ``info`` that was passed to the relationship on creation.
        This means that ``Colander`` options can be specified
        declaratively in ``SQLAlchemy`` models using the ``info``
        argument that you can pass to
        :meth:`sqlalchemy.orm.relationship`.

        For all relationships, the settings will only be applied to the outer
        Sequence or Mapping. To customise the inner schema node, create the
        attribute ``__colanderalchemy_config__`` on the related model with a
        dict-like structure corresponding to the Colander options that should
        be customised.

        Arguments/Keywords

        prop
            A given :class:`sqlalchemy.orm.properties.RelationshipProperty`
            instance that represents the relationship being mapped.
        overrides
            A dict-like structure that consists of schema attributes to
            override imperatively. Values provides as part of :attr:`overrides`
            will take precendence over all others.  Example keys include
            ``children``, ``includes``, ``excludes``, ``overrides``.
        """
        return self._get_node(prop, overrides, 'get_schema_from_relationship')


class NullSchema(colander.MappingSchema):
    """Colander schema to bypass validations."""


class WorkflowTransitionSchema(colander.MappingSchema):
    """Workflow schema for transitions."""

    transition = colander.SchemaNode(
        typ=colander.String(),
        title='Transition to be executed.'
    )
    message = colander.SchemaNode(
        typ=colander.String(),
        title='Message for this transition.',
        missing=colander.drop,
        default=''
    )


def native_value(value: str, field: str=None):
    """Convert string value to native python values.

    :param value: value to convert.
    :param field: Name of the field this value relates to.
    :returns: the value coerced to python type
    """
    if isinstance(value, str):
        if value.lower() in ['on', 'true', 'yes']:
            value = True
        elif value.lower() in ['off', 'false', 'no']:
            value = False

        # HACK: Some fields should be coerced here.
        if field == 'id':
            return value

        try:
            return ast.literal_eval(value)
        except (ValueError, SyntaxError):
            pass

    return value
