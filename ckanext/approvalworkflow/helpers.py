import ckanext.approvalworkflow.db as db
from ckan.plugins import toolkit


def get_approvalworkflow_info(context):
    aw_model = db.ApprovalWorkflow.get()

    if aw_model:
        if aw_model.active:
            aw_settings = db.table_dictize(aw_model, context)
            return aw_settings


def get_approvalworkflow_org_info(context, pkg_id):
    package = toolkit.get_action('package_show')(None, {'id': pkg_id})
    owner_org = package['owner_org']

    aw_org_model = db.ApprovalWorkflowOrganization.get(organization_id=owner_org)
    
    if aw_org_model:
        aw_settings = db.table_dictize(aw_org_model, context)

        return aw_settings


def get_approval_org_info(context, org_id):
    aw_org_model = db.ApprovalWorkflowOrganization.get(organization_id=org_id)
    
    if aw_org_model:
        aw_settings = db.table_dictize(aw_org_model, context)

        return aw_settings