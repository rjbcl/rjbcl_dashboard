from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("kycform", "0007_policyclaimrequest_policyclaimdocument"),
    ]

    operations = [
        migrations.AlterField(
            model_name="policyclaimrequest",
            name="claim_type",
            field=models.CharField(max_length=100),
        ),
        migrations.AddField(
            model_name="policyclaimrequest",
            name="product_name",
            field=models.CharField(default="", max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="policyclaimrequest",
            name="product_plan_id",
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
