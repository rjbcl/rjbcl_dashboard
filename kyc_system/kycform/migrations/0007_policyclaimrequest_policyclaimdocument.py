from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("kycform", "0006_group"),
    ]

    operations = [
        migrations.CreateModel(
            name="PolicyClaimRequest",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("claim_type", models.CharField(choices=[("LIFE", "Life Insurance"), ("DEATH", "Death Claim"), ("MEDICAL", "Medical Claim"), ("ACCIDENT", "Accident Claim"), ("FOREIGN_EMPLOYMENT", "Foreign Employment Claim"), ("OTHER", "Other")], max_length=32)),
                ("name_of_insured", models.CharField(max_length=200)),
                ("phone_number", models.CharField(max_length=20)),
                ("email", models.CharField(max_length=200)),
                ("date_of_loss", models.DateField()),
                ("contact_person", models.CharField(max_length=200)),
                ("policy_number", models.CharField(max_length=50)),
                ("place_of_loss", models.CharField(max_length=255)),
                ("details_of_loss", models.TextField()),
                ("message", models.TextField()),
                ("status", models.CharField(choices=[("PENDING", "Pending"), ("UNDER_REVIEW", "Under Review"), ("APPROVED", "Approved"), ("REJECTED", "Rejected")], default="PENDING", max_length=20)),
                ("submitted_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="claim_requests", to="kycform.kycuserinfo")),
            ],
            options={
                "db_table": "policy_claim_request",
                "ordering": ["-submitted_at"],
            },
        ),
        migrations.CreateModel(
            name="PolicyClaimDocument",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("file", models.FileField(upload_to="policy_claims/%Y/%m/%d/")),
                ("original_name", models.CharField(max_length=255)),
                ("uploaded_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("claim_request", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="documents", to="kycform.policyclaimrequest")),
            ],
            options={
                "db_table": "policy_claim_document",
                "ordering": ["uploaded_at"],
            },
        ),
    ]
