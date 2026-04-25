import 'package:flutter/material.dart';

import '../models/history_entry.dart';
import '../models/model_info.dart';
import '../models/patient_input.dart';
import '../models/prediction_result.dart';
import '../services/cardio_api.dart';
import 'assessment_screen.dart';
import 'batch_screen.dart';
import 'history_screen.dart';
import 'insights_screen.dart';
import 'model_details_screen.dart';

class HomeShell extends StatefulWidget {
  const HomeShell({super.key});

  @override
  State<HomeShell> createState() => _HomeShellState();
}

class _HomeShellState extends State<HomeShell> {
  final CardioApi _api = CardioApi();
  int _index = 0;
  PredictionResult? _latestResult;
  PatientInput _latestPatient = defaultPatientInput;
  final List<HistoryEntry> _history = <HistoryEntry>[];
  ModelInfo? _modelInfo;
  bool _loadingModelInfo = false;

  @override
  void initState() {
    super.initState();
    _loadModelInfo();
  }

  Future<void> _loadModelInfo() async {
    setState(() => _loadingModelInfo = true);
    try {
      final info = await _api.getModelInfo();
      if (!mounted) return;
      setState(() => _modelInfo = info);
    } catch (_) {
      if (!mounted) return;
    } finally {
      if (mounted) {
        setState(() => _loadingModelInfo = false);
      }
    }
  }

  void _saveResult(PatientInput patient, PredictionResult result) {
    setState(() {
      _latestPatient = patient;
      _latestResult = result;
      _history.insert(0, HistoryEntry(patient: patient, result: result));
      if (_history.length > 10) {
        _history.removeLast();
      }
      _index = 2;
    });
  }

  @override
  Widget build(BuildContext context) {
    final pages = <Widget>[
      AssessmentScreen(
        api: _api,
        initialPatient: _latestPatient,
        onSaved: _saveResult,
      ),
      BatchScreen(api: _api),
      InsightsScreen(
        patient: _latestPatient,
        result: _latestResult,
      ),
      HistoryScreen(
        history: _history,
        onSelect: (entry) {
          setState(() {
            _latestPatient = entry.patient;
            _latestResult = entry.result;
            _index = 0;
          });
        },
      ),
      ModelDetailsScreen(
        modelInfo: _modelInfo,
        loading: _loadingModelInfo,
        onRefresh: _loadModelInfo,
      ),
    ];

    return Scaffold(
      appBar: AppBar(
        title: const Text('CardioAI Hybrid'),
      ),
      body: SafeArea(
        child: IndexedStack(
          index: _index,
          children: pages,
        ),
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _index,
        onDestinationSelected: (value) => setState(() => _index = value),
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.favorite_outline),
            selectedIcon: Icon(Icons.favorite),
            label: 'Assess',
          ),
          NavigationDestination(
            icon: Icon(Icons.table_chart_outlined),
            selectedIcon: Icon(Icons.table_chart),
            label: 'Batch',
          ),
          NavigationDestination(
            icon: Icon(Icons.lightbulb_outline),
            selectedIcon: Icon(Icons.lightbulb),
            label: 'Insights',
          ),
          NavigationDestination(
            icon: Icon(Icons.history),
            selectedIcon: Icon(Icons.history_toggle_off),
            label: 'History',
          ),
          NavigationDestination(
            icon: Icon(Icons.info_outline),
            selectedIcon: Icon(Icons.info),
            label: 'Model',
          ),
        ],
      ),
    );
  }
}
