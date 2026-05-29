from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers
from .models import *


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = "__all__"


class DataSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataSource
        fields = "__all__"


class RawRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = RawRecord
        fields = "__all__"


class NormalizedEmissionRecordSerializer(serializers.ModelSerializer):
    source_type = serializers.SerializerMethodField()

    class Meta:
        model = NormalizedEmissionRecord
        fields = "__all__"

    def get_source_type(self, obj):
        if obj.raw_record_id is None:
            return ""
        try:
            return obj.raw_record.source.source_type
        except ObjectDoesNotExist:
            return ""