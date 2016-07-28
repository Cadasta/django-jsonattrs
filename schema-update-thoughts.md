## Schema calculation

First, here's the way that the schema calculation currently works:

1. Each Django content type for which you want to use
   `JSONAttributesField` has a list of *schema selectors* configured
   in the Django settings.  These selectors are period-separated
   sequences of model field names to follow to find a selector value
   (with `pk` getting you the primary key of whatever you're looking
   at).  Some examples: `project.organization.pk`, `project.pk`,
   `type`.  All but the last of the elements in these period-separated
   sequences should be the names of foreign key fields.  The last
   element in the sequence can be either a "normal" field name (whose
   value is convertible to a string) or `pk` (to use the primary key
   of a model instance referred to via a foreign key).

2. Each `Schema` model instance in the database has a content type to
   which it applies, a fixed sequence of schema selector values and a
   set of attribute fields.  A `Schema` instance is said to be
   *applicable* to a model instance containing a `JSONAttributesField`
   field if the content types of the schema and model instances match
   and the schema selector list for the `Schema` instance is a prefix
   of the list of schema selectors for the model instance.

3. To find the effective attribute list for a model instance
   containing a `JSONAttributesField` field, the attribute lists of
   all *Schema* instances that are *applicable* for the model instance
   are composed in order from least to most specific (one *Schema* is
   less specific than another if its schema selector list is shorter).


## Example scenario

```
class B(models.Model):
  pass

class C(models.Model):
  f3 = models.ForeignKey(D)

class D(models.Model):
  pass

class A(models.Model):
  f1 = models.ForeignKey(B)
  f2 = models.ForeignKey(C)
  f4 = models.CharField(max_length=32)
  f5 = models.CharField(max_length=100)
  attrs = JSONAttributesField()
```

Schema selectors for content type `A` are `(f1.pk. f2.f3.pk, f4)`.


## Schema selector updating

 1. Change to any field in instance of `A` not involved in schema
    selectors => no schema change.
 2. Change to `a.f1` => recalculate schemas.
 3. Change to `a.f2` => recalculate schemas.
 4. Change to `a.f2.f3` => recalculate schemas?
 5. Change to `a.f4` => recalculate schemas.

Schema recalculation involves the following steps, which should run in
a `pre_save` signal handler on any model class containing a
`JSONAttributesField` field:

 1. Save old instance attribute list.
 2. Calculate new attribute list from new selectors.
 3. Determine the difference between the new and old attribute lists.
 4. If the differences contain any illegal attribute list changes,
    raise an exception (thus preventing the model instance update by
    cancelling the save action).
 5. If the attribute list differences are OK, allow the save to
    proceed, and update the model instance's attribute list.
