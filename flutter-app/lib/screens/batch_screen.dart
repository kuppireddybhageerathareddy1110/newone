import 'package:flutter/material.dart';

import '../models/batch_prediction.dart';
import '../models/patient_input.dart';
import '../services/cardio_api.dart';

class BatchScreen extends StatefulWidget {
  const BatchScreen({
    super.key,
    required this.api,
  });

  final CardioApi api;

  @override
  State<BatchScreen> createState() => _BatchScreenState();
}

class _BatchScreenState extends State<BatchScreen> {
  static const String _template = '''
age,sex,oldpeak,chest_pain,restingbp_final,chol_final,maxhr_final,fasting_bs,resting_ecg,exercise_angina,st_slope
65,Male,2.5,Asymptomatic,160,300,130,Yes,ST-T Abnormality,Yes,Flat
54,Female,1.2,Non-anginal Pain,128,210,158,No,Normal,No,Upsloping
''';

  late final TextEditingController _controller;
  BatchPredictionResponse? _result;
  bool _submitting = false;

  @override
  void initState() {
    super.initState();
    _controller = TextEditingController(text: _template.trim());
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  List<PatientInput> _parseCsv(String csv) {
    final lines = csv
        .split(RegExp(r'\r?\n'))
        .map((line) => line.trim())
        .where((line) => line.isNotEmpty)
        .toList();

    if (lines.length < 2) {
      throw Exception('CSV needs a header row and at least one patient row.');
    }

    final headers = lines.first.split(',').map((item) => item.trim()).toList();

    return lines.skip(1).map((line) {
      final cells = line.split(',').map((item) => item.trim()).toList();
      final map = <String, String>{};
      for (var index = 0; index < headers.length; index++) {
        map[headers[index]] = index < cells.length ? cells[index] : '';
      }

      return PatientInput(
        age: double.parse(map['age']!),
        sex: map['sex']!,
        oldpeak: double.parse(map['oldpeak']!),
        chestPain: map['chest_pain']!,
        restingBpFinal: double.parse(map['restingbp_final']!),
        cholFinal: double.parse(map['chol_final']!),
        maxHrFinal: double.parse(map['maxhr_final']!),
        fastingBs: map['fasting_bs']!,
        restingEcg: map['resting_ecg']!,
        exerciseAngina: map['exercise_angina']!,
        stSlope: map['st_slope']!,
      );
    }).toList();
  }

  Future<void> _runBatch() async {
    setState(() => _submitting = true);
    try {
      final patients = _parseCsv(_controller.text);
      final result = await widget.api.predictBatch(patients);
      if (!mounted) return;
      setState(() => _result = result);
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
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Card(
          child: Padding(
            padding: const EdgeInsets.all(18),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Batch Assessment', style: Theme.of(context).textTheme.headlineSmall),
                const SizedBox(height: 8),
                const Text('Paste CSV input to score multiple patients through the backend batch endpoint.'),
                const SizedBox(height: 16),
                TextField(
                  controller: _controller,
                  minLines: 8,
                  maxLines: 14,
                  decoration: const InputDecoration(
                    labelText: 'CSV Input',
                    alignLabelWithHint: true,
                  ),
                ),
                const SizedBox(height: 16),
                Wrap(
                  spacing: 12,
                  runSpacing: 12,
                  children: [
                    FilledButton.icon(
                      onPressed: _submitting ? null : _runBatch,
                      icon: _submitting
                          ? const SizedBox(
                              width: 16,
                              height: 16,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            )
                          : const Icon(Icons.table_chart_outlined),
                      label: Text(_submitting ? 'Running...' : 'Run Batch'),
                    ),
                    OutlinedButton.icon(
                      onPressed: () => _controller.text = _template.trim(),
                      icon: const Icon(Icons.restart_alt),
                      label: const Text('Reset Template'),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 16),
        if (_result != null)
          Card(
            child: Padding(
              padding: const EdgeInsets.all(18),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Batch Result Summary', style: Theme.of(context).textTheme.titleLarge),
                  const SizedBox(height: 12),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: [
                      _SummaryChip(label: 'Cases', value: '${_result!.count}'),
                      _SummaryChip(label: 'Disease', value: '${_result!.diseaseCount}'),
                      _SummaryChip(label: 'No Disease', value: '${_result!.noDiseaseCount}'),
                      _SummaryChip(
                        label: 'Avg Probability',
                        value: '${(_result!.averageProbability * 100).toStringAsFixed(1)}%',
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  ..._result!.results.asMap().entries.map((entry) {
                    final index = entry.key;
                    final item = entry.value;
                    return ListTile(
                      contentPadding: EdgeInsets.zero,
                      dense: true,
                      leading: CircleAvatar(child: Text('${index + 1}')),
                      title: Text('${item.prediction} · ${item.riskLevel} risk'),
                      subtitle: Text('Probability ${(item.probability * 100).toStringAsFixed(1)}%'),
                    );
                  }),
                ],
              ),
            ),
          ),
      ],
    );
  }
}

class _SummaryChip extends StatelessWidget {
  const _SummaryChip({
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
