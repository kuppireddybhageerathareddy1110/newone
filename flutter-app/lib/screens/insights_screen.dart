import 'package:flutter/material.dart';

import '../models/patient_input.dart';
import '../models/prediction_result.dart';

class InsightsScreen extends StatelessWidget {
  const InsightsScreen({
    super.key,
    required this.patient,
    required this.result,
  });

  final PatientInput patient;
  final PredictionResult? result;

  @override
  Widget build(BuildContext context) {
    final staticInsights = <Map<String, String>>[
      {
        'title': 'Physical activity',
        'body': 'Aim for regular aerobic activity, adjusted to symptoms and clinician advice.',
      },
      {
        'title': 'Diet quality',
        'body': 'Prioritize fiber, unsaturated fats, and lower processed-food intake.',
      },
      {
        'title': 'Blood pressure follow-up',
        'body': 'Track sustained elevations and review them with a clinician.',
      },
      {
        'title': 'Medication adherence',
        'body': 'If prescribed, consistency matters more than occasional catch-up dosing.',
      },
    ];

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Card(
          child: Padding(
            padding: const EdgeInsets.all(18),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Clinical Insights', style: Theme.of(context).textTheme.headlineSmall),
                const SizedBox(height: 8),
                Text(
                  result == null
                      ? 'Run an assessment to unlock patient-specific recommendations.'
                      : 'Latest case: ${result!.riskLevel} risk for a ${patient.age.toStringAsFixed(0)} year old ${patient.sex.toLowerCase()} patient.',
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 16),
        if (result != null) ...[
          const Text('Patient-specific guidance', style: TextStyle(fontWeight: FontWeight.w700)),
          const SizedBox(height: 8),
          ...result!.recommendations.map((item) => Card(
                child: ListTile(
                  leading: const Icon(Icons.arrow_forward_ios_rounded, size: 18),
                  title: Text(item.title),
                  subtitle: Text(item.reason),
                ),
              )),
          const SizedBox(height: 16),
        ],
        const Text('General prevention themes', style: TextStyle(fontWeight: FontWeight.w700)),
        const SizedBox(height: 8),
        ...staticInsights.map((item) => Card(
              child: ListTile(
                leading: const Icon(Icons.favorite_border),
                title: Text(item['title']!),
                subtitle: Text(item['body']!),
              ),
            )),
      ],
    );
  }
}
