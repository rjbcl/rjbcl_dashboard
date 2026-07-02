from django.db import migrations, models
import django.db.models.deletion
from django.utils import timezone


class Migration(migrations.Migration):

    dependencies = [
        ("kycform", "0008_alter_policyclaimrequest_claim_type_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="KycSmsNotification",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("mobile", models.CharField(max_length=20)),
                ("message", models.TextField()),
                ("template_name", models.CharField(default="kyc_verified", max_length=100)),
                ("source", models.CharField(default="ADMIN", max_length=50)),
                (
                    "delivery_status",
                    models.CharField(
                        choices=[
                            ("PENDING", "Pending"),
                            ("SENT", "Sent"),
                            ("FAILED", "Failed"),
                            ("SKIPPED", "Skipped"),
                        ],
                        default="PENDING",
                        max_length=20,
                    ),
                ),
                ("provider_reference", models.CharField(blank=True, max_length=150, null=True)),
                ("error_message", models.TextField(blank=True, null=True)),
                ("sent_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(default=timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sms_notifications",
                        to="kycform.kycuserinfo",
                    ),
                ),
            ],
            options={
                "db_table": "kyc_sms_notification",
                "ordering": ["-created_at"],
            },
        ),
    ]
