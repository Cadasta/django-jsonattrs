## Existing Django packages

Package                 Last release  Comment
-------                 ------------  -------
`eav-django`            2014-07-30
`django-mutant`         2016-01-14    Latest real "dynamic models" package
`django-dynamic-model`  (2013-05-09)  Obsolete?
`django-dynamo`         2011-08-03    Obsolete
`vera` (wq)             2016-01-08    Not quite relevant


## Motivation

From `django-dynamo` documentation:

> Dynamic models are beneficial for applications that need data
> structures, which are only known at runtime, but not when the
> application is coded. Or when existing models need to be extended at
> runtime by additional fields. Typical use cases are:
>
> 1. CMS: In content management systems, users often need to maintain
>    content that is unique for their specific website. The required
>    data structures to store and maintain this content is therefore
>    not known to the developers beforehand.
>
> 2. Web Shop: The owner of a web shop has highly customized products,
>    with very special product attributes. The shop developers want
>    the web shop owner to define these attributes herself.
>
> 3. Survey: If you have an application to create and maintain online
>    surveys, you do neither know the questions nor the possible
>    answers at runtime, but let your users define these, as they
>    implement their surveys.



## Requirements

From Jürgen Schackmann's DjangoCon Europe 2013 talk:

> Must-have components of a dynamic model application:
>
> * *Meta-model front end* to let users maintain their meta-models
> * *Meta-model representation* to store the meta-model information
> * *Meta-model analyser* to detect changes that require some further
>   actions (for schema, admin or model)
> * *Schema sync manager* to update and sync the database schema
> * *Admin sync manager* to update and sync the Django admin
> * *Model/cache sync manager* to update and sync the Django models
>   and model cache



## Data modelling notes

In common with many application platforms like ours, we need some kind
of dynamic schema extensibility: different projects may have different
requirements for the data that they collect and display, meaning that
we don’t want to tie ourselves to a particular set of database columns
for parties, spatial units or relationships. Instead, we should use
something like what the Django community calls "dynamic models". (One
of the more common implementations of this approach goes by the name
of "entity-attribute-value" modelling, or EAV.)

The particular way we’ve been thinking of implementing this in the
database is with a Postgres binary JSON column to store entity
attributes. This approach allows for indexing of the JSON data for
quick field membership and matching queries. (Postgres supports a
couple of different indexing methods, depending on the queries that
need to be optimised, so we’ll need to think about that.)

Here’s a simple concrete example of how this might be used. Some
relationships have a seasonality to them, e.g. grazing rights. A
seasonality attribute isn’t relevant in most cases, so it would be
inconvenient to have a column in a database table for this attribute
since it will be null most of the time. Instead, by using an attribute
for seasonality, we don’t need to provide a value unless it’s needed
for the particular relationship in question.

Another application of this more flexible approach is a better
approach to internationalisation of data collection and
representation. Good internationalisation involves much more than
translation of text labels and changing date or numeric
formats. Specifically, many field types have a "local flavour"
dimension to them: formats for postcodes, national ID numbers,
etc. are all country-dependent. By keeping track of the detailed
attribute type information for the attribute fields used in a project,
we can give very specific types (e.g. "Indian national ID numbers",
"UK postcodes") that will allow for accurate validation and
normalisation.

There are some questions about the implementation of this
functionality that we need to work out. First, there’s a natural
relationship between types of entities and the sets of attributes that
are relevant for them: for parties, an individual person has different
data than a corporate entity or a group. It makes sense to capture
this relationship in some way so that, for instance, the platform
front-end can determine what data should be provided for a given party
depending on the party type. In parallel with this, individual
attribute fields will have types, both "coarse" types (e.g. numeric,
textual, date/time) and potentially also "detailed" types (e.g. "birth
date", "address" or one of the "local flavour" field types described
above). We need a clean and simple way to manage this information for
use for data validation and normalisation. (Another idea for possible
later development is also to use this information to help with survey
generation: instead of generating surveys completely manually, some
questions and sections could be generated automatically from the data
model.)

The implementation of this approach could be based on one of the
existing Django dynamic model applications, although we would probably
need to adapt it to our needs, since none of the applications I’ve
seen are currently under development, and none of them take advantage
of Postgres’s JSON column types.

For metadata to describe attributes, we probably need something like:

 * a short name (the JSON field name);

 * a long name;

 * a base type (e.g. `text`, `integer`), and;

 * a full type (e.g. `gender`, `occupation`, `id-phone-number`,
   `za-post-code`, `area`, `spatial-source`,
   `id-government-parcel-id`, `land-use`, `free-text`, `tenure-term`).

The idea here is to make it possible to do the kind of "local flavour"
validation mentioned above if it’s required ("local flavour" to go
with `django-localflavor`).



## Code sketch

```
from django.db.models import Model
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import JSONField
from bitemporal import bitemporal

from .organization import Organization
from .project import Project


class AttributeManager(models.Manager):
    """
    Custom manager for attributes: just adds a filter to get the
    allowed attribute set for a given object.
    """
    def attribute_set(self, obj):
        """
        Filter queryset for the attributes associated with a particular
        object.
        """
        project = getattr(obj, 'project', None)
        obj_type = ContentType.objects.get_for_model(obj)
        obj_subtype = getattr(obj, 'type', '')
        organization = getattr(project, 'organization', None)
        # NOT QUITE RIGHT: NEEDS TO DEAL WITH DEFAULTING
        # (organization=None, project=None) AND SUBTYPING.  SOMETHING
        # LIKE THIS THOUGH...
        return self.filter(organization=organization, project=project,
                           obj_type=obj_type, obj_subtype=obj_subtype)


@bitemporal
class Attribute(Model):
    """
    Attribute definitions: sets of attributes allowed for different
    object types, keyed on organization, project, Django model class
    and optional model "subtype".  Default attribute sets for
    organizations have project=None; system default attribute sets
    have organization=None and project=None.
    Attributes within attribute sets are ordered by an integer index
    (mainly used for display in the front-end) and have:
     * a name (used for the JSON field name);
     * a long human-readable name;
     * a base type (text, number, etc.);
     * an optional "full" type (used to control detailed validation
       and normalisation -- values might be things like
       "id-post-code", "gb-driving-license-number",
       "us-telephone-number");
     * a presence field saying whether the a value for the attribute
       is required or optional (the third "delete" option can be used
       to remove attributes defined for a particular object type for
       selected subtypes).
    """
    BASE_TYPE_CHOICES = (
        ('NO', 'Number'),
        ('IN', 'Integer'),
        ('FR', 'Number with fraction'),
        ('TX', 'Text'),
    )
    PRESENCE_CHOICES = (
        ('R', 'Required'),
        ('O', 'Optional'),
        ('D', 'Delete'),
    )

    objects = AttributeManager()

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    obj_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    obj_subtype = models.CharField(max_length=100)

    index = models.IntegerField()
    name = models.CharField(max_length=100)
    longname = models.TextField()
    base_type = models.CharField(max_length=2, choices=BASE_TYPE_CHOICES)
    full_type = models.CharField(max_length=100)
    presence = models.CharField(max_length=1, choices=PRESENCE_CHOICES,
                                default='O')

    class Meta:
        index_together = ['organization', 'project', 'obj_type', 'obj_subtype']
        ordering = ['index']


class JSONAttributesField(JSONField):
    """
    This is just like a normal ``JSONField`` field except that it is
    constrained to contain a single JSON object, and uses the
    ``Attribute`` model defined above to validate assignments to elements
    of that object.
    The way this is supposed to work is as follows:
    When you first attempt to assign to a member of a
    ``JSONAttributesField``, the class of which the field is a member
    is used to determine a project (from the class's ``project`` field
    if it has one), content type (from the class) and model subtype
    (from the object's ``type`` field if it has one).  These values are
    used to look up an attribute set, and this is then used to handle
    validation of assignments to the JSON field.
    """

    # NOT SURE HOW TO IMPLEMENT THIS YET...
    def something_something_something(self, obj):
        self.attrs = Attribute.objects.attribute_set(obj)
```
