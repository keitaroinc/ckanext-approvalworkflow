from ckan.plugins.interfaces import Interface


class IWorkflowSchema(Interface):
    '''
    Interface to define custom schemas.
    '''

    def update_approval_workflow_schema(self, schema):
        u'''
        Return a schema with the fields of the approval workflow.

        ckanext-approvalworkflow will use the returned schema to define and validate
        the fields before storing them.
        '''
        return schema
