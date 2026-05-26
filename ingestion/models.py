from django.db import models


class Company(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class DataSource(models.Model):
    SOURCE_TYPES = [
        ("sap", "SAP"),
        ("utility", "Utility"),
        ("travel", "Travel"),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPES)

    file_name = models.CharField(max_length=255)

    status = models.CharField(max_length=50, default="uploaded")

    uploaded_at = models.DateTimeField(auto_now_add=True)


class RawRecord(models.Model):
    source = models.ForeignKey(DataSource, on_delete=models.CASCADE)

    raw_json = models.JSONField()

    ingestion_errors = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)


class EmissionFactor(models.Model):
    activity_type = models.CharField(max_length=100)

    factor = models.FloatField()

    unit = models.CharField(max_length=50)

    source = models.CharField(max_length=100)


class PlantCodeLookup(models.Model):
    plant_code = models.CharField(max_length=50, unique=True)

    plant_name = models.CharField(max_length=255)

    country = models.CharField(max_length=100)


class NormalizedEmissionRecord(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("suspicious", "Suspicious"),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    raw_record = models.ForeignKey(
        RawRecord,
        on_delete=models.CASCADE
    )

    scope = models.CharField(max_length=20)

    category = models.CharField(max_length=100)

    activity_type = models.CharField(max_length=100)

    quantity = models.FloatField()

    original_unit = models.CharField(max_length=50)

    normalized_unit = models.CharField(max_length=50)

    co2e = models.FloatField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    locked_for_audit = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)


class AuditLog(models.Model):
    record = models.ForeignKey(
        NormalizedEmissionRecord,
        on_delete=models.CASCADE
    )

    action = models.CharField(max_length=100)

    timestamp = models.DateTimeField(auto_now_add=True)