import 'package:flutter/material.dart';

import '../models/patient_input.dart';
import '../models/prediction_result.dart';
import '../services/cardio_api.dart';

class AssessmentScreen extends StatefulWidget {
  const AssessmentScreen({
    super.key,
    required this.api,
    required this.initialPatient,
    required this.onSaved,
  });

  final CardioApi api;
  final PatientInput initialPatient;
  final void Function(PatientInput patient, PredictionResult result) onSaved;

  @override
  State<AssessmentScreen> createState() => _AssessmentScreenState();
}

class _AssessmentScreenState extends State<AssessmentScreen> {
  late PatientInput _patient;
  PredictionResult? _result;
  bool _submitting = false;

  @override
  void initState() {
    super.initState();
    _patient = widget.initialPatient;
  }

  @override
  void didUpdateWidget(covariant AssessmentScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.initialPatient != widget.initialPatient) {
      setState(() {
        _patient = widget.initialPatient;
      });
    }
  }

  Future<void> _submit() async {
    setState(() => _submitting = true);
    try {
      final result = await widget.api.predict(_patient);
      if (!mounted) return;
      setState(() => _result = result);
      widget.onSaved(_patient, result);
    } catch (error) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(error.toString())),
      );
    } finally {
      if (mounted) {
        setState(() => _submitting = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _HeaderCard(
            onLoadSample: () => setState(() {
              _patient = sampleHighRiskPatient;
            }),
          ),
          const SizedBox(height: 16),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                children: [
                  _NumberField(
                    label: 'Age',
                    value: _patient.age,
                    onChanged: (value) => setState(() {
                      _patient = _patient.copyWith(age: value);
                    }),
                  ),
                  const SizedBox(height: 12),
                  _DropdownField(
                    label: 'Sex',
                    value: _patient.sex,
                    items: const ['Male', 'Female'],
                    onChanged: (value) => setState(() {
                      _patient = _patient.copyWith(sex: value);
                    }),
                  ),
                  const SizedBox(height: 12),
                  _DropdownField(
                    label: 'Chest Pain Type',
                    value: _patient.chestPain,
                    items: const [
                      'Typical Angina',
                      'Atypical Angina',
                      'Non-anginal Pain',
                      'Asymptomatic',
                    ],
                    onChanged: (value) => setState(() {
                      _patient = _patient.copyWith(chestPain: value);
                    }),
                  ),
                  const SizedBox(height: 12),
                  _NumberField(
                    label: 'Resting Blood Pressure',
                    value: _patient.restingBpFinal,
                    onChanged: (value) => setState(() {
                      _patient = _patient.copyWith(restingBpFinal: value);
                    }),
                  ),
                  const SizedBox(height: 12),
                  _NumberField(
                    label: 'Cholesterol',
                    value: _patient.cholFinal,
                    onChanged: (value) => setState(() {
                      _patient = _patient.copyWith(cholFinal: value);
                    }),
                  ),
                  const SizedBox(height: 12),
                  _NumberField(
                    label: 'Max Heart Rate',
                    value: _patient.maxHrFinal,
                    onChanged: (value) => setState(() {
                      _patient = _patient.copyWith(maxHrFinal: value);
                    }),
                  ),
                  const SizedBox(height: 12),
                  _NumberField(
                    label: 'ST Depression (Oldpeak)',
                    value: _patient.oldpeak,
                    onChanged: (value) => setState(() {
                      _patient = _patient.copyWith(oldpeak: value);
                    }),
                  ),
                  const SizedBox(height: 12),
                  _DropdownField(
                    label: 'Fasting Blood Sugar > 120 mg/dl',
                    value: _patient.fastingBs,
                    items: const ['No', 'Yes'],
                    onChanged: (value) => setState(() {
                      _patient = _patient.copyWith(fastingBs: value);
                    }),
                  ),
                  const SizedBox(height: 12),
                  _DropdownField(
                    label: 'Resting ECG',
                    value: _patient.restingEcg,
                    items: const ['Normal', 'ST-T Abnormality', 'LV Hypertrophy'],
                    onChanged: (value) => setState(() {
                      _patient = _patient.copyWith(restingEcg: value);
                    }),
                  ),
                  const SizedBox(height: 12),
                  _DropdownField(
                    label: 'Exercise-Induced Angina',
                    value: _patient.exerciseAngina,
                    items: const ['No', 'Yes'],
                    onChanged: (value) => setState(() {
                      _patient = _patient.copyWith(exerciseAngina: value);
                    }),
                  ),
                  const SizedBox(height: 12),
                  _DropdownField(
                    label: 'ST Slope',
                    value: _patient.stSlope,
                    items: const ['Upsloping', 'Flat', 'Downsloping'],
                    onChanged: (value) => setState(() {
                      _patient = _patient.copyWith(stSlope: value);
                    }),
                  ),
                  const SizedBox(height: 16),
                  FilledButton.icon(
                    onPressed: _submitting ? null : _submit,
                    icon: _submitting
                        ? const SizedBox(
                            width: 16,
                            height: 16,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : const Icon(Icons.analytics_outlined),
                    label: Text(_submitting ? 'Analysing...' : 'Run Hybrid Analysis'),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          if (_result != null) _ResultCard(result: _result!),
        ],
      ),
    );
  }
}

class _HeaderCard extends StatelessWidget {
  const _HeaderCard({required this.onLoadSample});

  final VoidCallback onLoadSample;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Patient Risk Assessment',
              style: Theme.of(context).textTheme.headlineSmall,
            ),
            const SizedBox(height: 8),
            const Text(
              'Hybrid model using XGBoost, deep learning, and a meta logistic regression layer.',
            ),
            const SizedBox(height: 12),
            OutlinedButton.icon(
              onPressed: onLoadSample,
              icon: const Icon(Icons.person_search_outlined),
              label: const Text('Load High-Risk Sample'),
            ),
          ],
        ),
      ),
    );
  }
}

class _ResultCard extends StatelessWidget {
  const _ResultCard({required this.result});

  final PredictionResult result;

  Color _riskColor() {
    switch (result.riskLevel.toUpperCase()) {
      case 'HIGH':
        return const Color(0xFFD94A4A);
      case 'MEDIUM':
        return const Color(0xFFD68910);
      default:
        return const Color(0xFF15966D);
    }
  }

  @override
  Widget build(BuildContext context) {
    final probability = (result.probability * 100).toStringAsFixed(1);
    final ciLower = (result.confidenceInterval.lower * 100).toStringAsFixed(1);
    final ciUpper = (result.confidenceInterval.upper * 100).toStringAsFixed(1);

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                CircleAvatar(
                  backgroundColor: _riskColor().withOpacity(0.12),
                  foregroundColor: _riskColor(),
                  child: const Icon(Icons.favorite),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(result.prediction, style: Theme.of(context).textTheme.titleLarge),
                      Text('${result.riskLevel} risk · $probability% probability'),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                _InfoChip(label: 'XGB', value: '${(result.xgbProbability * 100).toStringAsFixed(1)}%'),
                _InfoChip(label: 'DL', value: '${(result.dlProbability * 100).toStringAsFixed(1)}%'),
                _InfoChip(label: '95% Range', value: '$ciLower% - $ciUpper%'),
              ],
            ),
            const SizedBox(height: 16),
            if (result.riskFactors.isNotEmpty) ...[
              const Text('Risk factors', style: TextStyle(fontWeight: FontWeight.w700)),
              const SizedBox(height: 8),
              ...result.riskFactors.map((item) => ListTile(
                    contentPadding: EdgeInsets.zero,
                    dense: true,
                    leading: const Icon(Icons.warning_amber_rounded),
                    title: Text(item),
                  )),
            ],
            if (result.recommendations.isNotEmpty) ...[
              const SizedBox(height: 12),
              const Text('Recommendations', style: TextStyle(fontWeight: FontWeight.w700)),
              const SizedBox(height: 8),
              ...result.recommendations.map((item) => ListTile(
                    contentPadding: EdgeInsets.zero,
                    dense: true,
                    leading: const Icon(Icons.medical_information_outlined),
                    title: Text(item.title),
                    subtitle: Text(item.reason),
                  )),
            ],
          ],
        ),
      ),
    );
  }
}

class _InfoChip extends StatelessWidget {
  const _InfoChip({
    required this.label,
    required this.value,
  });

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: const Color(0xFFF4F7FB),
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: const Color(0xFFDCE4ED)),
      ),
      child: Text('$label: $value'),
    );
  }
}

class _DropdownField extends StatelessWidget {
  const _DropdownField({
    required this.label,
    required this.value,
    required this.items,
    required this.onChanged,
  });

  final String label;
  final String value;
  final List<String> items;
  final ValueChanged<String> onChanged;

  @override
  Widget build(BuildContext context) {
    return DropdownButtonFormField<String>(
      value: value,
      decoration: InputDecoration(labelText: label),
      items: items
          .map((item) => DropdownMenuItem<String>(
                value: item,
                child: Text(item),
              ))
          .toList(),
      onChanged: (value) {
        if (value != null) {
          onChanged(value);
        }
      },
    );
  }
}

class _NumberField extends StatelessWidget {
  const _NumberField({
    required this.label,
    required this.value,
    required this.onChanged,
  });

  final String label;
  final double value;
  final ValueChanged<double> onChanged;

  @override
  Widget build(BuildContext context) {
    return TextFormField(
      key: ValueKey<String>('$label-$value'),
      initialValue: value.toString(),
      keyboardType: const TextInputType.numberWithOptions(decimal: true),
      decoration: InputDecoration(labelText: label),
      onChanged: (input) => onChanged(double.tryParse(input) ?? value),
    );
  }
}
