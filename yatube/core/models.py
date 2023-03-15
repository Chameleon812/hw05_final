from django.db import models


class CreatedModel(models.Model):
    """An abstract model that adds a creation date."""
    pub_date = models.DateTimeField(
        "Creation date",
        auto_now_add=True,
        db_index=True
    )

    class Meta:
        abstract = True
