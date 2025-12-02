import click

import ckanext.approvalworkflow.utils as utils


def get_commands():
    return [approval_workflow]


@click.group(u"approval_workflow", short_help=u"Approval workflow commands")
def approval_workflow():
    pass


@approval_workflow.command()
def initdb():
    """Adds approval workflow db tables to ckan

    Usage:

        approval_workflow initdb
        - Creates the necessary tables in the database
    """
    utils.initdb()
    click.secho(u"Approval Workflow DB tables created", fg=u"green")


@approval_workflow.command()
def dropdb():
    utils.dropdb()
    click.secho(u"Approval Workflow DB tables deleted", fg=u"green")
