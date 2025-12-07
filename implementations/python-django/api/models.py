from django.db import models


# Create your models here.
class User(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)

    class Meta:
        db_table = "users"  # FastAPI와 동일한 테이블 사용
        managed = False  # Django가 테이블을 관리하지 않음
