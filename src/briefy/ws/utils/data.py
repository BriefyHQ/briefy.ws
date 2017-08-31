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

import colander
import typing as t


ColumnOrRelationshipProp = t.Union[ColumnProperty, RelationshipProperty]
ConfigOrNone = t.Union[dict, None]


class BriefySchemaNode(SQLAlchemySchemaNode):
    """Colander schema validation for SQLAlchemy."""

    def _change_name(self, prop: ColumnOrRelationshipProp) -> str:
        """Change column name if starts with _.

        :param prop: ColumnProperty or RelationshipProperty
        :return: column name, without a starting _.
        """
        column_name = prop.key
        return column_name[1:] if column_name.startswith('_') else column_name

    def _get_node(self, prop: ColumnProperty, overrides: dict, schema_method: str) -> SchemaNode:
        """Get node wrapper that change node name when start with underscore.

        This is necessary to use the descriptor as getter and setter.

        :param prop: ColumnProperty
        :param overrides: Dictionary with attributes to be overriden.
        :param schema_method: Method name to use to get the SchemaNode.
        :return: SchemaNode instance.
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

    def get_schema_from_column(self, prop: ColumnProperty, overrides: dict) -> SchemaNode:
        """Build and return a :class:`colander.SchemaNode` for a given Column.

        This method uses information stored in the column within the ``info``
        that was passed to the Column on creation.  This means that
        ``Colander`` options can be specified declaratively in
        ``SQLAlchemy`` models using the ``info`` argument that you can
        pass to :class:`sqlalchemy.Column`.

        Arguments/Keywords

        :param prop: ColumnProperty
        :param overrides: Dictionary with attributes to be overriden.
        :return: SchemaNode instance.
        """
        return self._get_node(prop, overrides, 'get_schema_from_column')

    @staticmethod
    def _relationship_config(name: str, key: str, imp: dict, decl: dict) -> ConfigOrNone:
        """Process overrides.

        :param name: RelationshipProperty name.
        :param key: Category name. i.e.: children, includes, excludes, overrides.
        :param imp: Imperative configuration.
        :param decl: Declarative configuration.
        :return: Configuration.
        """
        config = None
        imperative_children = imp.pop(key, None)
        declarative_children = decl.pop(key, None)
        if imperative_children is not None:
            config = imperative_children
            logger.debug(f'Relationship {name}: {key} overridden imperatively.')
        elif declarative_children is not None:
            config = declarative_children
            logger.debug(f'Relationship {name}: {key} overridden via declarative.')
        return config

    def get_schema_from_relationship(
            self,
            prop: RelationshipProperty,
            overrides: dict
    ) -> SchemaNode:
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

        :param prop: RelationshipProperty
        :param overrides: Dictionary with attributes to be overriden.
        :return: SchemaNode instance.
        """
        # The name of the SchemaNode is the ColumnProperty key.
        name = self._change_name(prop)
        kwargs = {'name': name}
        decl_overrides = prop.info.get(self.sqla_info_key, {}).copy()
        self.declarative_overrides[name] = decl_overrides.copy()
        class_ = prop.mapper.class_
        if decl_overrides.pop('exclude', False):
            logger.debug(f'Relationship {name} skipped due to declarative overrides')
            return None

        for key in ['name', 'typ']:
            self.check_overrides(name, key, {}, decl_overrides, overrides)

        children = self._relationship_config(name, 'children', overrides, decl_overrides)
        includes = self._relationship_config(name, 'includes', overrides, decl_overrides)
        excludes = self._relationship_config(name, 'excludes', overrides, decl_overrides)
        rel_overrides = self._relationship_config(name, 'overrides', overrides, decl_overrides)

        # Add default values for missing parameters.
        missing = []
        if prop.innerjoin:
            # Inner joined relationships imply it is mandatory
            missing = required

        kwargs['missing'] = missing

        kwargs.update(decl_overrides)
        kwargs.update(overrides)

        if children is not None:
            node_type = Mapping()
            if prop.uselist:
                # xToMany relationships.
                node_type = Sequence()
            return SchemaNode(node_type, *children, **kwargs)

        node = BriefySchemaNode(
            class_, name=name, includes=includes, excludes=excludes, overrides=rel_overrides,
            missing=missing, parents_=self.parents_ + [self.class_]
        )

        if prop.uselist:
            node = SchemaNode(Sequence(), node, **kwargs)

        node.name = name
        return node

    def add_nodes(
            self,
            base_includes: t.Sequence[str],
            excludes: t.Sequence[str],
            overrides: dict
    ):
        """Add nodes to the schema."""
        if set(excludes) & set(base_includes):
            raise ValueError('excludes and includes are mutually exclusive.')

        properties = sorted(self.inspector.attrs, key=_creation_order)
        # Explicitly add overrides in here
        properties = [item.key for item in properties]
        all_fields = properties + [o for o in overrides if o not in properties]
        includes = []
        if base_includes:
            for item in base_includes:
                prefixed = f'_{item}'
                if item in all_fields:
                    includes.append(item)
                elif prefixed in all_fields:
                    includes.append(prefixed)

        for name in includes or all_fields:
            prop = self.inspector.attrs.get(name, name)
            if name in excludes or (includes and name not in includes):
                logger.debug(f'Attribute {name} skipped imperatively')
                continue

            name_overrides_copy = overrides.get(name, {}).copy()

            if (isinstance(prop, ColumnProperty) and isinstance(prop.columns[0], Column)):
                node = self.get_schema_from_column(prop, name_overrides_copy)
            elif isinstance(prop, RelationshipProperty):
                if prop.mapper.class_ in self.parents_ and name not in includes:
                    continue
                node = self.get_schema_from_relationship(prop, name_overrides_copy)
            elif isinstance(prop, colander.SchemaNode):
                node = prop
            elif isinstance(prop, str) and name in overrides:
                name_overrides_copy['name'] = prop
                node = colander.SchemaNode(**name_overrides_copy)
            else:
                logger.debug(
                    f'Attribute {name} skipped due to not being '
                    'a ColumnProperty or RelationshipProperty',
                )
                continue

            if node is not None:
                self.add(node)


class NullSchema(colander.MappingSchema):
    """Colander schema to bypass validations."""


class WorkflowTransitionSchema(colander.MappingSchema):
    """Workflow schema for transitions."""

    transition = colander.SchemaNode(typ=colander.String(), title='Transition to be executed.')
    message = colander.SchemaNode(
        typ=colander.String(),
        title='Message for this transition.',
        missing=colander.drop,
        default=''
    )


def native_value(value: str, field: str=None) -> bool:
    """Convert string value to native python values.

    :param value: value to convert.
    :param field: Name of the field this value relates to.
    :returns: the value coerced to python type.
    """
    if isinstance(value, str):
        if value.lower() in ['on', 'true', 'yes']:
            value = True
        elif value.lower() in ['off', 'false', 'no']:
            value = False
    return value
