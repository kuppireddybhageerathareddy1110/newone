import 'dart:convert';

import 'package:http/http.dart' as http;

import '../models/batch_prediction.dart';
import '../models/model_info.dart';
import '../models/patient_input.dart';
import '../models/prediction_result.dart';

class CardioApi {
  CardioApi({http.Client? client}) : _client = client ?? http.Client();

  static const String baseUrl = 'http://10.0.2.2:8001';

  final http.Client _client;

  Future<PredictionResult> predict(PatientInput input) async {
    final response = await _client.post(
      Uri.parse('$baseUrl/predict'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(input.toJson()),
    );

    if (response.statusCode >= 400) {
      throw Exception(_extractError(response.body, response.statusCode));
    }

    return PredictionResult.fromJson(
      jsonDecode(response.body) as Map<String, dynamic>,
    );
  }

  Future<ModelInfo> getModelInfo() async {
    final response = await _client.get(Uri.parse('$baseUrl/model/info'));

    if (response.statusCode >= 400) {
      throw Exception(_extractError(response.body, response.statusCode));
    }

    return ModelInfo.fromJson(
      jsonDecode(response.body) as Map<String, dynamic>,
    );
  }

  Future<BatchPredictionResponse> predictBatch(List<PatientInput> patients) async {
    final response = await _client.post(
      Uri.parse('$baseUrl/predict/batch'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'patients': patients.map((patient) => patient.toJson()).toList(),
      }),
    );

    if (response.statusCode >= 400) {
      throw Exception(_extractError(response.body, response.statusCode));
    }

    return BatchPredictionResponse.fromJson(
      jsonDecode(response.body) as Map<String, dynamic>,
    );
  }

  String _extractError(String body, int statusCode) {
    try {
      final decoded = jsonDecode(body) as Map<String, dynamic>;
      return decoded['error'] as String? ??
          decoded['detail'] as String? ??
          'Request failed with status $statusCode';
    } catch (_) {
      return 'Request failed with status $statusCode';
    }
  }
}
