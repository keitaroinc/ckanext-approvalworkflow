[![CI][]][1] [![Python][]][2] [![CKAN][]][3]

# ckanext-approvalworkflow

A CKAN extension for adding an Approval Workflow on Datasets.

The extension provides 3 options for the Approval Workflow:
- Not active
- Active
- Activate appruval workflow per organization


## Requirements

Make sure to have [email settings](https://docs.ckan.org/en/2.9/maintaining/configuration.html#email-settings) in your `ckan.ini` file.

The extension can work with [ckanext-datasetversions](https://github.com/keitaroinc/ckanext-datasetversions)


Compatibility with core CKAN versions: 2.10, 2.11

For CKAN 2.9 use tag 0.0.1

## Installation
To install ckanext-approvalworkflow:

1. Activate your CKAN virtual environment, for example:

     . /usr/lib/ckan/default/bin/activate

2. Clone the source and install it on the virtualenv

    `git clone https://github.com//ckanext-approvalworkflow.git`
    
    `cd ckanext-approvalworkflow`
    
    `pip install -e .`
    
	`pip install -r requirements.txt`

3. Add `approvalworkflow` to the `ckan.plugins` setting in your CKAN
   config file (by default the config file is located at
   `/etc/ckan/default/ckan.ini`).

4. Create the database tables running:

    `ckan -c /path/to/ini/file approval_workflow initdb`

5. If you are using ckanext-datasetversions, make sure to add `datasetversions` plugin after `approvalworkflow` in your CKAN config file

6. Restart CKAN. For example if you've deployed CKAN with Apache on Ubuntu:

    `sudo service apache2 reload`


## Config settings

None at present


## Developer installation

To install ckanext-approvalworkflow for development, activate your CKAN virtualenv and
do:

    git clone https://github.com//ckanext-approvalworkflow.git
    cd ckanext-approvalworkflow
    python setup.py develop
    pip install -r dev-requirements.txt


## Tests

To run the tests, do:

    pytest --ckan-ini=test.ini


## Releasing a new version of ckanext-approvalworkflow

If ckanext-approvalworkflow should be available on PyPI you can follow these steps to publish a new version:

1. Update the version number in the `setup.py` file. See [PEP 440](http://legacy.python.org/dev/peps/pep-0440/#public-version-identifiers) for how to choose version numbers.

2. Make sure you have the latest version of necessary packages:

    pip install --upgrade setuptools wheel twine

3. Create a source and binary distributions of the new version:

       python setup.py sdist bdist_wheel && twine check dist/*

   Fix any errors you get.

4. Upload the source distribution to PyPI:

       twine upload dist/*

5. Commit any outstanding changes:

       git commit -a
       git push

6. Tag the new release of the project on GitHub with the version number from
   the `setup.py` file. For example if the version number in `setup.py` is
   0.0.1 then do:

       git tag 0.0.1
       git push --tags

## License

[AGPL](https://www.gnu.org/licenses/agpl-3.0.en.html)


  [CI]: https://github.com/keitaroinc/ckanext-approvalworkflow/workflows/CI/badge.svg
  [1]: https://github.com/keitaroinc/ckanext-approvalworkflow/actions
  [Python]: https://img.shields.io/badge/python-3.9%20|%203.10%20|%203.11-blue
  [2]: https://www.python.org
  [CKAN]: https://img.shields.io/badge/ckan-%202.9%20|%202.10%20|%202.11-yellow
  [3]: https://www.ckan.org
