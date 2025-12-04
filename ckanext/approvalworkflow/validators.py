from ckanext.approvalworkflow import helpers


def validate_org_admin_state(key, data, errors, context):
    import sys
    print("VALIDATOR RUNNING", file=sys.stderr)
    print("DATA KEYS:", data.keys(), file=sys.stderr)

    private_value = data.get('private') or data.get('is_private')

    is_public = str(private_value).lower() == 'false'

    if not is_public:
        return

    user = context.get('auth_user_obj')
    owner_org = data.get('owner_org')

    is_admin = (
        user and (user.sysadmin or helpers.is_user_org_admin(owner_org))
    )

    if not is_admin:
        errors['private'].append('Only organization admins may publish datasets.')
