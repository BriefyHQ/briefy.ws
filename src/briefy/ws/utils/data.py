"""Data utilities for Briefy webservices."""
from briefy.common.log import logger
from colander import Mapping
from colander import required
from colander import SchemaNode
from colander import Sequence
from colanderalchemy import SQLAlchemySchemaNode
from colanderalchemy.schema import _creation_order
from sqlalchemy.orm import ColumnProperty
from sqlalchemy.orm import RelationshipProperty
from sqlalchemy.schema import Column

import ast
import colander


class BriefySchemaNode(SQLAlchemySchemaNode):
    """Colander schema validation for SQLAlchemy."""

    def _change_name(self, prop: ColumnProperty):
        """Change name of the column attribute when start with underscore."""
        column_name = prop.key
        return column_name[1:] if column_name.startswith('_') else column_name

    def _get_node(self, prop: ColumnProperty, overrides: dict, schema_method: str):
        """Get node wrapper that change node name when start with underscore.

        This is necessary to use the descriptor as getter and setter.
        """
        node_name = prop.key
        column_name = self._change_name(prop)
        excludes = self.excludes
        to_exclude = column_name in excludes or node_name in excludes
        if to_exclude:
            return None
        parent_method = getattr(super(), schema_method)
        node = parent_method(prop, overrides)
        node.name = column_name
        return node

    def get_schema_from_column(self, prop, overrides):
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
            will take precendence over all others.
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
        # The name of the SchemaNode is the ColumnProperty key.
        name = self._change_name(prop)
        kwargs = dict(name=name)
        declarative_overrides = prop.info.get(self.sqla_info_key, {}).copy()
        self.declarative_overrides[name] = declarative_overrides.copy()

        class_ = prop.mapper.class_

        if declarative_overrides.pop('exclude', False):
            logger.debug('Relationship %s skipped due to declarative overrides', name)
            return None

        for key in ['name', 'typ']:
            self.check_overrides(name, key, {}, declarative_overrides,
                                 overrides)

        key = 'children'
        imperative_children = overrides.pop(key, None)
        declarative_children = declarative_overrides.pop(key, None)
        if imperative_children is not None:
            children = imperative_children
            msg = 'Relationship %s: %s overridden imperatively.'
            logger.debug(msg, name, key)

        elif declarative_children is not None:
            children = declarative_children
            msg = 'Relationship %s: %s overridden via declarative.'
            logger.debug(msg, name, key)

        else:
            children = None

        key = 'includes'
        imperative_includes = overrides.pop(key, None)
        declarative_includes = declarative_overrides.pop(key, None)
        if imperative_includes is not None:
            includes = imperative_includes
            msg = 'Relationship %s: %s overridden imperatively.'
            logger.debug(msg, name, key)

        elif declarative_includes is not None:
            includes = declarative_includes
            msg = 'Relationship %s: %s overridden via declarative.'
            logger.debug(msg, name, key)

        else:
            includes = None

        key = 'excludes'
        imperative_excludes = overrides.pop(key, None)
        declarative_excludes = declarative_overrides.pop(key, None)

        if imperative_excludes is not None:
            excludes = imperative_excludes
            msg = 'Relationship %s: %s overridden imperatively.'
            logger.debug(msg, name, key)

        elif declarative_excludes is not None:
            excludes = declarative_excludes
            msg = 'Relationship %s: %s overridden via declarative.'
            logger.debug(msg, name, key)

        else:
            excludes = None

        key = 'overrides'
        imperative_rel_overrides = overrides.pop(key, None)
        declarative_rel_overrides = declarative_overrides.pop(key, None)

        if imperative_rel_overrides is not None:
            rel_overrides = imperative_rel_overrides
            msg = 'Relationship %s: %s overridden imperatively.'
            logger.debug(msg, name, key)

        elif declarative_rel_overrides is not None:
            rel_overrides = declarative_rel_overrides
            msg = 'Relationship %s: %s overridden via declarative.'
            logger.debug(msg, name, key)

        else:
            rel_overrides = None

        # Add default values for missing parameters.
        if prop.innerjoin:
            # Inner joined relationships imply it is mandatory
            missing = required
        else:
            # Any other join is thus optional
            missing = []
        kwargs['missing'] = missing

        kwargs.update(declarative_overrides)
        kwargs.update(overrides)

        if children is not None:
            if prop.uselist:
                # xToMany relationships.
                return SchemaNode(Sequence(), *children, **kwargs)
            else:
                # xToOne relationships.
                return SchemaNode(Mapping(), *children, **kwargs)

        node = BriefySchemaNode(class_,
                                name=name,
                                includes=includes,
                                excludes=excludes,
                                overrides=rel_overrides,
                                missing=missing,
                                parents_=self.parents_ + [self.class_])

        if prop.uselist:
            node = SchemaNode(Sequence(), node, **kwargs)

        node.name = name

        return node

    def add_nodes(self, includes, excludes, overrides):
        """Add nodes to the schema."""
        if set(excludes) & set(includes):
            msg = 'excludes and includes are mutually exclusive.'
            raise ValueError(msg)

        properties = sorted(self.inspector.attrs, key=_creation_order)
        # sorted to maintain the order in which the attributes
        # are defined
        for name in includes or [item.key for item in properties]:
            prop = self.inspector.attrs.get(name, name)

            if name in excludes or (includes and name not in includes):
                logger.debug('Attribute %s skipped imperatively', name)
                continue

            name_overrides_copy = overrides.get(name, {}).copy()

            if (isinstance(prop, ColumnProperty)
                    and isinstance(prop.columns[0], Column)):
                node = self.get_schema_from_column(
                    prop,
                    name_overrides_copy
                )
            elif isinstance(prop, RelationshipProperty):
                if prop.mapper.class_ in self.parents_ and name not in includes:
                    continue
                node = self.get_schema_from_relationship(
                    prop,
                    name_overrides_copy
                )
            elif isinstance(prop, colander.SchemaNode):
                node = prop
            elif isinstance(prop, str) and name in overrides:
                name_overrides_copy['name']= prop
                node = colander.SchemaNode(**name_overrides_copy)
            else:
                logger.debug(
                    'Attribute %s skipped due to not being '
                    'a ColumnProperty or RelationshipProperty',
                    name
                )
                continue

            if node is not None:
                self.add(node)


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
    return value
