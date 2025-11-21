import ckanext.approvalworkflow.db as db
from ckan.plugins import toolkit
from ckan.model import Member, User, Session

g = toolkit.g


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


def get_organization_info_for_user(include_dataset_count=True):
    '''Return a list of organizations with additional data
        such as user role ('capacity')
       for the ones that the user has permission.
    '''
    context = {'user': g.user}
    data_dict = {
        'id': g.userobj.id,
        }
    return toolkit.get_action('organization_list_for_user')(context, data_dict)


def is_user_org_admin(org_id):

    '''Gets the whole information for every organization
        the user has permissions for'''
    info = get_organization_info_for_user()

    for organization in info:
        # checking if the user has the role of admin in the organizations for which it has permissions
        if (organization.get('id') == org_id and organization.get('capacity') == 'admin'):
            return True

    return False


def get_org_admins_raw(org_id):
    """Return User objects for organization admins of the given org_id"""
    admins = (
        Session.query(User)
        .join(Member, Member.table_id == User.id)
        .filter(
            Member.group_id == org_id,
            Member.capacity == 'admin'
        )
        .all()
    )
    return admins
