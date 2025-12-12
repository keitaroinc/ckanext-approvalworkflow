"""
Custom CKAN validator for controlling public dataset visibility
File: ckanext/yourextension/validators.py
"""

from ckan.common import _
import ckan.plugins.toolkit as toolkit


def validate_public_dataset(key, data, errors, context):
    """
    Custom validator that checks if a dataset can be set to public.
    
    This validator checks custom conditions before allowing a dataset
    to have private=False (public visibility).
    
    Args:
        key: The key for the field being validated
        data: The flattened data dict for the dataset
        errors: Dict for collecting validation errors
        context: The context dict
    """
    
    # Get the private field value
    private_value = data.get(key)

    # If dataset is being set to public (private=False)
    if private_value == False or private_value == 'False':
        
        # Example condition 1: Check if dataset has a title
        title_key = ('title',)
        title = data.get(title_key, '')
        
        if not title or len(title.strip()) < 5:
            errors[key].append(_('Dataset must have a title with at least 5 characters to be made public'))
            return
        
    
    # If all conditions pass, validation succeeds
    return


def must_have_license(key, data, errors, context):
    """
    Validator ensuring public datasets have a license.
    """
    private_value = data.get(key)
    
    if private_value == False or private_value == 'False':
        license_key = ('license_id',)
        license_id = data.get(license_key, '')
        
        if not license_id or license_id == 'notspecified':
            errors[key].append(_('You must specify a license before making the dataset public'))