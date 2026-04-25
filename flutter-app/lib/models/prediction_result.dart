class PredictionAdvice {
  const PredictionAdvice({
    required this.title,
    required this.reason,
    required this.priority,
  });

  final String title;
  final String reason;
  final String priority;

  factory PredictionAdvice.fromJson(Map<String, dynamic> json) {
    return PredictionAdvice(
      title: json['title'] as String? ?? '',
      reason: json['reason'] as String? ?? '',
      priority: json['priority'] as String? ?? 'info',
    );
  }
}

class ConfidenceInterval {
  const ConfidenceInterval({
    required this.lower,
    required this.upper,
    required this.confidenceLevel,
    required this.modelDisagreement,
  });

  final double lower;
  final double upper;
  final double confidenceLevel;
  final double modelDisagreement;

  factory ConfidenceInterval.fromJson(Map<String, dynamic> json) {
    return ConfidenceInterval(
      lower: (json['lower'] as num?)?.toDouble() ?? 0,
      upper: (json['upper'] as num?)?.toDouble() ?? 0,
      confidenceLevel: (json['confidence_level'] as num?)?.toDouble() ?? 0.95,
      modelDisagreement: (json['model_disagreement'] as num?)?.toDouble() ?? 0,
    );
  }
}

class PredictionResult {
  const PredictionResult({
    required this.prediction,
    required this.probability,
    required this.xgbProbability,
    required this.dlProbability,
    required this.riskLevel,
    required this.modelUsed,
    required this.timestamp,
    required this.riskFactors,
    required this.protectiveFactors,
    required this.recommendations,
    required this.confidenceInterval,
  });

  final String prediction;
  final double probability;
  final double xgbProbability;
  final double dlProbability;
  final String riskLevel;
  final String modelUsed;
  final String timestamp;
  final List<String> riskFactors;
  final List<String> protectiveFactors;
  final List<PredictionAdvice> recommendations;
  final ConfidenceInterval confidenceInterval;

  factory PredictionResult.fromJson(Map<String, dynamic> json) {
    return PredictionResult(
      prediction: json['prediction'] as String? ?? '',
      probability: (json['probability'] as num?)?.toDouble() ?? 0,
      xgbProbability: (json['xgb_probability'] as num?)?.toDouble() ?? 0,
      dlProbability: (json['dl_probability'] as num?)?.toDouble() ?? 0,
      riskLevel: json['risk_level'] as String? ?? '',
      modelUsed: json['model_used'] as String? ?? '',
      timestamp: json['timestamp'] as String? ?? '',
      riskFactors: ((json['risk_factors'] as List?) ?? const []).cast<String>(),
      protectiveFactors: ((json['protective_factors'] as List?) ?? const []).cast<String>(),
      recommendations: ((json['recommendations'] as List?) ?? const [])
          .map((item) => PredictionAdvice.fromJson(item as Map<String, dynamic>))
          .toList(),
      confidenceInterval: ConfidenceInterval.fromJson(
        (json['confidence_interval'] as Map<String, dynamic>?) ?? const {},
      ),
    );
  }
}
