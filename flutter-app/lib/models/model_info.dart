class ModelMetricRow {
  const ModelMetricRow({
    required this.model,
    required this.category,
    required this.accuracy,
    required this.rocAuc,
  });

  final String model;
  final String category;
  final double accuracy;
  final double rocAuc;

  factory ModelMetricRow.fromJson(Map<String, dynamic> json) {
    return ModelMetricRow(
      model: json['Model'] as String? ?? '',
      category: json['Category'] as String? ?? '',
      accuracy: (json['Accuracy'] as num?)?.toDouble() ?? 0,
      rocAuc: (json['ROC-AUC'] as num?)?.toDouble() ?? 0,
    );
  }
}

class ModelInfo {
  const ModelInfo({
    required this.architecture,
    required this.version,
    required this.baseModels,
    required this.metaLearner,
    required this.xaiEngine,
    required this.features,
    required this.featureList,
    required this.leaderboard,
  });

  final String architecture;
  final String version;
  final List<String> baseModels;
  final String metaLearner;
  final String xaiEngine;
  final int features;
  final List<String> featureList;
  final List<ModelMetricRow> leaderboard;

  factory ModelInfo.fromJson(Map<String, dynamic> json) {
    return ModelInfo(
      architecture: json['architecture'] as String? ?? '',
      version: json['version'] as String? ?? '',
      baseModels: ((json['base_models'] as List?) ?? const []).cast<String>(),
      metaLearner: json['meta_learner'] as String? ?? '',
      xaiEngine: json['xai_engine'] as String? ?? '',
      features: json['features'] as int? ?? 0,
      featureList: ((json['feature_list'] as List?) ?? const []).cast<String>(),
      leaderboard: ((json['leaderboard'] as List?) ?? const [])
          .map((item) => ModelMetricRow.fromJson(item as Map<String, dynamic>))
          .toList(),
    );
  }
}
