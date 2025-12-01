[![CI][]][1] [![Python][]][2] [![CKAN][]][3]

# ckanext-approvalworkflow

This CKAN extension adds a structured dataset approval workflow to CKAN instances that require moderation before datasets become publicly visible. It enhances governance, quality control, and transparency by introducing a controlled review process and providing administrators with clear oversight of dataset publication activities.

The extension is designed to integrate seamlessly with CKAN’s core functionality while adding essential moderation features such as notifications, approval logging, and a dedicated approval stream.

This extension provides three configuration modes for managing the dataset approval workflow:

- **Not Active** – The approval workflow is disabled and datasets are published immediately.
- **Active** – The approval workflow is enabled globally for all organizations.
- **Activate Approval Workflow per Organization** – The workflow can be selectively enabled or disabled at the organization level.

---

## Dataset Approval Flow

When a user submits a new dataset, it enters an **Approval Pending** state. At this point:

### 1. Sent to Review Form  
When submitting a dataset, users see a **Review** button on the same page used for adding resources. Selecting this option places the dataset into the approval queue.

<img width="1237" height="848" alt="Sent to review form" src="https://github.com/user-attachments/assets/59620474-5994-430a-9791-5a6edaab3d73" />

---

### 2. Pending Datasets List  
Organization administrators can view all datasets currently awaiting approval.

<img width="1237" height="521" alt="Pending datasets list" src="https://github.com/user-attachments/assets/0d68db39-d541-46f1-a6cb-30889a8db393" />

---

### 3. Approval Form  
Admins and sysadmins can approve or reject the dataset and optionally include notes.

<img width="1237" height="539" alt="Approval form" src="https://github.com/user-attachments/assets/2943aa5b-a4b1-4366-a57a-715d3270b75a" />

---

### 4. Approval Stream Logging  
Every approval or rejection event is tracked in the Approval Stream, similar to CKAN’s Activity Stream.

<img width="1237" height="578" alt="Approval activity stream" src="https://github.com/user-attachments/assets/c53acda1-a8d3-40c7-b828-75b07cb57c1d" />

---

### Workflow Summary

1. **Notification** is sent — All administrators of the relevant CKAN organization receive an email containing a direct link to the dataset awaiting review.

2. **Review actions** — Organization administrators or system administrators can either approve or reject the dataset.

3. **Publication control** —  
   - Approved datasets move to a published state.  
   - Rejected datasets are saved as drafts.

4. **Approval Stream logging** — Every action is recorded with:  
   - The user who performed the action  
   - Timestamps for each workflow event  
   - Optional review notes  

This approval flow ensures that dataset publishing follows a consistent, auditable process and gives organizations full control over what becomes publicly accessible.

---

## Important Notes

**Note:**  
Any update made to a dataset by a **non-admin user** will automatically place the dataset back into the **Pending Approval** state.  
Dataset creations and updates performed by **organization administrators** or **sysadmins** are **not** subject to the approval workflow.



## Requirements

Make sure to have [email settings](https://docs.ckan.org/en/2.9/maintaining/configuration.html#email-settings) in your `ckan.ini` file.

Compatibility with core CKAN versions:

| CKAN version    | Compatible?   |
| --------------- | ------------- |
| 2.9             | Yes           |
| 2.10            | Yes           |
| 2.11            | Yes           |

For CKAN 2.9 use the 0.0.1 tag


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

If your CKAN instance uses additional dataset types defined through **ckanext-scheming**, beyond the default `dataset` type, ensure that these custom types are explicitly listed in the configuration. For example:

``ckanext.approvalworkflow.dataset_types = report, camel-photos, whitepaper``


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
