import 'patient_input.dart';
import 'prediction_result.dart';

class HistoryEntry {
  const HistoryEntry({
    required this.patient,
    required this.result,
  });

  final PatientInput patient;
  final PredictionResult result;
}
