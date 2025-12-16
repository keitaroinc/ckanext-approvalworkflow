from ckan.common import _
import logging
from ckanext.approvalworkflow import helpers

log = logging.getLogger(__name__)


def prevent_editor_make_dataset_public2(key, data, errors, context):
    """
    Validator that prevents non-admin users from making datasets public
    This validator runs during both create and update operations.
    Args:
        key: The key for the field being validated (usually ('private',))
        data: The flattened data dict for the dataset
        errors: Dict for collecting validation errors
        context: The context dict
    """
    log.info("prevent_editor_make_dataset_public validator called")

    # Get the private field value
    private_value = data.get(key)
    log.info(f"Key: {key}")
    log.info(f"Private value: {private_value} (type: {type(private_value)})")

    # Determine if dataset is being set to public
    is_public = False

    if private_value is False:
        is_public = True
    elif isinstance(private_value, str):
        if private_value.lower() == 'false':
            is_public = True
    elif private_value is None or private_value == '':
        # Empty/None typically means private in CKAN
        is_public = False

    log.info(f"Dataset is public: {is_public}")

    # If dataset is private, no validation needed
    if not is_public:
        log.info("Dataset is private, skipping validation")
        return

    log.info("Dataset is being set to PUBLIC - running approval checks...")

    # Get current user from context
    user = context.get('auth_user_obj')
    if not user:
        # Try to get user by name
        username = context.get('user')
        if username:
            import ckan.model as model
            user = model.User.get(username)

    if not user:
        log.warning("No user found in context")
        errors[key].append(_('You must be logged in to create public datasets'))
        return

    log.info(f"User: {user.name if hasattr(user, 'name') else user}")

    # Check if user is sysadmin
    is_sysadmin = getattr(user, 'sysadmin', False)
    log.info(f"Is sysadmin: {is_sysadmin}")

    # Sysadmins can always make datasets public
    if is_sysadmin:
        log.info("User is sysadmin - allowing public dataset")
        return

    # Get organization
    owner_org_key = ('owner_org',)
    owner_org = data.get(owner_org_key)

    if not owner_org:
        log.warning("No organization specified")
        errors[key].append(_('Dataset must belong to an organization to be made public'))
        return

    log.info(f"Organization ID: {owner_org}")

    # Import helpers
    try:
        from ckanext.approvalworkflow import helpers
    except ImportError:
        log.error("Could not import helpers")
        errors[key].append(_('System error: Could not check permissions'))
        return

    # Check if user is organization admin
    try:
        is_org_admin = helpers.is_user_org_admin(owner_org)
        log.info(f"Is organization admin: {is_org_admin}")
    except Exception as e:
        log.error(f"Error checking if user is org admin: {e}")
        is_org_admin = False

    # Check if organization has approval workflow enabled
    try:
        org_has_workflow = helpers.get_org_approval_info(owner_org)
        log.info(f"Organization has approval workflow: {org_has_workflow}")
    except Exception as e:
        log.error(f"Error checking org approval info: {e}")
        org_has_workflow = False

    # If no approval workflow, allow org admins to make public
    if not org_has_workflow:
        if is_org_admin:
            log.info("No approval workflow required and user is admin - allowing public")
            return
        else:
            log.warning("No approval workflow but user is not admin")
            errors[key].append(
                _('You must be an organization administrator to make datasets public')
            )
            return

    # Organization HAS approval workflow enabled
    log.info("Organization has approval workflow enabled")

    # Check if this is an update or create
    pkg_id_key = ('id',)
    pkg_id = data.get(pkg_id_key)

    if pkg_id:
        log.info(f"This is an UPDATE for dataset: {pkg_id}")
    else:
        log.info("This is a CREATE operation")

    # RULE: Only admins can approve and make public
    if is_org_admin:
        log.info("User IS org admin - allowing public")
        return
    else:
        # User is NOT admin
        log.info("User is NOT org admin")
        errors[key].append(
            _('Only organization administrators can make datasets public. '
                'This dataset must be approved by an administrator before it can be made public.')
        )
        return


def prevent_editor_make_dataset_public(context, pkg_dict):
    # This function is called to prevent editors from making datasets public
    # It's a placeholder for now, but can be implemented later if needed
    pass