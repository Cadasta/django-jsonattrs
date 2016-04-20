.. _installation:

============
Installation
============

You can install either the latest stable or development versions of
django-jsonattrs.

Requirements
============

The django-jsonattrs package works with the following Python and Django
versions:

- Python (3.5)
- Django (1.9)

Development version
===================

The latest development version can be found in its `Github
account`_. You can check the package out using::

    git clone https://github.com/Cadasta/django-jsonattrs.git

Then install it manually::

    cd django-jsonattrs
    python setup.py install

.. _Github account: https://github.com/Cadasta/django-jsonattrs/


Configuration
=============

To enable django-jsonattrs you need to add the package to your
``INSTALLED_APPS`` setting within your ``settings.py``::

    INSTALLED_APPS = (
        ...
        'jsonattrs',
    )
