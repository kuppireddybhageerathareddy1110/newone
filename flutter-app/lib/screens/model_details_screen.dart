import 'package:flutter/material.dart';

import '../models/model_info.dart';

class ModelDetailsScreen extends StatelessWidget {
  const ModelDetailsScreen({
    super.key,
    required this.modelInfo,
    required this.loading,
    required this.onRefresh,
  });

  final ModelInfo? modelInfo;
  final bool loading;
  final Future<void> Function() onRefresh;

  static const Map<String, Map<String, String>> glossary = {
    'age': {
      'full': 'Age',
      'meaning': 'Patient age in years.',
    },
    'oldpeak': {
      'full': 'ST Depression (Oldpeak)',
      'meaning': 'Exercise-induced ST depression relative to rest.',
    },
    'restingbp_final': {
      'full': 'Resting Blood Pressure',
      'meaning': 'Blood pressure measured at rest in mm Hg.',
    },
    'chol_final': {
      'full': 'Serum Cholesterol',
      'meaning': 'Cholesterol measured in mg/dl.',
    },
    'maxhr_final': {
      'full': 'Maximum Heart Rate',
      'meaning': 'Highest heart rate achieved during the test.',
    },
    'chol_age_ratio': {
      'full': 'Cholesterol-to-Age Ratio',
      'meaning': 'Engineered feature relating cholesterol burden to age.',
    },
    'bp_hr_ratio': {
      'full': 'Blood Pressure-to-Heart Rate Ratio',
      'meaning': 'Engineered feature relating resting BP to maximum heart rate.',
    },
    'stress_index': {
      'full': 'Stress Index',
      'meaning': 'Engineered feature combining oldpeak and heart rate.',
    },
    'cardiac_load': {
      'full': 'Cardiac Load',
      'meaning': 'Engineered feature combining age and blood pressure.',
    },
  };

  Map<String, String> _describeFeature(String feature) {
    final direct = glossary[feature];
    if (direct != null) return direct;

    if (feature.startsWith('cp_final_')) {
      return {
        'full': 'Chest Pain Type',
        'meaning': 'One-hot encoded chest pain category: ${feature.replaceFirst('cp_final_', '')}.',
      };
    }
    if (feature.startsWith('restecg_final_')) {
      return {
        'full': 'Resting ECG',
        'meaning': 'One-hot encoded ECG category: ${feature.replaceFirst('restecg_final_', '')}.',
      };
    }
    if (feature.startsWith('slope_final_')) {
      return {
        'full': 'ST Slope',
        'meaning': 'One-hot encoded ST slope category: ${feature.replaceFirst('slope_final_', '')}.',
      };
    }
    if (feature.startsWith('sex_')) {
      return {
        'full': 'Sex',
        'meaning': 'One-hot encoded sex indicator: ${feature.replaceFirst('sex_', '')}.',
      };
    }
    if (feature.startsWith('fbs_')) {
      return {
        'full': 'Fasting Blood Sugar',
        'meaning': 'Encoded fasting blood sugar indicator.',
      };
    }
    if (feature.startsWith('exang_')) {
      return {
        'full': 'Exercise-Induced Angina',
        'meaning': 'Encoded exercise angina indicator.',
      };
    }
    return {
      'full': feature,
      'meaning': 'Model input feature exposed by the backend.',
    };
  }

  @override
  Widget build(BuildContext context) {
    return RefreshIndicator(
      onRefresh: onRefresh,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Card(
            child: Padding(
              padding: const EdgeInsets.all(18),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Model Details', style: Theme.of(context).textTheme.headlineSmall),
                  const SizedBox(height: 8),
                  Text(
                    loading
                        ? 'Loading backend metadata...'
                        : modelInfo == null
                            ? 'Model details are unavailable until the backend responds.'
                            : '${modelInfo!.architecture} · v${modelInfo!.version}',
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          if (modelInfo != null) ...[
            Card(
              child: Padding(
                padding: const EdgeInsets.all(18),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('Architecture', style: TextStyle(fontWeight: FontWeight.w700)),
                    const SizedBox(height: 8),
                    Text('Base models: ${modelInfo!.baseModels.join(' + ')}'),
                    Text('Meta learner: ${modelInfo!.metaLearner}'),
                    Text('XAI engine: ${modelInfo!.xaiEngine}'),
                    Text('Feature count: ${modelInfo!.features}'),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(18),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('Top models', style: TextStyle(fontWeight: FontWeight.w700)),
                    const SizedBox(height: 8),
                    ...modelInfo!.leaderboard.take(5).map(
                      (row) => ListTile(
                        contentPadding: EdgeInsets.zero,
                        dense: true,
                        title: Text(row.model),
                        subtitle: Text(row.category),
                        trailing: Text('Acc ${row.accuracy.toStringAsFixed(3)}'),
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(18),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('Feature glossary', style: TextStyle(fontWeight: FontWeight.w700)),
                    const SizedBox(height: 8),
                    ...modelInfo!.featureList.map((feature) {
                      final meta = _describeFeature(feature);
                      return ListTile(
                        contentPadding: EdgeInsets.zero,
                        title: Text(meta['full']!),
                        subtitle: Text('${feature}\n${meta['meaning']!}'),
                        isThreeLine: true,
                      );
                    }),
                  ],
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }
}
