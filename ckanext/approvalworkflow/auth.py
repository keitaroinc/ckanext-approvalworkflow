import ckan.plugins.toolkit as toolkit
import ckan.authz as authz


def workflow(self, context):
    if context is not None:
        authorized = authz.is_sysadmin(context.user.username)
        if not authorized:
            return {'success': False,
                    'msg': toolkit._(
                        'You are not authorized to read this page')}
        else:
            return {'success': True}
    else:
        return {'success': False}
