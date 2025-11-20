import logging
from ckan.common import config
from ckan.lib.base import render
from ckan.common import _
from ckan.lib import mailer

log = logging.getLogger(__name__)


def get_approval_body(user, group_dict=None, pkg_dict=None):
    # get organization info
    if group_dict:
        group_type = (_('organization') if group_dict['is_organization']
                      else _('group'))

    extra_vars = {
        'aw_link_datasets': get_approval_link(pkg_dict),
        'site_title': config.get('ckan.site_title'),
        'site_url': config.get('ckan.site_url'),
        'user_name': user.name,
    }
    if pkg_dict:
        extra_vars['dataset_link'] = config.get('ckan.site_url') + '/dataset/edit/' + pkg_dict['name']
    if group_dict:
        extra_vars['group_type'] = group_type
        extra_vars['group_title'] = group_dict.get('title')

    return render('email/approval_needed.txt', extra_vars)


def get_approval_link(pkg_dict=None):
    if pkg_dict:
        workflow = config.get('ckan.site_url') + '/workflow/datasets'
        return workflow


def send_approval_needed(user, group_dict=None, pkg_dict=None):
    body = get_approval_body(user, group_dict, pkg_dict)
    extra_vars = {
        'aw_link_datasets': get_approval_link(pkg_dict),
        'site_title': config.get('ckan.site_title')
    }
    print(extra_vars['site_title'])

    if group_dict:
        group_type = (_('organization') if group_dict['is_organization']
                      else _('group'))
    if pkg_dict:
        extra_vars['dataset_link'] = config.get('ckan.site_url') + '/dataset/edit/' + pkg_dict['name']
    if group_dict:
        extra_vars['group_type'] = group_type
        extra_vars['group_title'] = group_dict.get('title')

    subject = render('email/approval_needed.txt', extra_vars)

    # Make sure we only use the first line
    subject = subject.split('\n')[0]

    mailer.mail_user(user, subject, body)
