import 'package:flutter/material.dart';

import '../models/history_entry.dart';

class HistoryScreen extends StatelessWidget {
  const HistoryScreen({
    super.key,
    required this.history,
    required this.onSelect,
  });

  final List<HistoryEntry> history;
  final ValueChanged<HistoryEntry> onSelect;

  @override
  Widget build(BuildContext context) {
    if (history.isEmpty) {
      return ListView(
        padding: const EdgeInsets.all(16),
        children: const [
          Card(
            child: Padding(
              padding: EdgeInsets.all(18),
              child: Text('No saved assessments yet. Run an analysis first.'),
            ),
          ),
        ],
      );
    }

    return ListView.separated(
      padding: const EdgeInsets.all(16),
      itemCount: history.length,
      separatorBuilder: (_, __) => const SizedBox(height: 12),
      itemBuilder: (context, index) {
        final entry = history[index];
        return Card(
          child: ListTile(
            contentPadding: const EdgeInsets.all(16),
            title: Text('${entry.result.prediction} · ${(entry.result.probability * 100).toStringAsFixed(1)}%'),
            subtitle: Text(
              'Age ${entry.patient.age.toStringAsFixed(0)} · ${entry.patient.sex} · ${entry.result.riskLevel} risk',
            ),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => onSelect(entry),
          ),
        );
      },
    );
  }
}
