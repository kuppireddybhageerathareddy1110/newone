import 'prediction_result.dart';

class BatchPredictionResponse {
  const BatchPredictionResponse({
    required this.count,
    required this.diseaseCount,
    required this.noDiseaseCount,
    required this.averageProbability,
    required this.generatedAt,
    required this.results,
  });

  final int count;
  final int diseaseCount;
  final int noDiseaseCount;
  final double averageProbability;
  final String generatedAt;
  final List<PredictionResult> results;

  factory BatchPredictionResponse.fromJson(Map<String, dynamic> json) {
    return BatchPredictionResponse(
      count: json['count'] as int? ?? 0,
      diseaseCount: json['disease_count'] as int? ?? 0,
      noDiseaseCount: json['no_disease_count'] as int? ?? 0,
      averageProbability: (json['average_probability'] as num?)?.toDouble() ?? 0,
      generatedAt: json['generated_at'] as String? ?? '',
      results: ((json['results'] as List?) ?? const [])
          .map((item) => PredictionResult.fromJson(item as Map<String, dynamic>))
          .toList(),
    );
  }
}
