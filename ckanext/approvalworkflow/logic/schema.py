import ckan.plugins as p
from ckanext.approvalworkflow.interfaces import IWorkflowSchema


def default_approval_workflow_schema():
    ignore_empty = p.toolkit.get_validator('ignore_empty')
    ignore_missing = p.toolkit.get_validator('ignore_missing')
    not_empty = p.toolkit.get_validator('not_empty')
    isodate = p.toolkit.get_validator('isodate')

    try:
        unicode_safe = p.toolkit.get_validator('unicode_safe')
    except p.toolkit.UnknownValidator:
        # CKAN 2.7
        unicode_safe = unicode  # noqa: F821
    return {
        'id': [ignore_empty, unicode_safe],
        'active': [not_empty, unicode_safe],
        'active_per_organization': [not_empty, unicode_safe],
        'disable_edit': [not_empty, unicode_safe],
        'created': [ignore_missing, isodate],
        'modified': [ignore_missing, isodate]
    }


def update_approval_workflow_schema():
    '''
    Returns the schema for the pages fields that can be added by other
    extensions.

    By default these are the keys of the
    :py:func:`ckanext.logic.schema.default_pages_schema`.
    Extensions can add or remove keys from this schema using the
    :py:meth:`ckanext.pages.interfaces.IPagesSchema.update_pages_schema`
    method.

    :returns: a dictionary mapping fields keys to lists of validator and
    converter functions to be applied to those fields
    :rtype: dictionary
    '''

    schema = default_approval_workflow_schema()
    for plugin in p.PluginImplementations(IWorkflowSchema):
        if hasattr(plugin, 'update_approval_workflow_schema'):
            schema = plugin.update_approval_workflow_schema(schema)

    return schema
