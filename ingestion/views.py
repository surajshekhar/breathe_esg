import csv
import io

from rest_framework.response import Response
from rest_framework.decorators import api_view

from .models import DataSource, RawRecord, NormalizedEmissionRecord, AuditLog
from .serializers import DataSourceSerializer, NormalizedEmissionRecordSerializer



@api_view(["GET"])
def health_check(request):
    return Response({
        "message": "Backend working"
    })

@api_view(["GET"])
def get_records(request):
    records = NormalizedEmissionRecord.objects.all()

    serializer = NormalizedEmissionRecordSerializer(
        records,
        many=True
    )

    return Response(serializer.data)

@api_view(["POST"])
def create_data_source(request):

    serializer = DataSourceSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=201)

    return Response(serializer.errors, status=400)


def _decode_bytes(data):
    for encoding in ("utf-8-sig", "utf-8", "latin1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def _pick_dialect(sample_text):
    try:
        return csv.Sniffer().sniff(sample_text)
    except csv.Error:
        return csv.excel


def _is_header(row):
    for cell in row:
        cell = (cell or "").strip()
        if any(ch.isalpha() for ch in cell):
            return True
    return False


def _read_csv_rows(uploaded_file):
    data = uploaded_file.read()
    text = _decode_bytes(data)
    sample = text[:2048]
    dialect = _pick_dialect(sample)

    reader = csv.reader(io.StringIO(text), dialect=dialect)
    rows = [
        [c.strip() for c in row]
        for row in reader
        if any((c or "").strip() for c in row)
    ]

    if not rows:
        return []

    header_row = rows[0] if _is_header(rows[0]) else None
    if header_row:
        headers = [h or f"col_{i + 1}" for i, h in enumerate(header_row)]
        data_rows = rows[1:]
    else:
        max_len = max(len(r) for r in rows)
        headers = [f"col_{i + 1}" for i in range(max_len)]
        data_rows = rows

    out = []
    for index, row in enumerate(data_rows, start=1):
        row = list(row)
        if len(row) < len(headers):
            row += [""] * (len(headers) - len(row))
        if len(row) > len(headers):
            extra_count = len(row) - len(headers)
            headers += [f"extra_{i + 1}" for i in range(extra_count)]
        item = {"row_num": index}
        for i, key in enumerate(headers):
            item[key] = row[i] if i < len(row) else ""
        out.append(item)

    return out


def _find_value(row, keys):
    lowered = {str(k).strip().lower(): v for k, v in row.items()}
    for key in keys:
        if key in lowered and str(lowered[key]).strip() != "":
            return str(lowered[key]).strip()
    return ""


def _parse_number(value):
    if value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _normalize_unit(unit):
    unit = (unit or "").strip().lower()
    unit_map = {
        "kwh": "kwh",
        "kilowatt-hour": "kwh",
        "mwh": "mwh",
        "megawatt-hour": "mwh",
        "km": "km",
        "kilometer": "km",
        "kilometers": "km",
        "mi": "mi",
        "mile": "mi",
        "miles": "mi",
        "kg": "kg",
        "kilogram": "kg",
        "kilograms": "kg",
        "ton": "ton",
        "tons": "ton",
        "tonne": "ton",
        "tonnes": "ton",
    }
    return unit_map.get(unit, "")


def _build_normalized(source, raw_record, row):
    errors = []

    quantity_text = _find_value(row, ["quantity", "qty", "amount", "value"])
    unit_text = _find_value(row, ["unit", "uom"])

    quantity = _parse_number(quantity_text)
    if quantity is None:
        errors.append("missing quantity")
        quantity = 0.0

    if quantity < 0:
        errors.append("negative value")

    normalized_unit = _normalize_unit(unit_text)
    if normalized_unit == "":
        errors.append("invalid unit")

    status = "suspicious" if errors else "pending"

    scope = _find_value(row, ["scope"]) or "unknown"
    category = _find_value(row, ["category"]) or "general"
    activity_type = _find_value(row, ["activity_type", "activity"]) or "unknown"

    record = NormalizedEmissionRecord.objects.create(
        company=source.company,
        raw_record=raw_record,
        scope=scope,
        category=category,
        activity_type=activity_type,
        quantity=quantity,
        original_unit=unit_text,
        normalized_unit=normalized_unit,
        co2e=quantity,
        status=status,
    )

    return record, errors


def _handle_upload(request, source_type):
    uploaded_file = request.FILES.get("file")
    if not uploaded_file:
        return Response({"error": "file required"}, status=400)

    company_id = request.data.get("company")
    if not company_id:
        return Response({"error": "company required"}, status=400)

    source = DataSource.objects.create(
        company_id=company_id,
        source_type=source_type,
        file_name=uploaded_file.name,
        status="uploaded",
    )

    try:
        rows = _read_csv_rows(uploaded_file)
    except Exception:
        source.status = "failed"
        source.save(update_fields=["status"])
        return Response({"error": "could not read file"}, status=400)

    for row in rows:
        raw_record = RawRecord.objects.create(
            source=source,
            raw_json=row,
        )
        _, errors = _build_normalized(source, raw_record, row)
        if errors:
            raw_record.ingestion_errors = "; ".join(errors)
            raw_record.save(update_fields=["ingestion_errors"])

    source.status = "normalized"
    source.save(update_fields=["status"])

    return Response({
        "data_source_id": source.id,
        "rows": len(rows),
    }, status=201)


@api_view(["POST"])
def upload_sap_csv(request):
    return _handle_upload(request, "sap")


@api_view(["POST"])
def upload_utility_csv(request):
    return _handle_upload(request, "utility")


@api_view(["POST"])
def upload_travel_csv(request):
    return _handle_upload(request, "travel")


def _update_review(record, action):
    if action == "approved":
        record.status = "approved"
        record.locked_for_audit = True
        record.save(update_fields=["status", "locked_for_audit"])
    elif action == "rejected":
        record.status = "rejected"
        record.locked_for_audit = True
        record.save(update_fields=["status", "locked_for_audit"])

    AuditLog.objects.create(
        record=record,
        action=action,
    )


@api_view(["POST"])
def approve_record(request, record_id):
    try:
        record = NormalizedEmissionRecord.objects.get(id=record_id)
    except NormalizedEmissionRecord.DoesNotExist:
        return Response({"error": "not found"}, status=404)

    _update_review(record, "approved")
    return Response({"status": "approved"})


@api_view(["POST"])
def reject_record(request, record_id):
    try:
        record = NormalizedEmissionRecord.objects.get(id=record_id)
    except NormalizedEmissionRecord.DoesNotExist:
        return Response({"error": "not found"}, status=404)

    _update_review(record, "rejected")
    return Response({"status": "rejected"})