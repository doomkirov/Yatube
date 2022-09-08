class Testing(models.Model):
    text = models.TextField(verbose_name='hello')
    author = models.ForeignKey(
        User,
        on_delete.models.CASCADE(),
    )
