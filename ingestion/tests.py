from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.test import APIClient

from .models import AuditLog, Company, NormalizedEmissionRecord, RawRecord


class IngestionApiTests(TestCase):
	def setUp(self):
		self.client = APIClient()
		self.company = Company.objects.create(name="Test Co")

	def _upload_csv(self, content, source_type="sap"):
		upload = SimpleUploadedFile(
			"sample.csv",
			content.encode("utf-8"),
			content_type="text/csv",
		)
		return self.client.post(
			f"/api/upload/{source_type}/",
			{"file": upload, "company": self.company.id},
			format="multipart",
		)

	def test_upload_creates_raw_and_normalized_records(self):
		content = (
			"quantity,unit,scope,category,activity_type\n"
			"10,kwh,scope_2,energy,consumption\n"
			"-5,kwh,scope_2,energy,consumption\n"
			",kg,scope_3,logistics,shipping\n"
		)
		response = self._upload_csv(content)

		self.assertEqual(response.status_code, 201)
		self.assertEqual(response.data["rows"], 3)
		self.assertEqual(response.data["suspicious_rows"], 2)
		self.assertEqual(RawRecord.objects.count(), 3)
		self.assertEqual(NormalizedEmissionRecord.objects.count(), 3)

		pending_count = NormalizedEmissionRecord.objects.filter(status="pending").count()
		suspicious_count = NormalizedEmissionRecord.objects.filter(status="suspicious").count()

		self.assertEqual(pending_count, 1)
		self.assertEqual(suspicious_count, 2)

	def test_approve_and_reject_create_audit_logs(self):
		content = (
			"quantity,unit,scope,category,activity_type\n"
			"10,kwh,scope_2,energy,consumption\n"
			"12,kwh,scope_2,energy,consumption\n"
		)
		self._upload_csv(content)

		record_ids = list(
			NormalizedEmissionRecord.objects.values_list("id", flat=True)
		)

		approve_response = self.client.post(
			f"/api/records/{record_ids[0]}/approve/"
		)
		reject_response = self.client.post(
			f"/api/records/{record_ids[1]}/reject/"
		)

		self.assertEqual(approve_response.status_code, 200)
		self.assertEqual(reject_response.status_code, 200)

		approved_record = NormalizedEmissionRecord.objects.get(id=record_ids[0])
		rejected_record = NormalizedEmissionRecord.objects.get(id=record_ids[1])

		self.assertEqual(approved_record.status, "approved")
		self.assertEqual(rejected_record.status, "rejected")
		self.assertTrue(approved_record.locked_for_audit)
		self.assertTrue(rejected_record.locked_for_audit)

		audit_actions = list(AuditLog.objects.values_list("action", flat=True))
		self.assertCountEqual(audit_actions, ["approved", "rejected"])

	def test_upload_requires_file(self):
		response = self.client.post(
			"/api/upload/sap/",
			{"company": self.company.id},
			format="multipart",
		)

		self.assertEqual(response.status_code, 400)
		self.assertIn("error", response.data)
