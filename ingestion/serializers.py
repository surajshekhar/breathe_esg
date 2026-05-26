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
    class Meta:
        model = NormalizedEmissionRecord
        fields = "__all__"